"""
Lambda handler: GET /api/news?symbol=INFY
Wraps SentimentAgent from backend/agents/sentiment_agent.py
"""
import json
import asyncio

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

    async def _analyse():
        score, reasons = await _agent.get_sentiment_score(bare, name)
        articles = await _agent.get_news(bare)
        return score, reasons, articles

    try:
        score, reasons, articles = asyncio.run(_analyse())
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
                "news":            articles[:20],   # Top 20 headlines (frontend reads "news" key)
            }),
        }
    except Exception as e:
        print(f"[news_sentiment] Error: {e}")
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": json.dumps({"error": str(e)}),
        }
