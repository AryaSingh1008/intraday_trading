"""
AI Signal Validator — Claude Haiku 3.5 via Bedrock InvokeModel
──────────────────────────────────────────────────────────────
Called when a user opens the stock detail modal.
Receives ALL pre-computed indicators and returns a grounded AI thesis.
Never invents numbers — only reasons about data it's given.

Prompt is loaded from: prompts/signal_validator.yaml
"""
import json
import logging
import sys
import os
import boto3

# Allow importing prompt_loader from the shared Lambda layer or local backend/
_HERE = os.path.dirname(os.path.abspath(__file__))
for _candidate in [
    os.path.join(_HERE, "..", "..", "backend"),          # local dev
    os.path.join(_HERE, "..", "shared"),                 # Lambda layer
    "/opt/python",                                       # Lambda /opt layer
]:
    if os.path.isdir(_candidate) and _candidate not in sys.path:
        sys.path.insert(0, _candidate)

from prompt_loader import load_prompt, validate_response  # noqa: E402

logger = logging.getLogger(__name__)

_client = None


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
        cfg = _build_prompt_cfg(stock_data)
        client = _get_client()

        response = client.invoke_model(
            modelId=cfg["model"],
            contentType="application/json",
            accept="application/json",
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": cfg["max_tokens"],
                "temperature": cfg["temperature"],
                "messages": [{"role": "user", "content": cfg["user"]}],
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


def _build_prompt_cfg(s: dict) -> dict:
    """Build the prompt config by loading the template and injecting stock data."""
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
    vol_ratio = round(volume / avg_volume, 2) if avg_volume and volume else "N/A"
    dist_high = round((price / high_52w - 1) * 100, 1) if high_52w and price else "N/A"
    dist_low = round((price / low_52w - 1) * 100, 1) if low_52w and price else "N/A"

    return load_prompt("signal_validator", {
        "symbol": symbol,
        "name": name,
        "sector": sector,
        "signal": signal,
        "score": score,
        "tech_score": tech_score,
        "sent_score": sent_score,
        "tech_weight": f"{tech_w:.0%}",
        "sent_weight": f"{sent_w:.0%}",
        "price": price,
        "change_pct": f"{change_pct:+.2f}",
        "volume": f"{volume:,}",
        "avg_volume": f"{avg_volume:,}",
        "vol_ratio": vol_ratio,
        "high_52w": high_52w or "N/A",
        "low_52w": low_52w or "N/A",
        "dist_high": dist_high,
        "dist_low": dist_low,
        "vwap": vwap or "N/A",
        "support": support or "N/A",
        "resistance": resistance or "N/A",
        "rs_ratio": rs_ratio or "N/A",
        "target_price": target_price or "N/A",
        "stop_loss": stop_loss or "N/A",
        "target_buy": target_buy or "N/A",
        "risk": risk,
        "reasons_str": reasons_str,
    })


def _parse_response(text: str) -> dict:
    """Parse Claude's JSON response, validate against schema, with fallback."""
    # Strip markdown fences if present
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1]
    if text.endswith("```"):
        text = text.rsplit("```", 1)[0]
    text = text.strip()

    try:
        data = json.loads(text)
        validate_response("signal_validator", data)
        return {
            "ai_thesis": data.get("thesis", ""),
            "ai_confidence": data.get("confidence", "MEDIUM"),
            "ai_signal_agrees": data.get("agrees", True),
            "ai_risk_flags": data.get("risk_flags", [])[:3],
            "ai_contradictions": data.get("contradictions", [])[:2],
            "ai_available": True,
        }
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        logger.warning("Failed to parse/validate AI response: %s — raw: %s", e, text[:200])
        # Fallback: use raw text as thesis
        return {
            "ai_thesis": text[:300] if text else None,
            "ai_confidence": None,
            "ai_signal_agrees": None,
            "ai_risk_flags": [],
            "ai_contradictions": [],
            "ai_available": bool(text),
        }
