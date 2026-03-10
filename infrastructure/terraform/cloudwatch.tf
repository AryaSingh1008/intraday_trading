# ─────────────────────────────────────────────────────────────────────────────
# CloudWatch Log Groups — 7 day retention (keeps within free tier 5GB/month)
# ─────────────────────────────────────────────────────────────────────────────
resource "aws_cloudwatch_log_group" "lambda_logs" {
  for_each          = local.lambda_names
  name              = "/aws/lambda/${each.value}"
  retention_in_days = 7
}

resource "aws_cloudwatch_log_group" "api_gateway" {
  name              = "/aws/api-gw/${local.prefix}-api"
  retention_in_days = 7
}
