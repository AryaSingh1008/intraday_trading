"""
Lambda handler: POST /api/chat
Invokes the Bedrock TradingAdvisorAgent and returns its response.

Request body:  { "message": "Should I buy INFY today?", "session_id": "optional-uuid" }
Response body: { "response": "Based on analysis...", "session_id": "uuid" }
"""
import json
import os
import boto3

_client = None

def _get_client():
    global _client
    if _client is None:
        _client = boto3.client("bedrock-agent-runtime", region_name=os.environ.get("AWS_REGION", "us-east-1"))
    return _client


AGENT_ID       = os.environ.get("BEDROCK_AGENT_ID", "")
AGENT_ALIAS_ID = os.environ.get("BEDROCK_AGENT_ALIAS_ID", "TSTALIASID")


def handler(event, context):
    # Parse request
    body       = json.loads(event.get("body") or "{}")
    message    = (body.get("message") or "").strip()
    session_id = body.get("session_id") or context.aws_request_id

    if not message:
        return _json({"error": "message is required"}, 400)

    if not AGENT_ID:
        return _json({
            "error": "Bedrock Agent not configured yet. Set BEDROCK_AGENT_ID environment variable.",
            "hint": "Run: terraform output bedrock_agent_id"
        }, 503)

    try:
        client = _get_client()
        response = client.invoke_agent(
            agentId      = AGENT_ID,
            agentAliasId = AGENT_ALIAS_ID,
            sessionId    = session_id,
            inputText    = message,
        )

        # Collect streamed response chunks
        completion = ""
        for event_chunk in response.get("completion", []):
            chunk = event_chunk.get("chunk", {})
            if "bytes" in chunk:
                completion += chunk["bytes"].decode("utf-8")

        return _json({
            "response":   completion or "I wasn't able to generate a response. Please try again.",
            "session_id": session_id,
        })

    except client.exceptions.AccessDeniedException:
        return _json({
            "error": "Bedrock access denied. Enable Claude Haiku model access in AWS Console → Bedrock → Model access.",
        }, 403)
    except Exception as e:
        print(f"[bedrock_chat] Error: {type(e).__name__}: {e}")
        return _json({"error": f"Agent error: {str(e)}"}, 500)


def _json(data: dict, status: int = 200):
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(data),
    }
