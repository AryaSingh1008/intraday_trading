"""
Lambda handler: DELETE /api/cache
Clears all DynamoDB cache entries (equivalent to _cache.clear() in app.py).
"""
import json
import dynamo_cache


def handler(event, context):
    count = dynamo_cache.delete_all()
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps({
            "message": f"Cache cleared — {count} entries deleted",
            "deleted": count,
        }),
    }
