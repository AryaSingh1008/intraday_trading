# ─────────────────────────────────────────────────────────────────────────────
# terraform.tfvars — fill in before running terraform apply
# ─────────────────────────────────────────────────────────────────────────────

aws_region     = "us-east-1"
aws_account_id = "975050340221"
project_name   = "trading"
environment    = "prod"

# Claude 3 Haiku requires Anthropic use-case details form (one-time, per-account).
# Using Amazon Nova Lite cross-region inference profile — no form needed, supports tool-use.
bedrock_model_id = "us.amazon.nova-lite-v1:0"

# Set to true AFTER running: infrastructure/build_layers.sh
lambda_layers_built = true
