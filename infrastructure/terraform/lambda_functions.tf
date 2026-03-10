# ─────────────────────────────────────────────────────────────────────────────
# Lambda source packaging — archive_file zips each handler directory
# ─────────────────────────────────────────────────────────────────────────────
data "archive_file" "stocks_signal" {
  type        = "zip"
  source_dir  = "${local.lambdas_dir}/trading_stocks_signal"
  output_path = "${local.layers_dir}/zips/trading_stocks_signal.zip"
  excludes    = ["__pycache__", "*.pyc", ".DS_Store"]
}

data "archive_file" "options_analysis" {
  type        = "zip"
  source_dir  = "${local.lambdas_dir}/trading_options_analysis"
  output_path = "${local.layers_dir}/zips/trading_options_analysis.zip"
  excludes    = ["__pycache__", "*.pyc", ".DS_Store"]
}

data "archive_file" "options_refresh" {
  type        = "zip"
  source_dir  = "${local.lambdas_dir}/trading_options_refresh"
  output_path = "${local.layers_dir}/zips/trading_options_refresh.zip"
  excludes    = ["__pycache__", "*.pyc", ".DS_Store"]
}

data "archive_file" "news_sentiment" {
  type        = "zip"
  source_dir  = "${local.lambdas_dir}/trading_news_sentiment"
  output_path = "${local.layers_dir}/zips/trading_news_sentiment.zip"
  excludes    = ["__pycache__", "*.pyc", ".DS_Store"]
}

data "archive_file" "wishlist" {
  type        = "zip"
  source_dir  = "${local.lambdas_dir}/trading_wishlist"
  output_path = "${local.layers_dir}/zips/trading_wishlist.zip"
  excludes    = ["__pycache__", "*.pyc", ".DS_Store"]
}

data "archive_file" "market_status" {
  type        = "zip"
  source_dir  = "${local.lambdas_dir}/trading_market_status"
  output_path = "${local.layers_dir}/zips/trading_market_status.zip"
  excludes    = ["__pycache__", "*.pyc", ".DS_Store"]
}

data "archive_file" "excel_export" {
  type        = "zip"
  source_dir  = "${local.lambdas_dir}/trading_excel_export"
  output_path = "${local.layers_dir}/zips/trading_excel_export.zip"
  excludes    = ["__pycache__", "*.pyc", ".DS_Store"]
}

data "archive_file" "cache_clear" {
  type        = "zip"
  source_dir  = "${local.lambdas_dir}/trading_cache_clear"
  output_path = "${local.layers_dir}/zips/trading_cache_clear.zip"
  excludes    = ["__pycache__", "*.pyc", ".DS_Store"]
}

data "archive_file" "bedrock_chat" {
  type        = "zip"
  source_dir  = "${local.lambdas_dir}/trading_bedrock_chat"
  output_path = "${local.layers_dir}/zips/trading_bedrock_chat.zip"
  excludes    = ["__pycache__", "*.pyc", ".DS_Store"]
}

data "archive_file" "bedrock_technical_tool" {
  type        = "zip"
  source_dir  = "${local.lambdas_dir}/trading_bedrock_technical_tool"
  output_path = "${local.layers_dir}/zips/trading_bedrock_technical_tool.zip"
  excludes    = ["__pycache__", "*.pyc", ".DS_Store"]
}

data "archive_file" "bedrock_sentiment_tool" {
  type        = "zip"
  source_dir  = "${local.lambdas_dir}/trading_bedrock_sentiment_tool"
  output_path = "${local.layers_dir}/zips/trading_bedrock_sentiment_tool.zip"
  excludes    = ["__pycache__", "*.pyc", ".DS_Store"]
}

data "archive_file" "bedrock_options_tool" {
  type        = "zip"
  source_dir  = "${local.lambdas_dir}/trading_bedrock_options_tool"
  output_path = "${local.layers_dir}/zips/trading_bedrock_options_tool.zip"
  excludes    = ["__pycache__", "*.pyc", ".DS_Store"]
}

# ─────────────────────────────────────────────────────────────────────────────
# HEAVY FUNCTIONS — need the heavy layer (pandas+scipy+ta+yfinance)
# ─────────────────────────────────────────────────────────────────────────────

resource "aws_lambda_function" "stocks_signal" {
  function_name    = local.lambda_names.stocks_signal
  role             = aws_iam_role.lambda_exec.arn
  runtime          = "python3.12"
  handler          = "handler.handler"
  filename         = data.archive_file.stocks_signal.output_path
  source_code_hash = data.archive_file.stocks_signal.output_base64sha256
  timeout          = 60
  memory_size      = 1024

  layers = compact([local.heavy_layer_arn, local.backend_layer_arn])

  environment {
    variables = merge(local.common_env, {
      FUNCTION_TYPE = "stocks_signal"
    })
  }

  depends_on = [aws_cloudwatch_log_group.lambda_logs]
}

