# ─────────────────────────────────────────────────────────────────────────────
# API Gateway HTTP API (v2) — cheaper and lower latency than REST API
# ─────────────────────────────────────────────────────────────────────────────
resource "aws_apigatewayv2_api" "main" {
  name          = "${local.prefix}-api"
  protocol_type = "HTTP"
  description   = "AI Trading Assistant API"

  cors_configuration {
    allow_origins  = ["*"]   # Lock down to CloudFront domain after first deploy
    allow_methods  = ["GET", "POST", "DELETE", "OPTIONS"]
    allow_headers  = ["Content-Type", "Authorization", "X-Requested-With"]
    expose_headers = ["Content-Disposition"]
    max_age        = 300
  }
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.main.id
  name        = "$default"
  auto_deploy = true

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gateway.arn
    format = jsonencode({
      requestId     = "$context.requestId"
      sourceIp      = "$context.identity.sourceIp"
      requestTime   = "$context.requestTime"
      httpMethod    = "$context.httpMethod"
      routeKey      = "$context.routeKey"
      status        = "$context.status"
      responseLength = "$context.responseLength"
      integrationError = "$context.integrationErrorMessage"
    })
  }
}

# ─────────────────────────────────────────────────────────────────────────────
# Lambda Integrations (one per function)
# ─────────────────────────────────────────────────────────────────────────────
resource "aws_apigatewayv2_integration" "stocks_signal" {
  api_id                 = aws_apigatewayv2_api.main.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.stocks_signal.invoke_arn
  payload_format_version = "2.0"
  timeout_milliseconds   = 60000
}

resource "aws_apigatewayv2_integration" "options_analysis" {
  api_id                 = aws_apigatewayv2_api.main.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.options_analysis.invoke_arn
  payload_format_version = "2.0"
  timeout_milliseconds   = 30000
}

resource "aws_apigatewayv2_integration" "news_sentiment" {
  api_id                 = aws_apigatewayv2_api.main.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.news_sentiment.invoke_arn
  payload_format_version = "2.0"
  timeout_milliseconds   = 20000
}

resource "aws_apigatewayv2_integration" "wishlist" {
  api_id                 = aws_apigatewayv2_api.main.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.wishlist.invoke_arn
  payload_format_version = "2.0"
  timeout_milliseconds   = 10000
}

resource "aws_apigatewayv2_integration" "market_status" {
  api_id                 = aws_apigatewayv2_api.main.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.market_status.invoke_arn
  payload_format_version = "2.0"
  timeout_milliseconds   = 5000
}

resource "aws_apigatewayv2_integration" "excel_export" {
  api_id                 = aws_apigatewayv2_api.main.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.excel_export.invoke_arn
  payload_format_version = "2.0"
  timeout_milliseconds   = 29000   # API GW HTTP v2 max is 30s; Lambda itself can run longer
}

resource "aws_apigatewayv2_integration" "cache_clear" {
  api_id                 = aws_apigatewayv2_api.main.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.cache_clear.invoke_arn
  payload_format_version = "2.0"
  timeout_milliseconds   = 10000
}

resource "aws_apigatewayv2_integration" "bedrock_chat" {
  api_id                 = aws_apigatewayv2_api.main.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.bedrock_chat.invoke_arn
  payload_format_version = "2.0"
  timeout_milliseconds   = 29000   # API GW HTTP v2 max is 30s; Bedrock streaming handled client-side
}

# ─────────────────────────────────────────────────────────────────────────────
# Routes — mirrors the existing FastAPI endpoints exactly
# ─────────────────────────────────────────────────────────────────────────────
resource "aws_apigatewayv2_route" "get_stocks" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "GET /api/stocks"
  target    = "integrations/${aws_apigatewayv2_integration.stocks_signal.id}"
}

resource "aws_apigatewayv2_route" "get_stock_detail" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "GET /api/stock/{symbol}"
  target    = "integrations/${aws_apigatewayv2_integration.stocks_signal.id}"
}

resource "aws_apigatewayv2_route" "get_stocks_list" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "GET /api/stocks/list"
  target    = "integrations/${aws_apigatewayv2_integration.stocks_signal.id}"
}

resource "aws_apigatewayv2_route" "get_options" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "GET /api/options"
  target    = "integrations/${aws_apigatewayv2_integration.options_analysis.id}"
}

resource "aws_apigatewayv2_route" "get_news" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "GET /api/news"
  target    = "integrations/${aws_apigatewayv2_integration.news_sentiment.id}"
}

resource "aws_apigatewayv2_route" "get_export" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "GET /api/export"
  target    = "integrations/${aws_apigatewayv2_integration.excel_export.id}"
}

resource "aws_apigatewayv2_route" "get_market_status" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "GET /api/market-status"
  target    = "integrations/${aws_apigatewayv2_integration.market_status.id}"
}

resource "aws_apigatewayv2_route" "delete_cache" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "DELETE /api/cache"
  target    = "integrations/${aws_apigatewayv2_integration.cache_clear.id}"
}

resource "aws_apigatewayv2_route" "get_wishlist" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "GET /api/wishlist"
  target    = "integrations/${aws_apigatewayv2_integration.wishlist.id}"
}

resource "aws_apigatewayv2_route" "post_wishlist" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "POST /api/wishlist"
  target    = "integrations/${aws_apigatewayv2_integration.wishlist.id}"
}

resource "aws_apigatewayv2_route" "delete_wishlist" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "DELETE /api/wishlist/{symbol}"
  target    = "integrations/${aws_apigatewayv2_integration.wishlist.id}"
}

resource "aws_apigatewayv2_route" "check_wishlist" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "GET /api/wishlist/check/{symbol}"
  target    = "integrations/${aws_apigatewayv2_integration.wishlist.id}"
}

resource "aws_apigatewayv2_route" "post_chat" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "POST /api/chat"
  target    = "integrations/${aws_apigatewayv2_integration.bedrock_chat.id}"
}
