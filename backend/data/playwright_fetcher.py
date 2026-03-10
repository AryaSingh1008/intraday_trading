"""
Playwright NSE Option Chain Fetcher
=====================================
Uses a real headless Chrome browser (system Chrome) to bypass Akamai
bot protection on NSE's option chain API.

Architecture
------------
- One persistent Playwright browser process (launched at startup).
- A background asyncio task calls `refresh_all()` every 150 seconds.
- Results are stored in `PlaywrightFetcher._cache[symbol]` as raw NSE JSON.
- `OptionsFetcher._fetch()` reads from this cache first (if fresh).

Graceful degradation
--------------------
- If Playwright is not installed → logs a warning, module is a no-op.
- If a symbol fetch fails → that symbol keeps its previous cached value.
- If browser crashes → browser is re-launched on next refresh cycle.
"""

import asyncio
import json
import logging
import time
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)

# Symbols to keep warm in the background
WARM_SYMBOLS = ["NIFTY", "BANKNIFTY", "RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK"]

# Cache TTL — reject data older than this
CACHE_TTL_SECONDS = 600   # 10 minutes

# ── Module-level state ────────────────────────────────────────────────────────
_cache: Dict[str, Tuple[dict, float]] = {}   # symbol → (raw_nse_dict, timestamp)
_browser = None
_playwright_obj = None
_available = False

try:
    from playwright.async_api import async_playwright, Browser, Page
    _available = True
except ImportError:
    logger.warning(
        "playwright not installed — NSE live option chain unavailable. "
        "Install with: pip install playwright && playwright install chrome"
    )


# ── Public helpers ────────────────────────────────────────────────────────────

def get_cached(symbol: str) -> Optional[dict]:
    """
    Return cached raw NSE option chain data for *symbol*, or None if:
    - no cache entry exists, or
    - the cached entry is older than CACHE_TTL_SECONDS.
    """
    entry = _cache.get(symbol.upper())
    if entry is None:
        return None
    raw_data, ts = entry
    if (time.time() - ts) > CACHE_TTL_SECONDS:
        return None
    return raw_data


def is_available() -> bool:
    return _available


# ── Internal browser helpers ──────────────────────────────────────────────────

async def _launch_browser():
    """Launch (or re-launch) the Playwright browser."""
    global _browser, _playwright_obj
    try:
        if _playwright_obj is None:
            _playwright_obj = await async_playwright().start()
        if _browser is not None:
            try:
                await _browser.close()
            except Exception:
                pass
        # Use system Chrome (no separate Chromium download needed)
        _browser = await _playwright_obj.chromium.launch(
            channel="chrome",
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--disable-setuid-sandbox",
            ],
        )
        logger.info("Playwright Chrome browser launched.")
    except Exception as e:
        logger.error(f"Playwright browser launch failed: {e}")
        _browser = None


async def _fetch_symbol(symbol: str) -> Optional[dict]:
    """
    Open a new page, navigate to NSE option-chain, intercept the API JSON
    response, and return the raw parsed dict.
    """
    global _browser
    if _browser is None:
        return None

    is_index = symbol in ("NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY")
    api_path  = "option-chain-indices" if is_index else "option-chain-equities"
    api_url   = f"https://www.nseindia.com/api/{api_path}?symbol={symbol}"

    intercepted: Optional[dict] = None
    page: Optional[Page] = None

    try:
        page = await _browser.new_page()

        # Mask automation fingerprints
        await page.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        await page.set_extra_http_headers({
            "Accept-Language": "en-US,en;q=0.9",
            "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        })

        # Intercept the API response while the page loads
        async def handle_response(response):
            nonlocal intercepted
            if api_path in response.url and "symbol=" in response.url:
                try:
                    body = await response.body()
                    data = json.loads(body)
                    # NSE returns {} when blocked; only accept non-empty records
                    if data.get("records", {}).get("data"):
                        intercepted = data
                        logger.debug(f"Playwright intercepted NSE data for {symbol}")
                except Exception:
                    pass

        page.on("response", handle_response)

        # Navigate to the option chain page (real human-facing URL)
        # Use domcontentloaded (not networkidle) to avoid ERR_HTTP2_PROTOCOL_ERROR;
        # NSE's HTTP/2 push streams can cause networkidle to throw — we still get
        # the Akamai cookies we need even if the event fires early.
        try:
            await page.goto(
                "https://www.nseindia.com/option-chain",
                wait_until="domcontentloaded",
                timeout=30_000,
            )
        except Exception as nav_err:
            logger.debug(
                f"Navigation warning for {symbol} (cookies may still be set): {nav_err}"
            )

        # Wait a moment for the page JS to trigger the API call
        await asyncio.sleep(3)

        # If the page didn't auto-trigger our symbol, make the API call directly
        # (the real browser already has valid Akamai cookies from the page load)
        if intercepted is None:
            try:
                resp = await page.evaluate(f"""
                  async () => {{
                    const r = await fetch('{api_url}', {{
                      credentials: 'include',
                      headers: {{ 'X-Requested-With': 'XMLHttpRequest' }}
                    }});
                    return r.json();
                  }}
                """)
                if isinstance(resp, dict) and resp.get("records", {}).get("data"):
                    intercepted = resp
                    logger.debug(f"Playwright eval fetched NSE data for {symbol}")
            except Exception as e:
                logger.debug(f"Playwright eval failed for {symbol}: {e}")

        return intercepted

    except Exception as e:
        logger.warning(f"Playwright fetch error for {symbol}: {e}")
        return None
    finally:
        if page:
            try:
                await page.close()
            except Exception:
                pass


# ── Public refresh entry point ────────────────────────────────────────────────

async def refresh_all(symbols: list = None) -> None:
    """
    Fetch fresh NSE option chain data for all *symbols* and update the cache.
    Called by the background loop in app.py every 150 seconds.
    """
    if not _available:
        return

    global _browser
    if _browser is None:
        await _launch_browser()
    if _browser is None:
        return   # browser failed to launch

    targets = [s.upper() for s in (symbols or WARM_SYMBOLS)]

    for symbol in targets:
        try:
            raw = await _fetch_symbol(symbol)
            if raw:
                _cache[symbol] = (raw, time.time())
                logger.info(f"Playwright: cached fresh NSE data for {symbol}")
            else:
                logger.debug(f"Playwright: no data returned for {symbol} (NSE may be closed)")
        except Exception as e:
            logger.warning(f"Playwright: error refreshing {symbol}: {e}")
            # If browser died, try to re-launch before next symbol
            if _browser is None or not _browser.is_connected():
                await _launch_browser()
                if _browser is None:
                    break   # browser won't recover; stop this cycle


async def shutdown() -> None:
    """Cleanly shut down Playwright browser on app exit."""
    global _browser, _playwright_obj
    try:
        if _browser:
            await _browser.close()
        if _playwright_obj:
            await _playwright_obj.stop()
    except Exception:
        pass
    _browser = None
    _playwright_obj = None
