"""
Lambda handler: GET /api/export
Generates Excel report, uploads to S3 exports bucket, returns pre-signed URL.
Lambda can't stream FileResponse, so we use S3 pre-signed URLs instead.
"""
import json
import os
import asyncio
import logging
import tempfile
from datetime import datetime

import boto3

from backend.data.stock_fetcher import StockFetcher
from backend.agents.signal_agent import SignalAgent
from backend.utils.excel_exporter import ExcelExporter

logger = logging.getLogger(__name__)

EXPORTS_BUCKET = os.environ.get("EXPORTS_BUCKET", "trading-exports-REDACTED")
URL_EXPIRY_SEC = 3600   # 1 hour pre-signed URL

_exporter = None
_s3       = None
_fetcher  = None
_agent    = None

INDIAN_STOCKS = {
    "RELIANCE.NS": "Reliance Industries", "TCS.NS": "Tata Consultancy Services",
    "INFY.NS": "Infosys", "HDFCBANK.NS": "HDFC Bank", "ICICIBANK.NS": "ICICI Bank",
    "WIPRO.NS": "Wipro", "TATAMOTORS.NS": "Tata Motors", "SBIN.NS": "State Bank of India",
    "AXISBANK.NS": "Axis Bank", "KOTAKBANK.NS": "Kotak Mahindra Bank",
    "BAJFINANCE.NS": "Bajaj Finance", "SUNPHARMA.NS": "Sun Pharmaceutical",
    "MARUTI.NS": "Maruti Suzuki", "LT.NS": "Larsen & Toubro", "ONGC.NS": "ONGC",
}


def _init():
    global _exporter, _s3, _fetcher, _agent
    if _exporter is None:
        _exporter = ExcelExporter()
    if _s3 is None:
        _s3 = boto3.client("s3")
    if _fetcher is None:
        _fetcher = StockFetcher()
    if _agent is None:
        _agent = SignalAgent()


async def _fetch_live_stocks() -> list:
    """Fetch and analyse all stocks with live data."""
    symbols = list(INDIAN_STOCKS.keys())
    batch_data = await _fetcher.get_batch_stock_data(symbols)

    tasks = []
    errors = []
    for symbol, name in INDIAN_STOCKS.items():
        stock_data = batch_data.get(symbol)
        if not stock_data:
            errors.append({"symbol": symbol, "name": name, "error": "No data available"})
            continue
        tasks.append(_agent.analyze(symbol, name, stock_data))

    results = list(await asyncio.gather(*tasks))
    return results + errors


def handler(event, context):
    _init()

    stocks = asyncio.run(_fetch_live_stocks())
    if not stocks:
        return _json({"error": "Could not fetch live stock data."}, 503)

    try:
        # Generate Excel in a Lambda-writable temp directory
        with tempfile.TemporaryDirectory() as tmpdir:
            # Temporarily override exporter's output to use /tmp
            excel_path = asyncio.run(_exporter.export(stocks, market="IN"))

            # Upload to S3
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            s3_key    = f"exports/trading_signals_{timestamp}.xlsx"

            _s3.upload_file(
                excel_path,
                EXPORTS_BUCKET,
                s3_key,
                ExtraArgs={"ContentType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"},
            )

            # Clean up local temp file
            try:
                os.remove(excel_path)
            except Exception:
                pass

        # Generate pre-signed URL (valid for 1 hour)
        url = _s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": EXPORTS_BUCKET, "Key": s3_key},
            ExpiresIn=URL_EXPIRY_SEC,
        )

        return _json({
            "download_url": url,
            "filename":     f"trading_signals_{timestamp}.xlsx",
            "expires_in":   URL_EXPIRY_SEC,
            "stock_count":  len(stocks),
        })

    except Exception as exc:
        logger.error(f"excel_export: {exc}")
        return _json({"error": f"Export failed: {exc}"}, 500)


def _json(data, status: int = 200):
    return {
        "statusCode": status,
        "headers": {
            "Content-Type":                "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(data, default=str),
    }
