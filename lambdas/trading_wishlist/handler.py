"""
Lambda handler: GET|POST|DELETE /api/wishlist and GET /api/wishlist/check/{symbol}
Replaces backend/utils/wishlist_store.py (file-based) with DynamoDB.
"""
import json
import os
import time
import boto3

USER_ID = "default"   # Single-user mode; extend to cognito sub for multi-user

_dynamodb = None
_table    = None


def _get_table():
    global _dynamodb, _table
    if _table is None:
        _dynamodb = boto3.resource("dynamodb", region_name=os.environ.get("AWS_REGION", "us-east-1"))
        _table = _dynamodb.Table(os.environ["WISHLIST_TABLE_NAME"])
    return _table


def handler(event, context):
    method      = event.get("requestContext", {}).get("http", {}).get("method", "GET")
    raw_path    = event.get("rawPath", "")
    path_params = event.get("pathParameters") or {}

    table = _get_table()

    # GET /api/wishlist/check/{symbol}
    if "check" in raw_path and path_params.get("symbol"):
        symbol = path_params["symbol"].upper()
        resp   = table.get_item(Key={"user_id": USER_ID, "symbol": symbol})
        return _json({"in_wishlist": "Item" in resp})

    # DELETE /api/wishlist/{symbol}
    if method == "DELETE" and path_params.get("symbol"):
        symbol = path_params["symbol"].upper()
        table.delete_item(Key={"user_id": USER_ID, "symbol": symbol})
        return _json({"removed": symbol})

    # POST /api/wishlist
    if method == "POST":
        body   = json.loads(event.get("body") or "{}")
        symbol = (body.get("symbol") or "").upper().strip()
        name   = (body.get("name") or symbol).strip()
        if not symbol:
            return _json({"error": "symbol required"}, 400)
        table.put_item(Item={
            "user_id":  USER_ID,
            "symbol":   symbol,
            "name":     name,
            "added_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        })
        return _json({"added": symbol})

    # GET /api/wishlist
    response = table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key("user_id").eq(USER_ID)
    )
    items = [{"symbol": i["symbol"], "name": i.get("name", i["symbol"])}
             for i in response.get("Items", [])]
    return _json({"wishlist": items})


def _json(data: dict, status: int = 200):
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(data),
    }
