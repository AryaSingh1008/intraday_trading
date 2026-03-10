# ─────────────────────────────────────────────────────────────────────────────
# DynamoDB Table 1: trading-cache
# Replaces the in-memory _cache dict in app.py
# ─────────────────────────────────────────────────────────────────────────────
resource "aws_dynamodb_table" "cache" {
  name         = local.cache_table_name
  billing_mode = "PAY_PER_REQUEST"   # On-demand; fits within free 25 RCU/WCU always-free tier
  hash_key     = "cache_key"

  attribute {
    name = "cache_key"
    type = "S"
  }

  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }

  point_in_time_recovery {
    enabled = false   # Not needed for cache data
  }
}

# ─────────────────────────────────────────────────────────────────────────────
# DynamoDB Table 2: trading-wishlist
# Replaces data/wishlist.json
# ─────────────────────────────────────────────────────────────────────────────
resource "aws_dynamodb_table" "wishlist" {
  name         = local.wishlist_table_name
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "user_id"
  range_key    = "symbol"

  attribute {
    name = "user_id"
    type = "S"
  }

  attribute {
    name = "symbol"
    type = "S"
  }

  point_in_time_recovery {
    enabled = true   # Keep enabled — this is real user data
  }
}

# ─────────────────────────────────────────────────────────────────────────────
# DynamoDB Table 3: trading-iv-history
# Replaces data/iv_history.json (30-day rolling IV history)
# ─────────────────────────────────────────────────────────────────────────────
resource "aws_dynamodb_table" "iv_history" {
  name         = local.iv_history_table_name
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "symbol"
  range_key    = "date"

  attribute {
    name = "symbol"
    type = "S"
  }

  attribute {
    name = "date"
    type = "S"
  }

  ttl {
    attribute_name = "expires_at"
    enabled        = true   # Auto-expires entries after 31 days (30-day rolling window)
  }

  point_in_time_recovery {
    enabled = false
  }
}
