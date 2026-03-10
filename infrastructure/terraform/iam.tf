# ─────────────────────────────────────────────────────────────────────────────
# IAM: Terraform deployer user (use instead of root for day-to-day operations)
# ─────────────────────────────────────────────────────────────────────────────
resource "aws_iam_user" "terraform_deployer" {
  name = "terraform-deployer"
  path = "/"
}

resource "aws_iam_user_policy_attachment" "terraform_deployer_admin" {
  user       = aws_iam_user.terraform_deployer.name
  policy_arn = "arn:aws:iam::aws:policy/AdministratorAccess"
  # Note: After initial deploy, scope this down to only the services used.
}

resource "aws_iam_access_key" "terraform_deployer_key" {
  user = aws_iam_user.terraform_deployer.name
}

# ─────────────────────────────────────────────────────────────────────────────
# IAM: Lambda Execution Role (shared by all Lambda functions)
# ─────────────────────────────────────────────────────────────────────────────
data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "lambda_exec" {
  name               = "${local.prefix}-lambda-exec-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
}

# CloudWatch Logs
resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# DynamoDB access
data "aws_iam_policy_document" "lambda_dynamodb" {
  statement {
    effect = "Allow"
    actions = [
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:DeleteItem",
      "dynamodb:Query",
      "dynamodb:Scan",
      "dynamodb:BatchWriteItem",
      "dynamodb:UpdateItem",
    ]
    resources = [
      "arn:aws:dynamodb:${local.region}:${local.account_id}:table/${local.cache_table_name}",
      "arn:aws:dynamodb:${local.region}:${local.account_id}:table/${local.wishlist_table_name}",
      "arn:aws:dynamodb:${local.region}:${local.account_id}:table/${local.iv_history_table_name}",
    ]
  }
}

resource "aws_iam_role_policy" "lambda_dynamodb" {
  name   = "${local.prefix}-lambda-dynamodb-policy"
  role   = aws_iam_role.lambda_exec.id
  policy = data.aws_iam_policy_document.lambda_dynamodb.json
}

# S3 access (exports bucket)
data "aws_iam_policy_document" "lambda_s3" {
  statement {
    effect = "Allow"
    actions = [
      "s3:PutObject",
      "s3:GetObject",
      "s3:DeleteObject",
    ]
    resources = [
      "arn:aws:s3:::${local.exports_bucket_name}/*",
    ]
  }
}

resource "aws_iam_role_policy" "lambda_s3" {
  name   = "${local.prefix}-lambda-s3-policy"
  role   = aws_iam_role.lambda_exec.id
  policy = data.aws_iam_policy_document.lambda_s3.json
}

# Bedrock access (for bedrock-chat Lambda to invoke the agent)
data "aws_iam_policy_document" "lambda_bedrock" {
  statement {
    effect = "Allow"
    actions = [
      "bedrock:InvokeAgent",
      "bedrock:InvokeModel",
    ]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "lambda_bedrock" {
  name   = "${local.prefix}-lambda-bedrock-policy"
  role   = aws_iam_role.lambda_exec.id
  policy = data.aws_iam_policy_document.lambda_bedrock.json
}

# Lambda invocation (for bedrock action groups to call other Lambdas)
data "aws_iam_policy_document" "lambda_invoke_lambda" {
  statement {
    effect = "Allow"
    actions = ["lambda:InvokeFunction"]
    resources = [
      "arn:aws:lambda:${local.region}:${local.account_id}:function:${local.prefix}-*",
    ]
  }
}

resource "aws_iam_role_policy" "lambda_invoke_lambda" {
  name   = "${local.prefix}-lambda-invoke-policy"
  role   = aws_iam_role.lambda_exec.id
  policy = data.aws_iam_policy_document.lambda_invoke_lambda.json
}

# ─────────────────────────────────────────────────────────────────────────────
# IAM: EventBridge Scheduler Role (to invoke Lambda)
# ─────────────────────────────────────────────────────────────────────────────
data "aws_iam_policy_document" "scheduler_assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["scheduler.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "scheduler_exec" {
  name               = "${local.prefix}-scheduler-exec-role"
  assume_role_policy = data.aws_iam_policy_document.scheduler_assume_role.json
}

data "aws_iam_policy_document" "scheduler_invoke_lambda" {
  statement {
    effect    = "Allow"
    actions   = ["lambda:InvokeFunction"]
    resources = [
      "arn:aws:lambda:${local.region}:${local.account_id}:function:${local.prefix}-*",
    ]
  }
}

resource "aws_iam_role_policy" "scheduler_invoke_lambda" {
  name   = "${local.prefix}-scheduler-invoke-policy"
  role   = aws_iam_role.scheduler_exec.id
  policy = data.aws_iam_policy_document.scheduler_invoke_lambda.json
}

# ─────────────────────────────────────────────────────────────────────────────
# IAM: Bedrock Agent Role
# ─────────────────────────────────────────────────────────────────────────────
data "aws_iam_policy_document" "bedrock_assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["bedrock.amazonaws.com"]
    }
    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [local.account_id]
    }
  }
}

resource "aws_iam_role" "bedrock_agent" {
  name               = "${local.prefix}-bedrock-agent-role"
  assume_role_policy = data.aws_iam_policy_document.bedrock_assume_role.json
}

data "aws_iam_policy_document" "bedrock_agent_permissions" {
  statement {
    effect    = "Allow"
    actions   = ["bedrock:InvokeModel"]
    resources = ["arn:aws:bedrock:${local.region}::foundation-model/${var.bedrock_model_id}"]
  }
  statement {
    effect    = "Allow"
    actions   = ["lambda:InvokeFunction"]
    resources = [
      "arn:aws:lambda:${local.region}:${local.account_id}:function:${local.prefix}-bedrock-*",
    ]
  }
}

resource "aws_iam_role_policy" "bedrock_agent_permissions" {
  name   = "${local.prefix}-bedrock-agent-policy"
  role   = aws_iam_role.bedrock_agent.id
  policy = data.aws_iam_policy_document.bedrock_agent_permissions.json
}
