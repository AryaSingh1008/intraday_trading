"""
Lambda handler: POST /api/chat
Invokes the Bedrock TradingAdvisorAgent (TradingGuru) and returns its response.

Request body:  { "message": "Should I buy INFY today?", "session_id": "optional-uuid" }
Response body: { "response": "...", "session_id": "uuid" }

Post-processing: append contextual follow-up suggestions if the agent
did not already include them, keeping the chat always interactive.
"""
import json
import os
import re
import boto3

_client = None

def _get_client():
    global _client
    if _client is None:
        _client = boto3.client(
            "bedrock-agent-runtime",
            region_name=os.environ.get("AWS_REGION", "us-east-1")
        )
    return _client


AGENT_ID       = os.environ.get("BEDROCK_AGENT_ID", "")
AGENT_ALIAS_ID = os.environ.get("BEDROCK_AGENT_ALIAS_ID", "TSTALIASID")

# ── All supported NSE stocks ──────────────────────────────────────────────────
NSE_STOCKS = {
    "RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK",
    "WIPRO", "TATAMOTORS", "SBIN", "AXISBANK", "KOTAKBANK",
    "BAJFINANCE", "SUNPHARMA", "MARUTI", "LT", "ONGC",
    "ADANIENT", "ADANIPORTS", "APOLLOHOSP", "ASIANPAINT", "BAJAJ-AUTO",
    "BAJAJFINSV", "BEL", "BPCL", "BHARTIARTL", "BRITANNIA",
    "CIPLA", "COALINDIA", "DRREDDY", "EICHERMOT", "GRASIM",
    "HCLTECH", "HDFCLIFE", "HEROMOTOCO", "HINDALCO", "HINDUNILVR",
    "INDUSINDBK", "ITC", "JIOFIN", "JSWSTEEL", "LTIM",
    "M&M", "NESTLEIND", "NTPC", "POWERGRID", "SHRIRAMFIN",
    "TATACONSUM", "TATASTEEL", "TECHM", "TITAN", "TRENT", "ULTRACEMCO",
}

# ── Common nicknames / abbreviations → canonical NSE symbol ──────────────────
# Users often say "icici", "sbi", "hdfc" etc. instead of exact NSE codes.
# _detect_intent() appends the canonical symbol to the expanded message so the
# stock regex can match it.
NSE_ALIASES = {
    "icici bank":         "ICICIBANK",
    "icici":              "ICICIBANK",
    "hdfc bank":          "HDFCBANK",
    "hdfc":               "HDFCBANK",
    "sbi":                "SBIN",
    "state bank":         "SBIN",
    "infosys":            "INFY",
    "tata motors":        "TATAMOTORS",
    "bajaj finance":      "BAJFINANCE",
    "bajaj fin":          "BAJFINANCE",
    "axis bank":          "AXISBANK",
    "axis":               "AXISBANK",
    "kotak bank":         "KOTAKBANK",
    "kotak mahindra":     "KOTAKBANK",
    "kotak":              "KOTAKBANK",
    "hero motocorp":      "HEROMOTOCO",
    "hero moto":          "HEROMOTOCO",
    "hero":               "HEROMOTOCO",
    "adani enterprises":  "ADANIENT",
    "adani":              "ADANIENT",
    "tata steel":         "TATASTEEL",
    "hindustan unilever": "HINDUNILVR",
    "hul":                "HINDUNILVR",
    "nestle india":       "NESTLEIND",
    "nestle":             "NESTLEIND",
    "asian paints":       "ASIANPAINT",
    "dr reddy":           "DRREDDY",
    "dr. reddy":          "DRREDDY",
    "indusind":           "INDUSINDBK",
    "indusind bank":      "INDUSINDBK",
    "sun pharma":         "SUNPHARMA",
    "sun pharmaceutical": "SUNPHARMA",
    "mahindra":           "M&M",
    "m&m":                "M&M",
    "jswsteel":           "JSWSTEEL",
    "jsw steel":          "JSWSTEEL",
    "jsw":                "JSWSTEEL",
    "l&t":                "LT",
    "larsen":             "LT",
    "larsen toubro":      "LT",
    "trent":              "TRENT",
    "titan":              "TITAN",
    "techm":              "TECHM",
    "tech mahindra":      "TECHM",
    "hcl tech":           "HCLTECH",
    "hcl":                "HCLTECH",
    "wipro":              "WIPRO",
    "reliance":           "RELIANCE",
}

