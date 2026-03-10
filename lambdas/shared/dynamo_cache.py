"""
Shared DynamoDB cache helper.
Replaces the in-memory _cache dict in the local FastAPI app.py
"""
import json
import os
import time
import boto3
from boto3.dynamodb.conditions import Key

_dynamodb = None
_table    = None

def _get_table():
    global _dynamodb, _table
    if _table is None:
        _dynamodb = boto3.resource("dynamodb", region_name=os.environ.get("AWS_REGION", "us-east-1"))
        _table = _dynamodb.Table(os.environ["CACHE_TABLE_NAME"])
    return _table


def get_cached(cache_key: str) -> dict | None:
    """
    Returns the cached data dict if it exists and hasn't expired.
    Returns None if cache miss or expired.
    """
    try:
        table = _get_table()
        response = table.get_item(Key={"cache_key": cache_key})
        item = response.get("Item")
        if not item:
            return None
        # Check if expired (DynamoDB TTL deletion is eventual, not instantaneous)
        if int(item.get("expires_at", 0)) < int(time.time()):
            return None
        return json.loads(item["data"])
    except Exception as e:
        print(f"[dynamo_cache] get_cached error for {cache_key}: {e}")
        return None


def set_cached(cache_key: str, data: dict, ttl_seconds: int = 300) -> None:
    """
    Stores data in DynamoDB cache with a TTL.
    """
    try:
        table = _get_table()
        table.put_item(Item={
            "cache_key":  cache_key,
            "data":       json.dumps(data, default=str),
            "expires_at": int(time.time()) + ttl_seconds,
            "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        })
    except Exception as e:
        print(f"[dynamo_cache] set_cached error for {cache_key}: {e}")


def delete_all() -> int:
    """
    Deletes all items in the cache table.
    Returns the count of deleted items.
    """
    try:
        table = _get_table()
        scan = table.scan(ProjectionExpression="cache_key")
        deleted = 0
        with table.batch_writer() as batch:
            for item in scan["Items"]:
                batch.delete_item(Key={"cache_key": item["cache_key"]})
                deleted += 1
        return deleted
    except Exception as e:
        print(f"[dynamo_cache] delete_all error: {e}")
        return 0
