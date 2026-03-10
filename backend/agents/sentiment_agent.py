"""
====================================================
  Sentiment Analysis Agent
  ─────────────────────────────────────────────────
  Fetches news headlines via FREE RSS feeds and
  scores them with VADER (runs 100% offline).

  News sources used (all FREE, no API key):
    • Google News RSS
    • Yahoo Finance RSS

  Returns a score between -50 and +50
    positive → bullish sentiment
    negative → bearish sentiment
====================================================
"""

import asyncio
import logging
import re
from typing import List, Optional, Tuple
from datetime import datetime, timezone, timedelta

import feedparser
from email.utils import parsedate_to_datetime
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# ── Stop words for title deduplication ────────────────────
_STOP_WORDS = {
    "the", "a", "an", "of", "in", "on", "at", "for", "to", "is", "are",
    "was", "were", "and", "or", "but", "by", "with", "as", "its", "it",
    "this", "that", "from", "into", "up", "down", "over", "under", "be",
    "has", "have", "had", "will", "would", "could", "should", "may", "can",
}


def _normalize_title(title: str) -> str:
    """
    Lowercase, strip punctuation, remove stop words.
    Returns a condensed key for near-duplicate detection.
    """
    t = title.lower()
    t = re.sub(r"[^a-z0-9 ]", " ", t)
    words = [w for w in t.split() if w and w not in _STOP_WORDS]
    return " ".join(words[:12])   # first 12 meaningful words

logger = logging.getLogger(__name__)

# ── Finance-domain lexicon injected into VADER ────────────
# VADER was trained on social media; these additions steer it
# toward correct interpretation of financial language.
_FINANCE_LEXICON = {
    # Strongly bullish
    "breakout":       2.5,  "rally":          2.0,  "surged":         2.0,
    "outperform":     2.5,  "bullish":        2.5,  "upgrade":        2.5,
    "beats":          1.5,  "beat":           1.5,  "upside":         1.5,
    "profitability":  1.5,  "dividend":       1.0,  "buyback":        1.5,
    "expansion":      1.5,  "record-high":    2.0,  "overweight":     1.5,
    "accumulation":   1.5,  "rebound":        1.8,  "recovery":       1.5,
    "strong-buy":     3.0,  "revenue-beat":   2.5,  "earnings-beat":  2.5,
    # Strongly bearish
    "breakdown":     -2.5,  "crash":         -3.0,  "downgrade":     -2.5,
    "bearish":       -2.5,  "underperform":  -2.5,  "underweight":   -1.5,
    "misses":        -1.5,  "miss":          -1.5,  "downside":      -1.5,
    "bankruptcy":    -3.0,  "fraud":         -3.0,  "investigation": -2.0,
    "recall":        -2.0,  "layoffs":       -2.0,  "restructuring": -1.5,
    "plunged":       -2.5,  "slumped":       -2.0,  "correction":    -1.5,
    "strong-sell":   -3.0,  "revenue-miss":  -2.5,  "earnings-miss": -2.5,
    # Finance-adjusted neutrals (VADER often mis-scores these)
    "support":        0.8,   # "finding support" is positive in finance
    "resistance":    -0.5,   # "hitting resistance" is negative
    "volatile":      -0.5,   # uncertainty is mildly negative
    "consolidation":  0.3,
    "flat":          -0.3,
}

# ── VADER analyser (loaded once, enhanced with finance lexicon) ──
_vader = SentimentIntensityAnalyzer()
_vader.lexicon.update(_FINANCE_LEXICON)


def _recency_weight(published_str: str) -> float:
    """
    Returns a weight based on how recent a headline is:
      ≤ 6 h  → 1.00   (very fresh)
      ≤ 24 h → 0.85
      ≤ 48 h → 0.65
      ≤ 72 h → 0.45
      older  → 0.30
    Defaults to 0.70 if the date cannot be parsed.
    """
    try:
        pub = parsedate_to_datetime(published_str)
        if pub.tzinfo is None:
            pub = pub.replace(tzinfo=timezone.utc)
        hours_old = (datetime.now(timezone.utc) - pub).total_seconds() / 3600
        if hours_old <= 6:   return 1.00
        if hours_old <= 24:  return 0.85
        if hours_old <= 48:  return 0.65
        if hours_old <= 72:  return 0.45
        return 0.30
    except Exception:
        return 0.70


