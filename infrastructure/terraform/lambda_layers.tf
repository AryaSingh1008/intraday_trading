# ─────────────────────────────────────────────────────────────────────────────
# Lambda Layers
# Run infrastructure/build_layers.sh FIRST to generate the zip files,
# then set lambda_layers_built = true in terraform.tfvars
# ─────────────────────────────────────────────────────────────────────────────

# Layer 1: NLP stack — vaderSentiment, feedparser, requests, pytz, bs4
# Used by: trading-news-sentiment, trading-bedrock-sentiment-tool
resource "aws_lambda_layer_version" "nlp" {
  count = var.lambda_layers_built ? 1 : 0

  filename            = "${local.layers_dir}/trading-nlp-layer.zip"
  layer_name          = "${local.prefix}-nlp-layer"
  description         = "VADER sentiment, feedparser, requests, pytz, beautifulsoup4"
  compatible_runtimes = ["python3.12"]
  source_code_hash    = filebase64sha256("${local.layers_dir}/trading-nlp-layer.zip")
}

# Layer 2: Export stack — openpyxl, pytz
# Used by: trading-excel-export
resource "aws_lambda_layer_version" "export" {
  count = var.lambda_layers_built ? 1 : 0

  filename            = "${local.layers_dir}/trading-export-layer.zip"
  layer_name          = "${local.prefix}-export-layer"
  description         = "openpyxl, pytz for Excel report generation"
  compatible_runtimes = ["python3.12"]
  source_code_hash    = filebase64sha256("${local.layers_dir}/trading-export-layer.zip")
}

# Layer 3: Heavy data-science stack — pandas, numpy, scipy, ta, yfinance, curl_cffi
# Used by: stocks-signal, options-analysis, options-refresh, bedrock-technical-tool, bedrock-options-tool
resource "aws_lambda_layer_version" "heavy" {
  count = var.lambda_layers_built ? 1 : 0

  filename            = "${local.layers_dir}/trading-heavy-layer.zip"
  layer_name          = "${local.prefix}-heavy-layer"
  description         = "pandas, numpy, scipy, ta, yfinance, curl_cffi, httpx"
  compatible_runtimes = ["python3.12"]
  source_code_hash    = filebase64sha256("${local.layers_dir}/trading-heavy-layer.zip")
}

# Layer 4: Backend Python source — backend/ package + shared/dynamo_cache.py
# Used by ALL 12 Lambda functions so they can do:
#   from backend.data.options_fetcher import OptionsFetcher
#   import dynamo_cache
# Lambda auto-adds /opt/python to sys.path, making layer contents importable.
resource "aws_lambda_layer_version" "backend" {
  count = var.lambda_layers_built ? 1 : 0

  filename            = "${local.layers_dir}/trading-backend-layer.zip"
  layer_name          = "${local.prefix}-backend-layer"
  description         = "backend/ Python source tree + shared/dynamo_cache.py"
  compatible_runtimes = ["python3.12"]
  source_code_hash    = filebase64sha256("${local.layers_dir}/trading-backend-layer.zip")
}

# Convenience locals to get the layer ARN (or null if not built yet)
locals {
  nlp_layer_arn     = var.lambda_layers_built ? aws_lambda_layer_version.nlp[0].arn     : null
  export_layer_arn  = var.lambda_layers_built ? aws_lambda_layer_version.export[0].arn  : null
  heavy_layer_arn   = var.lambda_layers_built ? aws_lambda_layer_version.heavy[0].arn   : null
  backend_layer_arn = var.lambda_layers_built ? aws_lambda_layer_version.backend[0].arn : null
}
