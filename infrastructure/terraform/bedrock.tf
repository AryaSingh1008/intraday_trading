# ─────────────────────────────────────────────────────────────────────────────
# AWS Bedrock Agent: TradingAdvisorAgent
# Requires AWS provider >= 5.40 and Bedrock Claude Haiku model access enabled
# in the AWS console BEFORE running terraform apply.
#
# HOW TO ENABLE MODEL ACCESS:
#   1. Go to AWS Console → Bedrock → Model access (us-east-1)
#   2. Click "Manage model access"
#   3. Enable: Anthropic → Claude 3 Haiku
#   4. Click "Save changes" (takes < 2 minutes to activate)
# ─────────────────────────────────────────────────────────────────────────────

resource "aws_bedrockagent_agent" "trading_advisor" {
  agent_name              = "${local.prefix}-TradingAdvisorAgent"
  agent_resource_role_arn = aws_iam_role.bedrock_agent.arn
  foundation_model        = var.bedrock_model_id
  idle_session_ttl_in_seconds = 600   # 10-minute session timeout

  # Instruction loaded from external file — edit prompts/trading_guru_agent.txt to update.
  # Using file() keeps prompt changes out of Terraform diffs and lets domain experts
  # iterate on wording without touching infrastructure code.
  instruction = file("${path.module}/../../prompts/trading_guru_agent.txt")

  description = "TradingGuru — friendly AI for Indian stock markets: signals, targets, news, education, comparisons"

  depends_on = [
    aws_iam_role_policy.bedrock_agent_permissions,
    aws_lambda_permission.bedrock_technical,
    aws_lambda_permission.bedrock_sentiment,
    aws_lambda_permission.bedrock_options,
  ]
}

# ─────────────────────────────────────────────────────────────────────────────
# Action Group 1: StockTechnicalAnalysis
# ─────────────────────────────────────────────────────────────────────────────
resource "aws_bedrockagent_agent_action_group" "technical_analysis" {
  agent_id          = aws_bedrockagent_agent.trading_advisor.id
  agent_version     = "DRAFT"
  action_group_name = "StockTechnicalAnalysis"
  prepare_agent     = false   # agent is prepared manually after all action groups are attached
  description       = "Computes RSI, MACD, Bollinger Bands, ADX, Stochastic RSI, EMA crossovers, and ATR for any NSE stock."

  action_group_executor {
    lambda = aws_lambda_function.bedrock_technical_tool.arn
  }

  function_schema {
    member_functions {
      functions {
        name        = "get_technical_analysis"
        description = "Fetches 60-day OHLCV from Yahoo Finance and computes all technical indicators. Returns a score 0-100 and list of plain-English reasons."
        parameters {
          map_block_key = "symbol"
          type          = "string"
          description   = "NSE stock symbol with .NS suffix, e.g. INFY.NS, RELIANCE.NS, TCS.NS, HDFCBANK.NS"
          required      = true
        }
      }
    }
  }
}

# ─────────────────────────────────────────────────────────────────────────────
# Action Group 2: NewsSentimentAnalysis
# ─────────────────────────────────────────────────────────────────────────────
resource "aws_bedrockagent_agent_action_group" "news_sentiment" {
  agent_id          = aws_bedrockagent_agent.trading_advisor.id
  agent_version     = "DRAFT"
  action_group_name = "NewsSentimentAnalysis"
  prepare_agent     = false
  description       = "Fetches Indian financial news from Economic Times, Moneycontrol, Business Standard and scores sentiment using VADER."

  action_group_executor {
    lambda = aws_lambda_function.bedrock_sentiment_tool.arn
  }

  function_schema {
    member_functions {
      functions {
        name        = "get_news_sentiment"
        description = "Fetches RSS news feeds and returns VADER sentiment score -50 to +50 and top headlines."
        parameters {
          map_block_key = "symbol"
          type          = "string"
          description   = "Stock symbol without .NS suffix, e.g. INFY, RELIANCE. Use empty string for general market sentiment."
          required      = true
        }
        parameters {
          map_block_key = "company_name"
          type          = "string"
          description   = "Full company name for better news search, e.g. Infosys, Reliance Industries, TCS"
          required      = false
        }
      }
    }
  }
}

# ─────────────────────────────────────────────────────────────────────────────
# Action Group 3: OptionsChainAnalysis
# ─────────────────────────────────────────────────────────────────────────────
resource "aws_bedrockagent_agent_action_group" "options_chain" {
  agent_id          = aws_bedrockagent_agent.trading_advisor.id
  agent_version     = "DRAFT"
  action_group_name = "OptionsChainAnalysis"
  prepare_agent     = false
  description       = "Fetches NSE option chain and returns PCR, IV percentile, max pain strike, and key option Greeks."

  action_group_executor {
    lambda = aws_lambda_function.bedrock_options_tool.arn
  }

  function_schema {
    member_functions {
      functions {
        name        = "get_options_data"
        description = "Returns option chain data for supported Indian instruments with Put-Call Ratio, IV percentile, and max pain."
        parameters {
          map_block_key = "symbol"
          type          = "string"
          description   = "Options symbol. Supported: NIFTY, BANKNIFTY, RELIANCE, TCS, INFY, HDFCBANK, ICICIBANK"
          required      = true
        }
      }
    }
  }
}

# ─────────────────────────────────────────────────────────────────────────────
# Agent Alias — stable production pointer (needed to invoke the agent)
# ─────────────────────────────────────────────────────────────────────────────
resource "aws_bedrockagent_agent_alias" "prod" {
  agent_id         = aws_bedrockagent_agent.trading_advisor.id
  agent_alias_name = "prod"
  description      = "Production alias for TradingAdvisorAgent"

  # Note: alias must be created after at least one PREPARED agent version exists.
  # After apply, manually prepare the agent once in the Bedrock console,
  # then run terraform apply again to update the alias to the prepared version.
}
