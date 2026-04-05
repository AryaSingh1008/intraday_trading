variable "aws_region" {
  description = "AWS region — must be us-east-1 for Bedrock Claude Haiku"
  type        = string
  default     = "us-east-1"
}

variable "aws_account_id" {
  description = "AWS account ID — pass via TF_VAR_aws_account_id, never hardcode"
  type        = string
  sensitive   = true
}

variable "project_name" {
  description = "Project name used as prefix for all resources"
  type        = string
  default     = "trading"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "prod"
}

variable "bedrock_model_id" {
  description = "Bedrock foundation model for the agent"
  type        = string
  # Claude Haiku 4.5 — active model, cross-region inference profile
  default     = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
}

variable "lambda_layers_built" {
  description = "Set to true once you have run build_layers.sh and the layer ZIPs exist"
  type        = bool
  default     = false
}