# ── Intent detection patterns ─────────────────────────────────────────────────
_STOCK_RE     = re.compile(
    r'\b(' + '|'.join(re.escape(s) for s in NSE_STOCKS) + r')(?:\.NS)?\b',
    re.IGNORECASE
)
_COMPARE_RE   = re.compile(
    r'\b(compare|vs\.?|versus|better|which is|difference between)\b',
    re.IGNORECASE
)
_BEST_RE      = re.compile(
    r'\b(best|top picks?|which stocks?|recommend|momentum|strong buy|outperform)\b',
    re.IGNORECASE
)
_MARKET_RE    = re.compile(
    r'\b(market|nifty|sensex|overall|today|bullish|bearish|trend|index)\b',
    re.IGNORECASE
)
_EDUCATION_RE = re.compile(
    r'\b(what is|what are|explain|how does|define|meaning of|rsi|macd|ema|sma|bollinger|adx|atr|stochastic|ai score|signal|divergence)\b',
    re.IGNORECASE
)
_PORTFOLIO_RE = re.compile(
    r'\b(i bought|i have|my portfolio|holding|loss|profit|bought at|exit|add more|average down)\b',
    re.IGNORECASE
)
_SECTOR_RE    = re.compile(
    r'\b(sector|it stocks?|banking stocks?|pharma stocks?|fmcg|auto stocks?|energy stocks?|infrastructure)\b',
    re.IGNORECASE
)
_SENTIMENT_RE = re.compile(
    r'\b(news|sentiment|headlines?|buzz|media|articles?|latest on|update on|positive news|negative news)\b',
    re.IGNORECASE
)
_HELP_RE      = re.compile(
    r'\b(what can you do|how (do i|to) use|help|capabilities|features|what questions)\b',
    re.IGNORECASE
)
_TECHNICAL_RE = re.compile(
    r'\b(analyse|analyze|signal|should i buy|should i sell|target price|stop.?loss|overbought|oversold|is .* good)\b',
    re.IGNORECASE
)


def _detect_intent(message: str):
    """Returns (primary_stock | None, intent_tag)."""
    # Expand common nicknames so "icici" → ICICIBANK, "sbi" → SBIN, etc.
    msg_lower = message.lower()
    expanded  = message
    for alias, symbol in NSE_ALIASES.items():
        if alias in msg_lower:
            expanded = expanded + " " + symbol  # append canonical symbol for regex to match
    stocks = _STOCK_RE.findall(expanded)
    stock  = stocks[0].upper() if stocks else None

    if _HELP_RE.search(message):
        return stock, "help"
    if _COMPARE_RE.search(message) and len(stocks) >= 2:
        return stock, "compare"
    if _BEST_RE.search(message):
        return stock, "best"
    if _PORTFOLIO_RE.search(message):
        return stock, "portfolio"
    if _SECTOR_RE.search(message):
        return stock, "sector"
    if _EDUCATION_RE.search(message):
        return stock, "education"
    if _SENTIMENT_RE.search(message):
        return stock, "sentiment"
    if _MARKET_RE.search(message):
        return stock, "market"
    if _TECHNICAL_RE.search(message) or stock:
        return stock, "technical"
    return stock, "general"


