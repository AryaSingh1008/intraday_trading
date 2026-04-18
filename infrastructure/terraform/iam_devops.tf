# ─────────────────────────────────────────────────────────────────────────────
# IAM: CodePipeline Role
# ─────────────────────────────────────────────────────────────────────────────
data "aws_iam_policy_document" "codepipeline_assume" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["codepipeline.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "codepipeline" {
  name               = "${local.prefix}-codepipeline-role"
  assume_role_policy = data.aws_iam_policy_document.codepipeline_assume.json
}

data "aws_iam_policy_document" "codepipeline_permissions" {
  statement {
    effect = "Allow"
    actions = [
      "s3:GetObject", "s3:GetObjectVersion", "s3:GetBucketVersioning",
      "s3:PutObject", "s3:ListBucket",
    ]
    resources = [
      aws_s3_bucket.pipeline_artifacts.arn,
      "${aws_s3_bucket.pipeline_artifacts.arn}/*",
    ]
  }

  statement {
    effect = "Allow"
    actions = ["codebuild:BatchGetBuilds", "codebuild:StartBuild"]
    resources = [
      aws_codebuild_project.build_layers.arn,
      aws_codebuild_project.terraform_plan.arn,
      aws_codebuild_project.terraform_apply.arn,
      aws_codebuild_project.frontend_deploy.arn,
    ]
  }

  statement {
    effect    = "Allow"
    actions   = ["codestar-connections:UseConnection"]
    resources = [aws_codestarconnections_connection.github.arn]
  }

  statement {
    effect    = "Allow"
    actions   = ["sns:Publish"]
    resources = [aws_sns_topic.pipeline_approvals.arn]
  }
}

resource "aws_iam_role_policy" "codepipeline" {
  name   = "${local.prefix}-codepipeline-policy"
  role   = aws_iam_role.codepipeline.id
  policy = data.aws_iam_policy_document.codepipeline_permissions.json
}

# ─────────────────────────────────────────────────────────────────────────────
# IAM: CodeBuild Role
# ─────────────────────────────────────────────────────────────────────────────
data "aws_iam_policy_document" "codebuild_assume" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["codebuild.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "codebuild" {
  name               = "${local.prefix}-codebuild-role"
  assume_role_policy = data.aws_iam_policy_document.codebuild_assume.json
}

