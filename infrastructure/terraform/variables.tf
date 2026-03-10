variable "aws_region" {
  description = "AWS region — must be us-east-1 for Bedrock Claude Haiku"
  type        = string
  default     = "us-east-1"
}

variable "aws_account_id" {
  description = "AWS account ID"
  type        = string
  default     = "REDACTED"
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
  default     = "anthropic.claude-3-haiku-20240307-v1:0"
}

variable "lambda_layers_built" {
  description = "Set to true once you have run build_layers.sh and the layer ZIPs exist"
  type        = bool
  default     = false
}