def _build_followup(message: str, stock, intent: str) -> str:
    """Build a contextual 'explore next' block with 4 numbered suggestions."""
    lines = ["\n\n---", "**What would you like to explore next?**", ""]

    if stock and intent in ("technical", "portfolio"):
        alt = "TCS" if stock != "TCS" else "INFY"
        lines += [
            f"1. 📰 **News check** — *\"What's the latest news on {stock}?\"*",
            f"2. 🔄 **Compare** — *\"Compare {stock} with {alt}\"*",
            f"3. 🌐 **Top picks today** — *\"Which stocks have the best momentum?\"*",
            f"4. 💼 **Track it** — Open the **My Portfolio** tab to record your trade",
        ]

    elif stock and intent == "sentiment":
        lines += [
            f"1. 📊 **Full signal** — *\"Should I buy {stock} today?\"*",
            f"2. 🎯 **Target price** — *\"What is the target price for {stock}?\"*",
            f"3. 🔄 **Compare** — *\"Compare {stock} with another stock\"*",
            f"4. 💼 **Track it** — Open the **My Portfolio** tab to add your holdings",
        ]

    elif stock and intent == "compare":
        lines += [
            f"1. 📊 **Deep dive** — *\"Analyse {stock} in detail\"*",
            f"2. 🎯 **Target prices** — *\"What is the target price for {stock}?\"*",
            f"3. 🌐 **Best stocks today** — *\"Which stocks should I buy today?\"*",
            f"4. 🏭 **Sector view** — *\"How is the IT sector doing?\"*",
        ]

    elif intent == "best":
        lines += [
            "1. 📊 **Analyse a pick** — *\"Should I buy INFY?\"* or *\"Analyse TCS\"*",
            "2. 🏭 **Sector view** — *\"How is the IT sector doing?\"*",
            "3. 📰 **Market news** — *\"What's the latest financial news?\"*",
            "4. 💼 **My Portfolio** — Track the stocks you buy in the **My Portfolio** tab",
        ]

    elif intent == "market":
        lines += [
            "1. 📊 **Pick a stock** — *\"Should I buy HDFCBANK today?\"*",
            "2. 🏭 **Sector check** — *\"How are banking stocks doing?\"*",
            "3. 🌐 **Top momentum** — *\"Which stocks have the best momentum right now?\"*",
            "4. 🎓 **Learn** — *\"What does bullish mean?\"* or *\"Explain MACD\"*",
        ]

    elif intent == "education":
        lines += [
            "1. 📊 **See it live** — *\"Check RSI for INFY\"* or *\"Analyse RELIANCE\"*",
            "2. 🎓 **More concepts** — *\"What is MACD?\"* or *\"Explain Bollinger Bands\"*",
            "3. 🌐 **Best picks** — *\"Which stocks should I buy today?\"*",
            "4. 💡 **AI Score** — *\"How is the AI score calculated?\"*",
        ]

    elif intent == "sector":
        lines += [
            "1. 📊 **Specific stock** — *\"Analyse HCLTECH\"* or *\"Should I buy BHARTIARTL?\"*",
            "2. 🔄 **Compare** — *\"Compare TCS vs INFY\"*",
            "3. 🌐 **Top picks** — *\"Which stocks have the best momentum today?\"*",
            "4. 📰 **Sector news** — *\"What's the latest news on Indian IT stocks?\"*",
        ]

    elif intent == "help":
        lines += [
            "1. 📊 **Try an analysis** — *\"Should I buy RELIANCE today?\"*",
            "2. 🎓 **Learn** — *\"What is RSI?\"* or *\"Explain the AI score\"*",
            "3. 🔄 **Compare** — *\"Compare TCS vs INFY\"*",
            "4. 🌐 **Find opportunities** — *\"Which stocks have the best momentum?\"*",
        ]

    else:
        lines += [
            "1. 📊 **Analyse a stock** — *\"Should I buy INFY?\"* or *\"Analyse TCS\"*",
            "2. 🎯 **Target prices** — *\"What is the target price for RELIANCE?\"*",
            "3. 🔄 **Compare stocks** — *\"Compare HDFCBANK vs SBIN\"*",
            "4. 🌐 **Top picks** — *\"Which stocks should I buy today?\"*",
        ]

    lines += [
        "",
        "> 💡 **43 stocks supported:** ADANIENT · ITC · TITAN · BHARTIARTL · HINDALCO · "
        "NESTLEIND · TRENT · HCLTECH · and all other NIFTY 50 stocks",
        "> 🎓 **Curious?** Ask *\"What is RSI?\"*, *\"Explain MACD\"*, or *\"What does bearish mean?\"*",
    ]

    return "\n".join(lines)


def handler(event, context):
    body       = json.loads(event.get("body") or "{}")
    message    = (body.get("message") or "").strip()
    session_id = body.get("session_id") or context.aws_request_id

    if not message:
        return _json({"error": "message is required"}, 400)

    if not AGENT_ID:
        return _json({
            "error": "Bedrock Agent not configured. Set BEDROCK_AGENT_ID env variable.",
            "hint":  "Run: terraform output bedrock_agent_id",
        }, 503)

    try:
        client   = _get_client()
        response = client.invoke_agent(
            agentId      = AGENT_ID,
            agentAliasId = AGENT_ALIAS_ID,
            sessionId    = session_id,
            inputText    = message,
        )

        # Collect streamed chunks
        completion = ""
        for event_chunk in response.get("completion", []):
            chunk = event_chunk.get("chunk", {})
            if "bytes" in chunk:
                completion += chunk["bytes"].decode("utf-8")

        if not completion:
            completion = "I wasn't able to generate a response. Please try again."

        # Append follow-up suggestions if agent didn't already include them
        if "explore next" not in completion.lower() and \
           "what would you like" not in completion.lower():
            stock, intent = _detect_intent(message)
            completion += _build_followup(message, stock, intent)

        return _json({"response": completion, "session_id": session_id})

    except Exception as e:
        print(f"[bedrock_chat] Error: {type(e).__name__}: {e}")
        return _json({"error": f"Agent error: {str(e)}"}, 500)


def _json(data: dict, status: int = 200):
    return {
        "statusCode": status,
        "headers": {
            "Content-Type":                "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(data),
    }