resource "aws_lambda_function" "options_analysis" {
  function_name    = local.lambda_names.options_analysis
  role             = aws_iam_role.lambda_exec.arn
  runtime          = "python3.12"
  handler          = "handler.handler"
  filename         = data.archive_file.options_analysis.output_path
  source_code_hash = data.archive_file.options_analysis.output_base64sha256
  timeout          = 30
  memory_size      = 512

  layers = compact([local.heavy_layer_arn, local.backend_layer_arn])

  environment {
    variables = merge(local.common_env, {
      FUNCTION_TYPE = "options_analysis"
    })
  }

  depends_on = [aws_cloudwatch_log_group.lambda_logs]
}

resource "aws_lambda_function" "options_refresh" {
  function_name    = local.lambda_names.options_refresh
  role             = aws_iam_role.lambda_exec.arn
  runtime          = "python3.12"
  handler          = "handler.handler"
  filename         = data.archive_file.options_refresh.output_path
  source_code_hash = data.archive_file.options_refresh.output_base64sha256
  timeout          = 120
  memory_size      = 512

  layers = compact([local.heavy_layer_arn, local.backend_layer_arn])

  environment {
    variables = merge(local.common_env, {
      FUNCTION_TYPE = "options_refresh"
    })
  }

  depends_on = [aws_cloudwatch_log_group.lambda_logs]
}

resource "aws_lambda_function" "bedrock_technical_tool" {
  function_name    = local.lambda_names.bedrock_technical_tool
  role             = aws_iam_role.lambda_exec.arn
  runtime          = "python3.12"
  handler          = "handler.handler"
  filename         = data.archive_file.bedrock_technical_tool.output_path
  source_code_hash = data.archive_file.bedrock_technical_tool.output_base64sha256
  timeout          = 30
  memory_size      = 512

  layers = compact([local.heavy_layer_arn, local.backend_layer_arn])

  environment {
    variables = merge(local.common_env, {
      FUNCTION_TYPE = "bedrock_technical_tool"
    })
  }

  depends_on = [aws_cloudwatch_log_group.lambda_logs]
}

resource "aws_lambda_function" "bedrock_options_tool" {
  function_name    = local.lambda_names.bedrock_options_tool
  role             = aws_iam_role.lambda_exec.arn
  runtime          = "python3.12"
  handler          = "handler.handler"
  filename         = data.archive_file.bedrock_options_tool.output_path
  source_code_hash = data.archive_file.bedrock_options_tool.output_base64sha256
  timeout          = 30
  memory_size      = 512

  layers = compact([local.heavy_layer_arn, local.backend_layer_arn])

  environment {
    variables = merge(local.common_env, {
      FUNCTION_TYPE = "bedrock_options_tool"
    })
  }

  depends_on = [aws_cloudwatch_log_group.lambda_logs]
}

# ─────────────────────────────────────────────────────────────────────────────
# LIGHT FUNCTIONS — NLP layer (feedparser, vaderSentiment, requests, pytz)
# ─────────────────────────────────────────────────────────────────────────────

resource "aws_lambda_function" "news_sentiment" {
  function_name    = local.lambda_names.news_sentiment
  role             = aws_iam_role.lambda_exec.arn
  runtime          = "python3.12"
  handler          = "handler.handler"
  filename         = data.archive_file.news_sentiment.output_path
  source_code_hash = data.archive_file.news_sentiment.output_base64sha256
  timeout          = 20
  memory_size      = 256

  layers = compact([local.nlp_layer_arn, local.backend_layer_arn])

  environment {
    variables = local.common_env
  }

  depends_on = [aws_cloudwatch_log_group.lambda_logs]
}

resource "aws_lambda_function" "bedrock_sentiment_tool" {
  function_name    = local.lambda_names.bedrock_sentiment_tool
  role             = aws_iam_role.lambda_exec.arn
  runtime          = "python3.12"
  handler          = "handler.handler"
  filename         = data.archive_file.bedrock_sentiment_tool.output_path
  source_code_hash = data.archive_file.bedrock_sentiment_tool.output_base64sha256
  timeout          = 20
  memory_size      = 256

  layers = compact([local.nlp_layer_arn, local.backend_layer_arn])

  environment {
    variables = local.common_env
  }

  depends_on = [aws_cloudwatch_log_group.lambda_logs]
}

resource "aws_lambda_function" "excel_export" {
  function_name    = local.lambda_names.excel_export
  role             = aws_iam_role.lambda_exec.arn
  runtime          = "python3.12"
  handler          = "handler.handler"
  filename         = data.archive_file.excel_export.output_path
  source_code_hash = data.archive_file.excel_export.output_base64sha256
  timeout          = 90
  memory_size      = 256

  layers = compact([local.export_layer_arn, local.backend_layer_arn])

  environment {
    variables = local.common_env
  }

  depends_on = [aws_cloudwatch_log_group.lambda_logs]
}

