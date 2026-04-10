# ─────────────────────────────────────────────────────────────────────────────
# terraform.tfvars — fill in before running terraform apply
# ─────────────────────────────────────────────────────────────────────────────

aws_region   = "us-east-1"
project_name = "trading"
environment  = "prod"

# aws_account_id is passed via TF_VAR_aws_account_id (never commit secrets)

# Claude Haiku 4.5 — active model, no marketplace subscription needed.
# Cross-region inference profile for best availability.
bedrock_model_id = "us.anthropic.claude-haiku-4-5-20251001-v1:0"

# Set to true AFTER running: infrastructure/build_layers.sh
lambda_layers_built = true
