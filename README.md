# 📈 AI-Powered Intraday Trading Assistant

**Real-time NSE/BSE stock analysis with institutional-grade AI signals.**

A fully serverless cloud platform combining technical analysis, news sentiment, and AI-powered recommendations. Deployed on AWS with 100% uptime, zero infrastructure overhead, and pay-as-you-go pricing (~$2–5/month).

> ⚠️ **Disclaimer:** This tool is for **educational purposes only**.
> Trading involves risk and you may lose money. Always consult a financial advisor before investing real money.

---

## 🎯 Key Features

✅ **43 NIFTY 50 Stocks** — Real-time BUY/SELL/HOLD signals (refreshed every 5 min)
✅ **AI Chat Interface** — Ask in plain English, get institutional analysis
✅ **Portfolio Tracker** — Track holdings with live P&L (day + total gain)
✅ **Wishlist/Watchlist** — Bookmark stocks, persisted across sessions
✅ **Market News** — Real-time sentiment (bullish/bearish labels)
✅ **Excel Export** — Download full analysis for all 43 stocks
✅ **Zero Server Costs** — 100% serverless (scales to $0 when market closed)
✅ **100% Free Data** — yfinance, NSE, Google News RSS (no paid APIs)

---

## 🏗️ Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                    AWS SERVERLESS STACK                        │
└────────────────────────────────────────────────────────────────┘

  👤 Browser (Chrome/Mobile)
         │
         ↓ HTTPS
  ┌──────────────────┐
  │ CloudFront CDN   │  (Singapore PoP, HTTP/2 + HTTP/3)
  └────┬──────┬──────┘
       │      │
  Static │     │ API calls
  files  │     │ /api/*
    ↓    │     ↓
  ┌────┐ │  ┌──────────────────┐
  │ S3 │ │  │ API Gateway      │
  │SPA │ │  │ (15 routes)      │
  └────┘ │  └────────┬─────────┘
         │           │
         │           ↓
         │      ┌─────────────┐
         │      │13 Lambdas:  │
         │      │• stocks     │
         │      │• options    │
         │      │• news       │
         │      │• portfolio  │
         │      │• bedrock    │
         │      │  (AI chat)  │
         │      └──┬──┬──┬────┘
         │         │  │  │
  ┌──────┼─────────┘  │  │
  │      │            │  │
  ↓      ↓            ↓  ↓
[DynamoDB] [Bedrock] [yfinance] [RSS feeds]
- cache      Claude    prices      6 sources
- wishlist   3.5 H     NSE opts    sentiment
- portfolio  Aiken
- iv-hist.
```

---

## 🛠️ Tech Stack

| Layer | Technology | Service |
|-------|-----------|---------|
| **Frontend** | HTML5 + Bootstrap 5 + Chart.js | S3 + CloudFront |
| **Backend** | 13 Lambda functions (Python) | AWS Lambda |
| **Database** | NoSQL, serverless, auto-scale | DynamoDB |
| **AI/Chat** | Claude 3.5 Haiku (tool-use) | AWS Bedrock |
| **API** | HTTP v2, 15 routes | API Gateway |
| **Data Sources** | yfinance, NSE, 6 RSS feeds | Free (no APIs) |
| **IaC** | 10+ Terraform modules | Terraform |
| **Monitoring** | Real-time logs | CloudWatch |

---

## 📊 Signal Algorithm

**10 Technical Indicators:**
```
RSI (±20) | MACD (±15) | Bollinger (±15) | EMA (±15) | RSI Div (±12)
SMA (±10) | Volume (±10) | ADX (±8) | Stochastic (±8)
```

**Sentiment Analysis from 6 RSS feeds:**
- VADER NLP + finance domain lexicon
- Recency weighting (fresh news > old)
- Score: -50 (bearish) to +50 (bullish)

**Final Score (Adaptive Weighting):**
```
Score = Technical × (75%|65%|55%) + Sentiment × (25%|35%|45%)

Thresholds:
  > 70   → STRONG BUY   🟢🟢
 55–70   → BUY          🟢
 40–55   → HOLD         🟡
 25–40   → SELL         🔴
  < 25   → STRONG SELL  🔴🔴
```

---

## 📁 Project Structure

```
intraday_trading/
├── README.md
├── requirements.txt
├── TradingPlatform_Presentation.pptx   ← 18-slide office deck

├── backend/                            ← Agents (used in Lambda + local)
│   ├── agents/
│   │   ├── technical_agent.py          ← 10 indicators
│   │   ├── sentiment_agent.py          ← VADER + RSS
│   │   ├── signal_agent.py             ← Orchestrator
│   │   └── options_agent.py            ← NSE analysis
│   ├── data/
│   │   ├── stock_fetcher.py            ← yfinance
│   │   ├── options_fetcher.py          ← NSE chain
│   │   └── playwright_fetcher.py       ← Browser
│   ├── utils/
│   │   ├── excel_exporter.py
│   │   ├── greeks.py
│   │   ├── iv_history_store.py
│   │   └── wishlist_store.py
│   └── app.py                          ← FastAPI (local dev)

├── frontend/                           ← SPA (S3 + CloudFront)
│   ├── index.html                      ← 4 tabs
│   ├── css/style.css
│   └── js/app.js

├── lambdas/                            ← AWS Lambda handlers
│   ├── trading_stocks_signal/          ← Main engine
│   ├── trading_options_analysis/
│   ├── trading_news_sentiment/
│   ├── trading_wishlist/
│   ├── trading_portfolio/              ← NEW: Holdings tracker
│   ├── trading_market_status/
│   ├── trading_excel_export/
│   ├── trading_cache_clear/
│   ├── trading_bedrock_chat/           ← AI chat
│   ├── trading_bedrock_technical_tool/
│   ├── trading_bedrock_sentiment_tool/
│   └── trading_bedrock_options_tool/

└── infrastructure/                     ← Terraform IaC
    ├── terraform/
    │   ├── api_gateway.tf
    │   ├── bedrock.tf
    │   ├── cloudfront.tf
    │   ├── dynamodb.tf
    │   ├── eventbridge.tf
    │   ├── iam.tf
    │   ├── lambda_functions.tf
    │   ├── lambda_layers.tf
    │   ├── s3.tf
    │   ├── terraform.tfvars            ← AWS account ID, region
    │   ├── terraform.lock.hcl
    │   └── variables.tf
    └── layers/
        ├── trading-backend-layer.zip
        ├── trading-heavy-layer.zip     ← pandas, numpy, ta
        ├── trading-nlp-layer.zip       ← VADER, feedparser
        └── trading-export-layer.zip    ← openpyxl
```

---

## 🚀 Deployment

**Deploy to AWS:**
```bash
cd infrastructure/terraform
terraform init
terraform apply
```

**Cost:** $2–5/month @ moderate usage
- Lambda: 1M calls/month FREE
- DynamoDB: 25 RCU/WCU FREE
- CloudFront: 1 TB/month FREE
- S3: 5 GB FREE
- API Gateway: 1M calls/month FREE
- Bedrock: Pay per token

---

## 🔒 Security

✅ CloudFront-only entry point (S3 private)
✅ IAM roles with least-privilege
✅ DynamoDB: Lambda-only access
✅ Pre-signed URLs (1-hour expiry)
✅ No hardcoded credentials
✅ Terraform state encrypted

---

## 📊 Key Functions

**SignalAgent.analyze()** — Master orchestrator calling TechnicalAgent + SentimentAgent in parallel
**TechnicalAgent.analyze()** — Scores 10 indicators, returns 0–100
**SentimentAgent.get_sentiment_score()** — VADER + finance lexicon on 6 RSS feeds
**_detect_intent()** — Intent classifier with NSE aliases expansion (icici → ICICIBANK)
**renderModalChart()** — 15-min intraday chart (Chart.js)
**loadPortfolio()** — Fetch holdings, calculate live P&L

---

## 🔧 Local Development

```bash
pip install -r requirements.txt
python run.py
# Opens http://localhost:8000
```

---

## 📞 Support

For issues, check:
1. CloudWatch Lambda logs
2. API Gateway metrics
3. DynamoDB on-demand billing
4. Bedrock token usage

---

*Built with AWS, Python, AI, and ❤️ for smarter, safer investing.*
