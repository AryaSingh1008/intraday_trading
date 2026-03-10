# ─────────────────────────────────────────────────────────────────────────────
# terraform.tfvars — fill in before running terraform apply
# ─────────────────────────────────────────────────────────────────────────────

aws_region     = "us-east-1"
aws_account_id = "REDACTED"
project_name   = "trading"
environment    = "prod"

bedrock_model_id = "anthropic.claude-3-haiku-20240307-v1:0"

# Set to true AFTER running: infrastructure/build_layers.sh
lambda_layers_built = true