data "aws_iam_policy_document" "codebuild_permissions" {
  statement {
    effect = "Allow"
    actions = [
      "logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents",
    ]
    resources = [
      "arn:aws:logs:${local.region}:${local.account_id}:log-group:/aws/codebuild/${local.prefix}-*",
      "arn:aws:logs:${local.region}:${local.account_id}:log-group:/aws/codebuild/${local.prefix}-*:*",
    ]
  }

  statement {
    effect = "Allow"
    actions = [
      "s3:GetObject", "s3:GetObjectVersion", "s3:PutObject",
      "s3:ListBucket", "s3:DeleteObject",
    ]
    resources = [
      aws_s3_bucket.pipeline_artifacts.arn,
      "${aws_s3_bucket.pipeline_artifacts.arn}/*",
      aws_s3_bucket.exports.arn,
      "${aws_s3_bucket.exports.arn}/*",
      aws_s3_bucket.frontend.arn,
      "${aws_s3_bucket.frontend.arn}/*",
    ]
  }

  # Terraform state bucket — bucket name comes from a GitHub secret / SSM param
  # at apply time; wildcard covers any valid state bucket name.
  statement {
    effect = "Allow"
    actions = [
      "s3:GetObject", "s3:PutObject", "s3:DeleteObject", "s3:ListBucket",
      "s3:GetBucketVersioning", "s3:GetBucketLocation", "s3:GetEncryptionConfiguration",
    ]
    resources = [
      "arn:aws:s3:::*-tf-state*",
      "arn:aws:s3:::*-tf-state*/*",
      "arn:aws:s3:::*terraform-state*",
      "arn:aws:s3:::*terraform-state*/*",
    ]
  }

  statement {
    effect = "Allow"
    actions = [
      "ssm:GetParameter", "ssm:GetParameters",
      "ssm:DescribeParameters", "ssm:GetParametersByPath",
    ]
    resources = ["*"]
  }

  # Full admin over trading-* tagged resources (same scope as github-actions OIDC role)
  statement {
    effect = "Allow"
    actions = [
      "lambda:*", "dynamodb:*", "apigateway:*",
      "cloudfront:*", "cognito-idp:*",
      "events:*", "scheduler:*",
      "bedrock:*", "logs:*", "xray:*",
    ]
    resources = ["*"]
  }

  statement {
    effect    = "Allow"
    actions   = ["iam:PassRole"]
    resources = ["arn:aws:iam::${local.account_id}:role/${local.prefix}-*"]
    condition {
      test     = "StringLike"
      variable = "iam:PassedToService"
      values = [
        "lambda.amazonaws.com",
        "codedeploy.amazonaws.com",
        "scheduler.amazonaws.com",
        "bedrock.amazonaws.com",
      ]
    }
  }

  statement {
    effect = "Allow"
    actions = [
      "iam:CreateRole", "iam:DeleteRole", "iam:GetRole", "iam:UpdateRole",
      "iam:AttachRolePolicy", "iam:DetachRolePolicy",
      "iam:PutRolePolicy", "iam:GetRolePolicy", "iam:DeleteRolePolicy",
      "iam:ListRolePolicies", "iam:ListAttachedRolePolicies",
      "iam:TagRole", "iam:UntagRole",
      "iam:CreateUser", "iam:DeleteUser", "iam:GetUser",
      "iam:CreateAccessKey", "iam:DeleteAccessKey", "iam:ListAccessKeys",
      "iam:AttachUserPolicy", "iam:DetachUserPolicy",
      "iam:ListAttachedUserPolicies", "iam:TagUser", "iam:UntagUser",
    ]
    resources = [
      "arn:aws:iam::${local.account_id}:role/${local.prefix}-*",
      "arn:aws:iam::${local.account_id}:user/terraform-deployer",
    ]
  }

  statement {
    effect    = "Allow"
    actions   = ["sts:GetCallerIdentity"]
    resources = ["*"]
  }

  statement {
    effect = "Allow"
    actions = [
      "codedeploy:CreateDeployment",
      "codedeploy:GetDeployment", "codedeploy:GetDeploymentConfig",
      "codedeploy:RegisterApplicationRevision", "codedeploy:GetApplicationRevision",
      "codedeploy:GetApplication", "codedeploy:GetDeploymentGroup",
      "codedeploy:ListDeploymentGroups", "codedeploy:BatchGetDeploymentGroups",
    ]
    resources = ["*"]
  }

  # Terraform plan reads current state of every managed resource.
  # These read-only permissions cover all services in this project's .tf files.
  statement {
    effect = "Allow"
    actions = [
      "codebuild:BatchGetProjects", "codebuild:ListProjects",
      "codepipeline:GetPipeline", "codepipeline:GetPipelineState",
      "codestar-connections:GetConnection", "codestar-connections:ListConnections",
      "codeconnections:GetConnection", "codeconnections:ListConnections",
      "s3:GetBucketPolicy", "s3:GetBucketAcl", "s3:GetBucketCORS",
      "s3:GetBucketWebsite", "s3:GetBucketLogging", "s3:GetLifecycleConfiguration",
      "s3:GetBucketObjectLockConfiguration", "s3:GetBucketPublicAccessBlock",
      "s3:GetBucketRequestPayment", "s3:GetBucketTagging",
      "s3:GetReplicationConfiguration", "s3:GetAccelerateConfiguration",
      "s3:GetBucketNotification",
      "sns:GetTopicAttributes", "sns:ListSubscriptionsByTopic", "sns:ListTagsForResource",
      "cloudwatch:DescribeAlarms", "cloudwatch:ListTagsForResource",
    ]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "codebuild" {
  name   = "${local.prefix}-codebuild-policy"
  role   = aws_iam_role.codebuild.id
  policy = data.aws_iam_policy_document.codebuild_permissions.json
}

# X-Ray write access for Lambda functions (used when tracing_config = "Active")
resource "aws_iam_role_policy_attachment" "lambda_xray" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/AWSXRayDaemonWriteAccess"
}

# ─────────────────────────────────────────────────────────────────────────────
# IAM: CodeDeploy Role
# ─────────────────────────────────────────────────────────────────────────────
data "aws_iam_policy_document" "codedeploy_assume" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["codedeploy.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "codedeploy" {
  name               = "${local.prefix}-codedeploy-role"
  assume_role_policy = data.aws_iam_policy_document.codedeploy_assume.json
}

# AWS managed policy grants CodeDeploy permission to update Lambda aliases
resource "aws_iam_role_policy_attachment" "codedeploy_lambda" {
  role       = aws_iam_role.codedeploy.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSCodeDeployRoleForLambda"
}

# Allow CodeDeploy to read alarms so it can trigger automatic rollback
data "aws_iam_policy_document" "codedeploy_cloudwatch" {
  statement {
    effect    = "Allow"
    actions   = ["cloudwatch:DescribeAlarms"]
    resources = [
      aws_cloudwatch_metric_alarm.stocks_signal_errors.arn,
      aws_cloudwatch_metric_alarm.options_analysis_errors.arn,
    ]
  }
}

resource "aws_iam_role_policy" "codedeploy_cloudwatch" {
  name   = "${local.prefix}-codedeploy-cw-policy"
  role   = aws_iam_role.codedeploy.id
  policy = data.aws_iam_policy_document.codedeploy_cloudwatch.json
}
