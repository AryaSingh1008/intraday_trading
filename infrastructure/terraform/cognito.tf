# ─────────────────────────────────────────────────────────────────────────────
# Cognito User Pool — email/password auth with open signup
# ─────────────────────────────────────────────────────────────────────────────

resource "aws_cognito_user_pool" "main" {
  name = "${local.prefix}-user-pool"

  # Users sign in with their email address
  username_attributes      = ["email"]
  auto_verified_attributes = ["email"]

  # Password policy — keep it reasonable for a personal trading app
  password_policy {
    minimum_length                   = 8
    require_uppercase                = true
    require_lowercase                = true
    require_numbers                  = true
    require_symbols                  = false
    temporary_password_validity_days = 7
  }

  # Email attribute is required at signup
  schema {
    name                     = "email"
    attribute_data_type      = "String"
    required                 = true
    mutable                  = true
    string_attribute_constraints {
      min_length = 5
      max_length = 254
    }
  }

  # Account recovery via verified email
  account_recovery_setting {
    recovery_mechanism {
      name     = "verified_email"
      priority = 1
    }
  }

  # Use Cognito's default email sender (no SES setup needed)
  email_configuration {
    email_sending_account = "COGNITO_DEFAULT"
  }

  # Allow users to self-register (open signup)
  admin_create_user_config {
    allow_admin_create_user_only = false
  }

  tags = local.common_tags
}

# ─────────────────────────────────────────────────────────────────────────────
# Cognito App Client — public SPA client (no secret)
# ─────────────────────────────────────────────────────────────────────────────

resource "aws_cognito_user_pool_client" "web" {
  name         = "${local.prefix}-web-client"
  user_pool_id = aws_cognito_user_pool.main.id

  # No client secret — SPA runs in the browser and can't keep secrets
  generate_secret = false

  # Auth flows needed for the amazon-cognito-identity-js SDK
  explicit_auth_flows = [
    "ALLOW_USER_SRP_AUTH",       # Secure Remote Password (default SDK flow)
    "ALLOW_USER_PASSWORD_AUTH",  # Direct password auth (fallback)
    "ALLOW_REFRESH_TOKEN_AUTH",  # Token refresh — keeps users logged in
  ]

  # Token validity
  access_token_validity  = 60   # minutes
  id_token_validity      = 60   # minutes
  refresh_token_validity = 30   # days

  token_validity_units {
    access_token  = "minutes"
    id_token      = "minutes"
    refresh_token = "days"
  }

  # Hide whether an account exists — prevents user enumeration attacks
  prevent_user_existence_errors = "ENABLED"
}

# ─────────────────────────────────────────────────────────────────────────────
# API Gateway JWT Authorizer — validates Cognito ID tokens on every request
# ─────────────────────────────────────────────────────────────────────────────

resource "aws_apigatewayv2_authorizer" "cognito_jwt" {
  api_id           = aws_apigatewayv2_api.main.id
  authorizer_type  = "JWT"
  name             = "${local.prefix}-cognito-jwt"
  identity_sources = ["$request.header.Authorization"]

  jwt_configuration {
    # Cognito OIDC discovery endpoint — API GW fetches JWKS from here
    issuer   = "https://cognito-idp.${local.region}.amazonaws.com/${aws_cognito_user_pool.main.id}"
    # Only tokens issued for this specific app client are accepted
    audience = [aws_cognito_user_pool_client.web.id]
  }
}
