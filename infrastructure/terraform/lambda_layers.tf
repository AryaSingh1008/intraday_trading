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

# Layer 3: Heavy data-science stack — pandas, numpy, ta, yfinance, curl_cffi
# Used by: stocks-signal, options-analysis, options-refresh, bedrock-technical-tool, bedrock-options-tool
# NOTE: Uploaded to S3 because the ZIP (>50 MB) exceeds the Lambda direct-upload limit
#       (PublishLayerVersion API allows max ~67 MB via ZipFile; S3 path allows up to 250 MB).
resource "aws_lambda_layer_version" "heavy" {
  count = var.lambda_layers_built ? 1 : 0

  s3_bucket   = aws_s3_bucket.exports.id
  s3_key      = "layers/trading-heavy-layer.zip"
  layer_name          = "${local.prefix}-heavy-layer"
  description         = "pandas, numpy, ta, yfinance, curl_cffi"
  compatible_runtimes = ["python3.12"]

  depends_on = [aws_s3_object.heavy_layer_zip]
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

# Upload the heavy layer ZIP to S3 so Terraform can reference it via s3_bucket/s3_key.
# This avoids the 67 MB payload limit on the Lambda PublishLayerVersion direct-upload path.
resource "aws_s3_object" "heavy_layer_zip" {
  count  = var.lambda_layers_built ? 1 : 0
  bucket = aws_s3_bucket.exports.id
  key    = "layers/trading-heavy-layer.zip"
  source = "${local.layers_dir}/trading-heavy-layer.zip"
  etag   = filemd5("${local.layers_dir}/trading-heavy-layer.zip")

  # S3 multipart-upload etag format (hash-N) differs from local filemd5(),
  # causing a perpetual diff. Ignore after initial upload; re-upload manually
  # if the layer ZIP content actually changes (rebuild + terraform apply -replace).
  lifecycle {
    ignore_changes = [etag]
  }
}

# Convenience locals to get the layer ARN (or null if not built yet)
locals {
  nlp_layer_arn     = var.lambda_layers_built ? aws_lambda_layer_version.nlp[0].arn     : null
  export_layer_arn  = var.lambda_layers_built ? aws_lambda_layer_version.export[0].arn  : null
  heavy_layer_arn   = var.lambda_layers_built ? aws_lambda_layer_version.heavy[0].arn   : null
  backend_layer_arn = var.lambda_layers_built ? aws_lambda_layer_version.backend[0].arn : null
}
