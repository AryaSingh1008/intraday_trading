# ─────────────────────────────────────────────────────────────────────────────
# S3: Frontend Bucket (serves static SPA via CloudFront OAC)
# ─────────────────────────────────────────────────────────────────────────────
resource "aws_s3_bucket" "frontend" {
  bucket        = local.frontend_bucket_name
  force_destroy = false
}

resource "aws_s3_bucket_public_access_block" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "frontend" {
  bucket = aws_s3_bucket.frontend.id
  versioning_configuration {
    status = "Enabled"
  }
}

# Allow CloudFront OAC to read from this bucket
data "aws_iam_policy_document" "frontend_bucket_policy" {
  statement {
    sid    = "AllowCloudFrontOAC"
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["cloudfront.amazonaws.com"]
    }
    actions   = ["s3:GetObject"]
    resources = ["${aws_s3_bucket.frontend.arn}/*"]
    condition {
      test     = "StringEquals"
      variable = "AWS:SourceArn"
      values   = [aws_cloudfront_distribution.main.arn]
    }
  }
}

resource "aws_s3_bucket_policy" "frontend" {
  bucket = aws_s3_bucket.frontend.id
  policy = data.aws_iam_policy_document.frontend_bucket_policy.json

  # Must wait for public access block to be applied first
  depends_on = [aws_s3_bucket_public_access_block.frontend]
}

# Upload frontend static files
resource "aws_s3_object" "frontend_html" {
  bucket        = aws_s3_bucket.frontend.id
  key           = "index.html"
  source        = "${local.project_root}/frontend/index.html"
  content_type  = "text/html"
  etag          = filemd5("${local.project_root}/frontend/index.html")
  cache_control = "no-cache, no-store, must-revalidate"
}

resource "aws_s3_object" "frontend_css" {
  bucket        = aws_s3_bucket.frontend.id
  key           = "css/style.css"
  source        = "${local.project_root}/frontend/css/style.css"
  content_type  = "text/css"
  etag          = filemd5("${local.project_root}/frontend/css/style.css")
  cache_control = "public, max-age=31536000, immutable"
}

resource "aws_s3_object" "frontend_js" {
  bucket        = aws_s3_bucket.frontend.id
  key           = "js/app.js"
  source        = "${local.project_root}/frontend/js/app.js"
  content_type  = "application/javascript"
  etag          = filemd5("${local.project_root}/frontend/js/app.js")
  cache_control = "public, max-age=31536000, immutable"
}

# ─────────────────────────────────────────────────────────────────────────────
# S3: Exports Bucket (temporary Excel report storage, pre-signed URLs)
# ─────────────────────────────────────────────────────────────────────────────
resource "aws_s3_bucket" "exports" {
  bucket        = local.exports_bucket_name
  force_destroy = true   # Reports are temporary
}

resource "aws_s3_bucket_public_access_block" "exports" {
  bucket = aws_s3_bucket.exports.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Auto-delete exported Excel files after 1 day
resource "aws_s3_bucket_lifecycle_configuration" "exports" {
  bucket = aws_s3_bucket.exports.id

  rule {
    id     = "delete-old-exports"
    status = "Enabled"
    filter {}   # applies to all objects in the bucket
    expiration {
      days = 1
    }
  }
}
