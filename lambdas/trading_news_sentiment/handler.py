"""
Lambda handler: GET /api/news?symbol=INFY
Wraps SentimentAgent from backend/agents/sentiment_agent.py
"""
import json
import os

from backend.agents.sentiment_agent import SentimentAgent

_agent = None

def handler(event, context):
    global _agent
    if _agent is None:
        _agent = SentimentAgent()

    qs     = event.get("queryStringParameters") or {}
    symbol = (qs.get("symbol") or "").upper().strip()
    name   = qs.get("name") or symbol

    # Map symbol to company name if not provided
    NAMES = {
        "RELIANCE": "Reliance Industries", "TCS": "Tata Consultancy Services",
        "INFY": "Infosys", "HDFCBANK": "HDFC Bank", "ICICIBANK": "ICICI Bank",
        "WIPRO": "Wipro", "TATAMOTORS": "Tata Motors", "SBIN": "State Bank of India",
        "AXISBANK": "Axis Bank", "KOTAKBANK": "Kotak Mahindra Bank",
        "BAJFINANCE": "Bajaj Finance", "SUNPHARMA": "Sun Pharmaceutical",
        "MARUTI": "Maruti Suzuki", "LT": "Larsen & Toubro", "ONGC": "ONGC",
    }
    bare = symbol.replace(".NS", "").replace(".BO", "")
    if name == symbol and bare in NAMES:
        name = NAMES[bare]

    try:
        score, reasons, articles = _agent.get_sentiment_score(bare, name)
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps({
                "symbol":          bare,
                "sentiment_score": round(score, 2),
                "reasons":         reasons,
                "articles":        articles[:10],   # Top 10 headlines
            }),
        }
    except Exception as e:
        print(f"[news_sentiment] Error: {e}")
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": json.dumps({"error": str(e)}),
        }
