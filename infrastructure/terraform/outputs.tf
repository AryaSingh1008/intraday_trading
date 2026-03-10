output "cloudfront_url" {
  description = "CloudFront distribution URL — open this in your browser"
  value       = "https://${aws_cloudfront_distribution.main.domain_name}"
}

output "api_gateway_url" {
  description = "API Gateway base URL (accessed via CloudFront /api/*)"
  value       = aws_apigatewayv2_api.main.api_endpoint
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID (needed for cache invalidation)"
  value       = aws_cloudfront_distribution.main.id
}

output "frontend_bucket" {
  description = "S3 bucket for frontend files"
  value       = aws_s3_bucket.frontend.bucket
}

output "exports_bucket" {
  description = "S3 bucket for temporary Excel exports"
  value       = aws_s3_bucket.exports.bucket
}

output "dynamodb_cache_table" {
  description = "DynamoDB cache table name"
  value       = aws_dynamodb_table.cache.name
}

output "dynamodb_wishlist_table" {
  description = "DynamoDB wishlist table name"
  value       = aws_dynamodb_table.wishlist.name
}

output "dynamodb_iv_history_table" {
  description = "DynamoDB IV history table name"
  value       = aws_dynamodb_table.iv_history.name
}

output "bedrock_agent_id" {
  description = "Bedrock Agent ID — update BEDROCK_AGENT_ID in trading-bedrock-chat Lambda env var after deploy"
  value       = aws_bedrockagent_agent.trading_advisor.agent_id
}

output "bedrock_agent_alias_id" {
  description = "Bedrock Agent Alias ID — update BEDROCK_AGENT_ALIAS_ID in trading-bedrock-chat Lambda"
  value       = aws_bedrockagent_agent_alias.prod.agent_alias_id
}

output "terraform_deployer_access_key" {
  description = "Access key ID for the new terraform-deployer IAM user (use instead of root)"
  value       = aws_iam_access_key.terraform_deployer_key.id
  sensitive   = false
}

output "terraform_deployer_secret_key" {
  description = "Secret access key for terraform-deployer — save this securely, shown only once"
  value       = aws_iam_access_key.terraform_deployer_key.secret
  sensitive   = true   # Use: terraform output -raw terraform_deployer_secret_key
}

output "lambda_layer_status" {
  description = "Lambda layer deployment status"
  value       = var.lambda_layers_built ? "✅ Layers deployed" : "⚠️ Run build_layers.sh then set lambda_layers_built=true"
}