# ─────────────────────────────────────────────────────────────────────────────
# BOTO3-ONLY FUNCTIONS — no layer needed (boto3 pre-installed in Lambda runtime)
# ─────────────────────────────────────────────────────────────────────────────

resource "aws_lambda_function" "wishlist" {
  function_name    = local.lambda_names.wishlist
  role             = aws_iam_role.lambda_exec.arn
  runtime          = "python3.12"
  handler          = "handler.handler"
  filename         = data.archive_file.wishlist.output_path
  source_code_hash = data.archive_file.wishlist.output_base64sha256
  timeout          = 10
  memory_size      = 128

  layers = compact([local.backend_layer_arn])

  environment {
    variables = local.common_env
  }

  depends_on = [aws_cloudwatch_log_group.lambda_logs]
}

resource "aws_lambda_function" "market_status" {
  function_name    = local.lambda_names.market_status
  role             = aws_iam_role.lambda_exec.arn
  runtime          = "python3.12"
  handler          = "handler.handler"
  filename         = data.archive_file.market_status.output_path
  source_code_hash = data.archive_file.market_status.output_base64sha256
  timeout          = 5
  memory_size      = 128

  layers = compact([local.backend_layer_arn])

  environment {
    variables = local.common_env
  }

  depends_on = [aws_cloudwatch_log_group.lambda_logs]
}

resource "aws_lambda_function" "cache_clear" {
  function_name    = local.lambda_names.cache_clear
  role             = aws_iam_role.lambda_exec.arn
  runtime          = "python3.12"
  handler          = "handler.handler"
  filename         = data.archive_file.cache_clear.output_path
  source_code_hash = data.archive_file.cache_clear.output_base64sha256
  timeout          = 10
  memory_size      = 128

  layers = compact([local.backend_layer_arn])

  environment {
    variables = local.common_env
  }

  depends_on = [aws_cloudwatch_log_group.lambda_logs]
}

resource "aws_lambda_function" "bedrock_chat" {
  function_name    = local.lambda_names.bedrock_chat
  role             = aws_iam_role.lambda_exec.arn
  runtime          = "python3.12"
  handler          = "handler.handler"
  filename         = data.archive_file.bedrock_chat.output_path
  source_code_hash = data.archive_file.bedrock_chat.output_base64sha256
  timeout          = 120
  memory_size      = 256

  layers = compact([local.backend_layer_arn])

  environment {
    variables = merge(local.common_env, {
      BEDROCK_AGENT_ID       = "PLACEHOLDER_REPLACE_AFTER_BEDROCK_DEPLOY"
      BEDROCK_AGENT_ALIAS_ID = "TSTALIASID"
    })
  }

  depends_on = [aws_cloudwatch_log_group.lambda_logs]
}

# ─────────────────────────────────────────────────────────────────────────────
# Lambda resource-based policies — allow API Gateway to invoke
# ─────────────────────────────────────────────────────────────────────────────
locals {
  api_triggered_lambdas = {
    stocks_signal    = aws_lambda_function.stocks_signal.function_name
    options_analysis = aws_lambda_function.options_analysis.function_name
    news_sentiment   = aws_lambda_function.news_sentiment.function_name
    wishlist         = aws_lambda_function.wishlist.function_name
    market_status    = aws_lambda_function.market_status.function_name
    excel_export     = aws_lambda_function.excel_export.function_name
    cache_clear      = aws_lambda_function.cache_clear.function_name
    bedrock_chat     = aws_lambda_function.bedrock_chat.function_name
  }
}

resource "aws_lambda_permission" "api_gateway" {
  for_each = local.api_triggered_lambdas

  statement_id  = "AllowAPIGatewayInvoke-${each.key}"
  action        = "lambda:InvokeFunction"
  function_name = each.value
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*/*"
}

# Allow Bedrock to invoke the action-group tool lambdas
resource "aws_lambda_permission" "bedrock_technical" {
  statement_id  = "AllowBedrockInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.bedrock_technical_tool.function_name
  principal     = "bedrock.amazonaws.com"
  source_arn    = "arn:aws:bedrock:${local.region}:${local.account_id}:agent/*"
}

resource "aws_lambda_permission" "bedrock_sentiment" {
  statement_id  = "AllowBedrockInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.bedrock_sentiment_tool.function_name
  principal     = "bedrock.amazonaws.com"
  source_arn    = "arn:aws:bedrock:${local.region}:${local.account_id}:agent/*"
}

resource "aws_lambda_permission" "bedrock_options" {
  statement_id  = "AllowBedrockInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.bedrock_options_tool.function_name
  principal     = "bedrock.amazonaws.com"
  source_arn    = "arn:aws:bedrock:${local.region}:${local.account_id}:agent/*"
}
