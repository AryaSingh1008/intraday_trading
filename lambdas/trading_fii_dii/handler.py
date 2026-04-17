"""
Lambda handler: GET /api/fii-dii
Returns today's FII and DII net buy/sell activity from NSE.
Used as a market-level sentiment modifier — if FIIs are heavy net sellers,
all stock signals should be treated with more caution.
"""
import json
import logging
import urllib.request
import urllib.error
from datetime import datetime
from zoneinfo import ZoneInfo

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

IST = ZoneInfo("Asia/Kolkata")

_NSE_FII_DII_URL = "https://www.nseindia.com/api/fiidiiTradeReact"

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept":     "application/json, text/plain, */*",
    "Referer":    "https://www.nseindia.com/",
}


def _fetch_fii_dii() -> dict:
    try:
        req = urllib.request.Request(_NSE_FII_DII_URL, headers=_HEADERS)
        with urllib.request.urlopen(req, timeout=8) as resp:
            raw = json.loads(resp.read())
        # NSE returns a list of daily rows; take the most recent row
        rows = raw if isinstance(raw, list) else raw.get("data", [])
        if not rows:
            return _empty()
        today = rows[0]

        def _net(row, key_buy, key_sell):
            try:
                return round(float(row.get(key_buy, 0) or 0) - float(row.get(key_sell, 0) or 0), 2)
            except Exception:
                return 0.0

        fii_net = _net(today, "fiiBuyValue",  "fiiSellValue")
        dii_net = _net(today, "diiBuyValue",  "diiSellValue")

        # Market bias: if FII net < -2000 Cr = strongly bearish, > +2000 = strongly bullish
        if fii_net <= -2000:
            market_bias    = "BEARISH"
            bias_reason    = f"FIIs sold ₹{abs(fii_net):,.0f} Cr net today — heavy institutional selling, market under pressure"
            score_modifier = -8
        elif fii_net >= 2000:
            market_bias    = "BULLISH"
            bias_reason    = f"FIIs bought ₹{fii_net:,.0f} Cr net today — strong institutional buying, market has tailwind"
            score_modifier = +5
        elif fii_net <= -500:
            market_bias    = "MILDLY BEARISH"
            bias_reason    = f"FIIs sold ₹{abs(fii_net):,.0f} Cr net today — mild institutional selling"
            score_modifier = -3
        elif fii_net >= 500:
            market_bias    = "MILDLY BULLISH"
            bias_reason    = f"FIIs bought ₹{fii_net:,.0f} Cr net today — mild institutional buying"
            score_modifier = +2
        else:
            market_bias    = "NEUTRAL"
            bias_reason    = f"FII net activity is minimal (₹{fii_net:,.0f} Cr) — market driven by retail/DII flow"
            score_modifier = 0

        return {
            "date":           today.get("date", datetime.now(IST).strftime("%d-%b-%Y")),
            "fii_buy":        float(today.get("fiiBuyValue",  0) or 0),
            "fii_sell":       float(today.get("fiiSellValue", 0) or 0),
            "fii_net":        fii_net,
            "dii_buy":        float(today.get("diiBuyValue",  0) or 0),
            "dii_sell":       float(today.get("diiSellValue", 0) or 0),
            "dii_net":        dii_net,
            "market_bias":    market_bias,
            "bias_reason":    bias_reason,
            "score_modifier": score_modifier,
            "source":         "NSE",
        }
    except Exception as e:
        log.warning("FII/DII fetch failed: %s", e)
        return _empty()


def _empty() -> dict:
    return {
        "date":           datetime.now(IST).strftime("%d-%b-%Y"),
        "fii_net":        0,
        "dii_net":        0,
        "market_bias":    "UNAVAILABLE",
        "bias_reason":    "FII/DII data temporarily unavailable — NSE API may be down",
        "score_modifier": 0,
        "source":         "unavailable",
    }


def handler(event, context):
    data = _fetch_fii_dii()
    log.info("FII/DII result: %s", data)
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type":                "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(data),
    }
