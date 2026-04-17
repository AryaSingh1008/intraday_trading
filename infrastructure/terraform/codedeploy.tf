# ─────────────────────────────────────────────────────────────────────────────
# Lambda aliases — CodeDeploy shifts traffic between versions via these aliases.
# API Gateway integrations point to :live alias ARNs (see api_gateway.tf).
# ─────────────────────────────────────────────────────────────────────────────
resource "aws_lambda_alias" "stocks_signal_live" {
  name             = "live"
  function_name    = aws_lambda_function.stocks_signal.function_name
  function_version = "$LATEST"

  lifecycle {
    # CodeDeploy manages routing_config and function_version during deployments.
    # Terraform must not fight CodeDeploy by resetting these on every apply.
    ignore_changes = [routing_config, function_version]
  }
}

resource "aws_lambda_alias" "options_analysis_live" {
  name             = "live"
  function_name    = aws_lambda_function.options_analysis.function_name
  function_version = "$LATEST"

  lifecycle {
    ignore_changes = [routing_config, function_version]
  }
}

# ─────────────────────────────────────────────────────────────────────────────
# API Gateway permissions for the :live aliases
# (The $LATEST permissions already exist via aws_lambda_permission.api_gateway
# for-each loop — these are the additional alias-qualified permissions.)
# ─────────────────────────────────────────────────────────────────────────────
resource "aws_lambda_permission" "api_gateway_stocks_signal_alias" {
  statement_id  = "AllowAPIGatewayInvokeAlias"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.stocks_signal.function_name
  qualifier     = aws_lambda_alias.stocks_signal_live.name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*/*"
}

resource "aws_lambda_permission" "api_gateway_options_analysis_alias" {
  statement_id  = "AllowAPIGatewayInvokeAlias"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.options_analysis.function_name
  qualifier     = aws_lambda_alias.options_analysis_live.name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*/*"
}

# ─────────────────────────────────────────────────────────────────────────────
# CloudWatch Alarms — trigger automatic CodeDeploy rollback on error spike
# ─────────────────────────────────────────────────────────────────────────────
resource "aws_cloudwatch_metric_alarm" "stocks_signal_errors" {
  alarm_name          = "${local.prefix}-stocks-signal-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 60
  statistic           = "Sum"
  threshold           = 3
  treat_missing_data  = "notBreaching"
  alarm_description   = "Triggers CodeDeploy rollback when stocks-signal errors exceed threshold"

  dimensions = {
    FunctionName = aws_lambda_function.stocks_signal.function_name
    Resource     = "${aws_lambda_function.stocks_signal.function_name}:live"
  }
}

resource "aws_cloudwatch_metric_alarm" "options_analysis_errors" {
  alarm_name          = "${local.prefix}-options-analysis-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 60
  statistic           = "Sum"
  threshold           = 2
  treat_missing_data  = "notBreaching"
  alarm_description   = "Triggers CodeDeploy rollback when options-analysis errors exceed threshold"

  dimensions = {
    FunctionName = aws_lambda_function.options_analysis.function_name
    Resource     = "${aws_lambda_function.options_analysis.function_name}:live"
  }
}

# ─────────────────────────────────────────────────────────────────────────────
# CodeDeploy Application (Lambda compute platform)
# ─────────────────────────────────────────────────────────────────────────────
resource "aws_codedeploy_app" "lambda" {
  name             = "${local.prefix}-lambda-app"
  compute_platform = "Lambda"
}

# ─────────────────────────────────────────────────────────────────────────────
# Deployment Group: stocks-signal
# Strategy: Canary — send 10% traffic to new version for 5 minutes before full shift.
# If the CloudWatch alarm fires during the bake time, CodeDeploy auto-rolls back.
# ─────────────────────────────────────────────────────────────────────────────
resource "aws_codedeploy_deployment_group" "stocks_signal" {
  app_name               = aws_codedeploy_app.lambda.name
  deployment_group_name  = "${local.prefix}-stocks-signal-dg"
  service_role_arn       = aws_iam_role.codedeploy.arn
  deployment_config_name = "CodeDeployDefault.LambdaCanary10Percent5Minutes"

  deployment_style {
    deployment_option = "WITH_TRAFFIC_CONTROL"
    deployment_type   = "BLUE_GREEN"
  }

  auto_rollback_configuration {
    enabled = true
    events  = ["DEPLOYMENT_FAILURE", "DEPLOYMENT_STOP_ON_ALARM"]
  }

  alarm_configuration {
    alarms  = [aws_cloudwatch_metric_alarm.stocks_signal_errors.alarm_name]
    enabled = true
  }
}

# ─────────────────────────────────────────────────────────────────────────────
# Deployment Group: options-analysis
# Strategy: Linear — add 10% traffic every 1 minute (full shift in 10 minutes).
# ─────────────────────────────────────────────────────────────────────────────
resource "aws_codedeploy_deployment_group" "options_analysis" {
  app_name               = aws_codedeploy_app.lambda.name
  deployment_group_name  = "${local.prefix}-options-analysis-dg"
  service_role_arn       = aws_iam_role.codedeploy.arn
  deployment_config_name = "CodeDeployDefault.LambdaLinear10PercentEvery1Minute"

  deployment_style {
    deployment_option = "WITH_TRAFFIC_CONTROL"
    deployment_type   = "BLUE_GREEN"
  }

  auto_rollback_configuration {
    enabled = true
    events  = ["DEPLOYMENT_FAILURE", "DEPLOYMENT_STOP_ON_ALARM"]
  }

  alarm_configuration {
    alarms  = [aws_cloudwatch_metric_alarm.options_analysis_errors.alarm_name]
    enabled = true
  }
}
