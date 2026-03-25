# ─────────────────────────────────────────────────────────────────────────────
# terraform.tfvars — fill in before running terraform apply
# ─────────────────────────────────────────────────────────────────────────────

aws_region     = "us-east-1"
aws_account_id = "975050340221"
project_name   = "trading"
environment    = "prod"

# Claude 3.5 Haiku — approved via Anthropic use-case form (March 2026).
# Cross-region inference profile for best availability.
bedrock_model_id = "us.anthropic.claude-3-5-haiku-20241022-v1:0"

# Set to true AFTER running: infrastructure/build_layers.sh
lambda_layers_built = true
