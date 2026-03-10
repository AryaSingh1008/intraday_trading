locals {
  prefix      = var.project_name
  account_id  = var.aws_account_id
  region      = var.aws_region

  # Paths (relative to terraform/ directory)
  project_root   = "${path.module}/../.."
  lambdas_dir    = "${path.module}/../../lambdas"
  layers_dir     = "${path.module}/../layers"

  # DynamoDB table names
  cache_table_name      = "${local.prefix}-cache"
  wishlist_table_name   = "${local.prefix}-wishlist"
  iv_history_table_name = "${local.prefix}-iv-history"

  # S3 bucket names (must be globally unique — account ID suffix ensures uniqueness)
  frontend_bucket_name = "${local.prefix}-frontend-${local.account_id}"
  exports_bucket_name  = "${local.prefix}-exports-${local.account_id}"

  # Lambda function names
  lambda_names = {
    stocks_signal          = "${local.prefix}-stocks-signal"
    options_analysis       = "${local.prefix}-options-analysis"
    options_refresh        = "${local.prefix}-options-refresh"
    news_sentiment         = "${local.prefix}-news-sentiment"
    wishlist               = "${local.prefix}-wishlist"
    market_status          = "${local.prefix}-market-status"
    excel_export           = "${local.prefix}-excel-export"
    cache_clear            = "${local.prefix}-cache-clear"
    bedrock_chat           = "${local.prefix}-bedrock-chat"
    bedrock_technical_tool = "${local.prefix}-bedrock-technical-tool"
    bedrock_sentiment_tool = "${local.prefix}-bedrock-sentiment-tool"
    bedrock_options_tool   = "${local.prefix}-bedrock-options-tool"
  }

  # Common Lambda environment variables (injected into all functions)
  common_env = {
    CACHE_TABLE_NAME      = local.cache_table_name
    WISHLIST_TABLE_NAME   = local.wishlist_table_name
    IV_HISTORY_TABLE_NAME = local.iv_history_table_name
    EXPORTS_BUCKET        = local.exports_bucket_name
    AWS_ACCOUNT_ID_VALUE  = local.account_id
    PROJECT_REGION        = local.region
  }
}
