"""
AI Signal Validator — Claude Haiku 3.5 via Bedrock InvokeModel
──────────────────────────────────────────────────────────────
Called when a user opens the stock detail modal.
Receives ALL pre-computed indicators and returns a grounded AI thesis.
Never invents numbers — only reasons about data it's given.
"""
import json
import logging
import boto3

logger = logging.getLogger(__name__)

_client = None
MODEL_ID = "us.anthropic.claude-3-5-haiku-20241022-v1:0"


def _get_client():
    global _client
    if _client is None:
        _client = boto3.client("bedrock-runtime", region_name="us-east-1")
    return _client


def validate_signal(stock_data: dict) -> dict:
    """
    Send pre-computed indicators to Claude Haiku and get back a
    structured AI analysis. Returns dict with ai_thesis, ai_confidence, etc.
    """
    try:
        prompt = _build_prompt(stock_data)
        client = _get_client()

        response = client.invoke_model(
            modelId=MODEL_ID,
            contentType="application/json",
            accept="application/json",
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 512,
                "temperature": 0.2,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
            }),
        )

        body = json.loads(response["body"].read())
        text = body.get("content", [{}])[0].get("text", "")

        return _parse_response(text)

    except Exception as e:
        logger.error("AI validation failed: %s", e)
        return {
            "ai_thesis": None,
            "ai_confidence": None,
            "ai_signal_agrees": None,
            "ai_risk_flags": [],
            "ai_contradictions": [],
            "ai_available": False,
        }


def _build_prompt(s: dict) -> str:
    """Build the grounded prompt with all pre-computed indicators."""
    symbol = s.get("symbol", "?")
    name = s.get("name", symbol)
    signal = s.get("signal", "HOLD")
    score = s.get("score", 50)
    tech_score = s.get("tech_score", 50)
    sent_score = s.get("sent_score", 0)
    tech_w = s.get("tech_weight", 0.75)
    sent_w = s.get("sent_weight", 0.25)

    price = s.get("current_price", 0)
    change_pct = s.get("change_pct", 0)
    volume = s.get("volume", 0)
    avg_volume = s.get("avg_volume", 0)
    high_52w = s.get("high_52w")
    low_52w = s.get("low_52w")
    vwap = s.get("vwap")
    support = s.get("support_level")
    resistance = s.get("resistance_level")
    rs_ratio = s.get("rs_ratio")
    target_price = s.get("target_price")
    stop_loss = s.get("stop_loss")
    target_buy = s.get("target_buy_price")
    risk = s.get("risk", "MEDIUM")
    reasons = s.get("reasons", [])
    sector = s.get("sector", "Others")

    reasons_str = "\n".join(f"  - {r}" for r in reasons) if reasons else "  (none)"

    # Volume ratio
    vol_ratio = round(volume / avg_volume, 2) if avg_volume and volume else None

    # Distance from 52W high/low
    dist_high = round((price / high_52w - 1) * 100, 1) if high_52w and price else None
    dist_low = round((price / low_52w - 1) * 100, 1) if low_52w and price else None

    return f"""You are a stock signal validator for Indian equities. You receive PRE-COMPUTED indicators and must reason ONLY about the data given. Never invent prices, numbers, or data points.

STOCK: {name} ({symbol}) | Sector: {sector}
PRICE: Rs {price} | Change: {change_pct:+.2f}%
52W HIGH: Rs {high_52w or 'N/A'} ({dist_high or 'N/A'}% away) | 52W LOW: Rs {low_52w or 'N/A'} ({dist_low or 'N/A'}% above)
VOLUME: {volume:,} | Avg Volume: {avg_volume:,} | Vol Ratio: {vol_ratio or 'N/A'}x
VWAP: Rs {vwap or 'N/A'}
SUPPORT (S1): Rs {support or 'N/A'} | RESISTANCE (R1): Rs {resistance or 'N/A'}
RS vs NIFTY 50: {rs_ratio or 'N/A'}

TECHNICAL SCORE: {tech_score}/100 (weight: {tech_w:.0%})
SENTIMENT SCORE: {sent_score}/50 (weight: {sent_w:.0%})
COMBINED SCORE: {score}/100
RULE-BASED SIGNAL: {signal}
RISK LEVEL: {risk}

TARGET PRICE: Rs {target_price or 'N/A'} | STOP LOSS: Rs {stop_loss or 'N/A'} | RE-ENTRY: Rs {target_buy or 'N/A'}

INDICATOR REASONS:
{reasons_str}

TASK: Analyse whether the {signal} signal makes sense given these indicators.
Return ONLY a JSON object with these fields:
- "agrees": boolean - does the data support the {signal} signal?
- "confidence": "HIGH" or "MEDIUM" or "LOW" - how strongly do indicators agree with each other?
- "thesis": string - 2-3 sentence plain-English trading thesis. Mention specific numbers from above. No jargon.
- "risk_flags": array of strings - specific risks (max 3). Empty array if none.
- "contradictions": array of strings - conflicting indicators (max 2). Empty array if none.

Return ONLY valid JSON, no markdown fences, no extra text."""


def _parse_response(text: str) -> dict:
    """Parse Claude's JSON response with fallback."""
    # Strip markdown fences if present
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1]
    if text.endswith("```"):
        text = text.rsplit("```", 1)[0]
    text = text.strip()

    try:
        data = json.loads(text)
        return {
            "ai_thesis": data.get("thesis", ""),
            "ai_confidence": data.get("confidence", "MEDIUM"),
            "ai_signal_agrees": data.get("agrees", True),
            "ai_risk_flags": data.get("risk_flags", [])[:3],
            "ai_contradictions": data.get("contradictions", [])[:2],
            "ai_available": True,
        }
    except (json.JSONDecodeError, KeyError) as e:
        logger.warning("Failed to parse AI response: %s — raw: %s", e, text[:200])
        # Fallback: use raw text as thesis
        return {
            "ai_thesis": text[:300] if text else None,
            "ai_confidence": None,
            "ai_signal_agrees": None,
            "ai_risk_flags": [],
            "ai_contradictions": [],
            "ai_available": bool(text),
        }