class SentimentAgent:

    async def get_news(self, symbol: Optional[str] = None) -> List[dict]:
        """Fetch and score news headlines. Returns list of news dicts."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._fetch_news, symbol)

    async def get_sentiment_score(self, symbol: str, company_name: str) -> Tuple[float, List[str]]:
        """
        Returns (score -50…+50, list_of_reason_strings).
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._score, symbol, company_name)

    # ── Sync workers ─────────────────────────────────────

    def _fetch_news(self, symbol: Optional[str]) -> List[dict]:
        headlines = []
        urls = self._build_feed_urls(symbol)

        for url in urls:
            try:
                feed = feedparser.parse(url)
                for entry in feed.entries[:8]:
                    title   = entry.get("title", "")
                    summary = entry.get("summary", "")
                    text    = title + " " + summary
                    score   = _vader.polarity_scores(text)["compound"]

                    sentiment_label = "Positive" if score > 0.05 else ("Negative" if score < -0.05 else "Neutral")
                    sentiment_icon  = "📈" if score > 0.05 else ("📉" if score < -0.05 else "➡️")

                    headlines.append({
                        "title":      title[:120],
                        "source":     entry.get("source", {}).get("title", "News") if hasattr(entry.get("source", {}), "get") else "News",
                        "published":  entry.get("published", ""),
                        "link":       entry.get("link", "#"),
                        "sentiment":  sentiment_label,
                        "sentiment_icon": sentiment_icon,
                        "score":      round(score, 3),
                    })
            except Exception as e:
                logger.warning(f"Feed error ({url}): {e}")

        # De-duplicate using normalised title (catches syndicated near-duplicates)
        seen   = set()
        unique = []
        for item in headlines:
            key = _normalize_title(item["title"])
            if key not in seen:
                seen.add(key)
                unique.append(item)

        return unique[:15]

    def _score(self, symbol: str, company_name: str) -> tuple:
        """
        Calculate aggregate sentiment score for a specific stock.
        Improvements vs original:
          • Scores title + summary (not title alone) — more signal per article
          • Weighted average by recency (fresh news counts more)
          • Finance-domain VADER lexicon applied globally
        """
        urls            = self._build_feed_urls(symbol, company_name)
        weighted_scores = []   # list of (compound_score, recency_weight)
        reasons         = []

        for url in urls:
            try:
                feed = feedparser.parse(url)
                for entry in feed.entries[:5]:
                    title   = entry.get("title",   "")
                    summary = entry.get("summary", "")
                    text    = (title + " " + summary).strip()   # FIX: was title-only
                    vs      = _vader.polarity_scores(text)["compound"]
                    weight  = _recency_weight(entry.get("published", ""))
                    weighted_scores.append((vs, weight))
            except Exception:
                pass

        if not weighted_scores:
            return 0.0, ["No recent news found — neutral sentiment assumed"]

        # Recency-weighted average
        total_weight = sum(w for _, w in weighted_scores)
        avg_score    = sum(s * w for s, w in weighted_scores) / total_weight

        # Normalise from [-1,+1] → [-50,+50]
        normalised = round(avg_score * 50, 1)

        if normalised > 15:
            reasons.append(f"Recent news is mostly positive (sentiment score: {normalised:.0f}/50)")
        elif normalised < -15:
            reasons.append(f"Recent news is mostly negative (sentiment score: {normalised:.0f}/50)")
        else:
            reasons.append(f"Recent news is mixed/neutral (sentiment score: {normalised:.0f}/50)")

        return normalised, reasons

    # ── Feed URL builder ─────────────────────────────────

    @staticmethod
    def _build_feed_urls(symbol: Optional[str] = None,
                         company_name: str = "") -> List[str]:
        urls = []

        # Google News – general Indian market
        urls.append(
            "https://news.google.com/rss/search?q=stock+market+today&hl=en-IN&gl=IN&ceid=IN:en"
        )

        # Economic Times Markets – high-quality Indian financial news
        urls.append(
            "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms"
        )

        # Moneycontrol – most popular Indian finance portal
        urls.append(
            "https://www.moneycontrol.com/rss/MCtopnews.xml"
        )

        # Business Standard Markets – premium Indian business news
        urls.append(
            "https://www.business-standard.com/rss/markets-106.rss"
        )

        if symbol:
            # Strip .NS / .BO suffix for search
            clean = symbol.replace(".NS", "").replace(".BO", "")
            query = company_name if company_name else clean

            # Google News RSS – specific stock
            q_encoded = query.replace(" ", "+")
            urls.append(
                f"https://news.google.com/rss/search?q={q_encoded}+stock&hl=en-IN&gl=IN&ceid=IN:en"
            )

            # Yahoo Finance RSS (works for US symbols)
            if not symbol.endswith((".NS", ".BO")):
                urls.append(
                    f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={symbol}&region=US&lang=en-US"
                )

        return urls