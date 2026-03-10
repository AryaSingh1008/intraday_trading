# ─────────────────────────────────────────────────────────────────────────────
# CloudFront Origin Access Control (OAC) — replaces legacy OAI
# ─────────────────────────────────────────────────────────────────────────────
resource "aws_cloudfront_origin_access_control" "frontend" {
  name                              = "${local.prefix}-frontend-oac"
  description                       = "OAC for trading frontend S3 bucket"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

# ─────────────────────────────────────────────────────────────────────────────
# CloudFront Distribution
# Two origins: S3 (frontend) + API Gateway (backend)
# ─────────────────────────────────────────────────────────────────────────────
resource "aws_cloudfront_distribution" "main" {
  enabled             = true
  is_ipv6_enabled     = true
  default_root_object = "index.html"
  price_class         = "PriceClass_100"   # US, EU, Asia (covers India via Singapore PoP)
  comment             = "AI Trading Assistant — ${var.environment}"
  http_version        = "http2and3"

  # ── Origin 1: S3 (static SPA) ──────────────────────────────────────────────
  origin {
    origin_id                = "S3Origin"
    domain_name              = aws_s3_bucket.frontend.bucket_regional_domain_name

    origin_access_control_id = aws_cloudfront_origin_access_control.frontend.id
  }

  # ── Origin 2: API Gateway HTTP API ─────────────────────────────────────────
  origin {
    origin_id   = "APIGWOrigin"
    domain_name = "${aws_apigatewayv2_api.main.id}.execute-api.${local.region}.amazonaws.com"

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "https-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  # ── Cache Behaviour 1: /api/* → API Gateway (no caching) ──────────────────
  ordered_cache_behavior {
    path_pattern           = "/api/*"
    target_origin_id       = "APIGWOrigin"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"]
    cached_methods         = ["GET", "HEAD"]
    compress               = false

    forwarded_values {
      query_string = true
      headers      = ["Accept", "Content-Type", "Authorization"]
      cookies {
        forward = "none"
      }
    }

    min_ttl     = 0
    default_ttl = 0
    max_ttl     = 0
  }

  # ── Default Cache Behaviour: /* → S3 (long cache for versioned assets) ─────
  default_cache_behavior {
    target_origin_id       = "S3Origin"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD"]
    compress               = true

    forwarded_values {
      query_string = true   # Needed for ?v=5 cache busting
      cookies {
        forward = "none"
      }
    }

    min_ttl     = 0
    default_ttl = 86400     # 1 day for index.html
    max_ttl     = 31536000  # 1 year for versioned CSS/JS
  }

  # SPA routing: return index.html for 403/404 (client-side routing)
  custom_error_response {
    error_code            = 403
    response_code         = 200
    response_page_path    = "/index.html"
    error_caching_min_ttl = 0
  }

  custom_error_response {
    error_code            = 404
    response_code         = 200
    response_page_path    = "/index.html"
    error_caching_min_ttl = 0
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true   # Uses *.cloudfront.net domain for free
    # To use a custom domain, replace with:
    # acm_certificate_arn      = "<certificate-arn>"
    # ssl_support_method       = "sni-only"
    # minimum_protocol_version = "TLSv1.2_2021"
  }
}
