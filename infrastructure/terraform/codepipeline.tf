# ─────────────────────────────────────────────────────────────────────────────
# DISABLED — GitHub Actions owns deployments now.
# Uncomment to re-enable AWS CodePipeline.
# ─────────────────────────────────────────────────────────────────────────────

/*

# ─────────────────────────────────────────────────────────────────────────────
# S3 Artifact Store — shared by both pipelines
# ─────────────────────────────────────────────────────────────────────────────
resource "aws_s3_bucket" "pipeline_artifacts" {
  bucket        = "${local.prefix}-pipeline-artifacts-${local.account_id}"
  force_destroy = true
}

resource "aws_s3_bucket_versioning" "pipeline_artifacts" {
  bucket = aws_s3_bucket.pipeline_artifacts.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket_lifecycle_configuration" "pipeline_artifacts" {
  bucket = aws_s3_bucket.pipeline_artifacts.id

  rule {
    id     = "expire-old-artifacts"
    status = "Enabled"
    filter {}
    expiration { days = 30 }
  }
}

resource "aws_s3_bucket_public_access_block" "pipeline_artifacts" {
  bucket                  = aws_s3_bucket.pipeline_artifacts.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ─────────────────────────────────────────────────────────────────────────────
# CodeStar Connection — GitHub v2 App
# IMPORTANT: After terraform apply, go to AWS Developer Tools → Connections,
# find this connection in "Pending" state, and click "Update pending connection"
# to authorize the GitHub App. This one-time step cannot be automated.
# ─────────────────────────────────────────────────────────────────────────────
resource "aws_codestarconnections_connection" "github" {
  name          = "${local.prefix}-github-connection"
  provider_type = "GitHub"
}

# ─────────────────────────────────────────────────────────────────────────────
# SNS Topic — Manual approval notifications
# ─────────────────────────────────────────────────────────────────────────────
resource "aws_sns_topic" "pipeline_approvals" {
  name = "${local.prefix}-pipeline-approvals"
}

resource "aws_sns_topic_subscription" "approval_email" {
  topic_arn = aws_sns_topic.pipeline_approvals.arn
  protocol  = "email"
  endpoint  = "singh.arya1097@gmail.com"
}

# ─────────────────────────────────────────────────────────────────────────────
# Infrastructure Pipeline (V2)
# Triggers on pushes to main that touch: infrastructure/**, lambdas/**,
# backend/**, prompts/**
#
# Stages:
#   1. Source      — pull from GitHub via CodeStar
#   2. BuildLayers — run build_layers.sh + zip handlers
#   3. TfPlan      — terraform plan → tfplan artifact
#   4. Approval    — manual gate (SNS email)
#   5. TfApply     — terraform apply + CodeDeploy traffic shift
# ─────────────────────────────────────────────────────────────────────────────
resource "aws_codepipeline" "infra" {
  name           = "${local.prefix}-infra-pipeline"
  role_arn       = aws_iam_role.codepipeline.arn
  pipeline_type  = "V2"
  execution_mode = "QUEUED"

  artifact_store {
    location = aws_s3_bucket.pipeline_artifacts.bucket
    type     = "S3"
  }

  trigger {
    provider_type = "CodeStarSourceConnection"
    git_configuration {
      source_action_name = "GitHub_Source"
      push {
        branches {
          includes = ["main"]
        }
        file_paths {
          includes = [
            "infrastructure/**",
            "lambdas/**",
            "backend/**",
            "prompts/**",
          ]
        }
      }
    }
  }

  stage {
    name = "Source"
    action {
      name             = "GitHub_Source"
      category         = "Source"
      owner            = "AWS"
      provider         = "CodeStarSourceConnection"
      version          = "1"
      output_artifacts = ["SourceArtifact"]

      configuration = {
        ConnectionArn        = aws_codestarconnections_connection.github.arn
        FullRepositoryId     = "AryaSingh1008/intraday_trading"
        BranchName           = "main"
        OutputArtifactFormat = "CODE_ZIP"
        DetectChanges        = "false"
      }
    }
  }

  stage {
    name = "BuildLayers"
    action {
      name             = "Build_Lambda_Layers"
      category         = "Build"
      owner            = "AWS"
      provider         = "CodeBuild"
      version          = "1"
      input_artifacts  = ["SourceArtifact"]
      output_artifacts = ["LayerArtifact"]

      configuration = {
        ProjectName = aws_codebuild_project.build_layers.name
      }
    }
  }

  stage {
    name = "TerraformPlan"
    action {
      name             = "Terraform_Plan"
      category         = "Build"
      owner            = "AWS"
      provider         = "CodeBuild"
      version          = "1"
      input_artifacts  = ["LayerArtifact"]
      output_artifacts = ["PlanArtifact"]

      configuration = {
        ProjectName = aws_codebuild_project.terraform_plan.name
      }
    }
  }

  stage {
    name = "Approval"
    action {
      name     = "Manual_Approval"
      category = "Approval"
      owner    = "AWS"
      provider = "Manual"
      version  = "1"

      configuration = {
        NotificationArn    = aws_sns_topic.pipeline_approvals.arn
        CustomData         = "Terraform plan complete. Review the plan in CodeBuild logs then approve to apply."
        ExternalEntityLink = "https://${local.region}.console.aws.amazon.com/codesuite/codebuild/${local.account_id}/projects/${aws_codebuild_project.terraform_plan.name}/history"
      }
    }
  }

  stage {
    name = "TerraformApply"
    action {
      name            = "Terraform_Apply"
      category        = "Build"
      owner           = "AWS"
      provider        = "CodeBuild"
      version         = "1"
      input_artifacts = ["PlanArtifact"]

      configuration = {
        ProjectName = aws_codebuild_project.terraform_apply.name
      }
    }
  }
}

# ─────────────────────────────────────────────────────────────────────────────
# Frontend Pipeline (V2)
# Triggers on pushes to main that touch: frontend/**
# ─────────────────────────────────────────────────────────────────────────────
resource "aws_codepipeline" "frontend" {
  name           = "${local.prefix}-frontend-pipeline"
  role_arn       = aws_iam_role.codepipeline.arn
  pipeline_type  = "V2"
  execution_mode = "SUPERSEDED"

  artifact_store {
    location = aws_s3_bucket.pipeline_artifacts.bucket
    type     = "S3"
  }

  trigger {
    provider_type = "CodeStarSourceConnection"
    git_configuration {
      source_action_name = "GitHub_Source"
      push {
        branches {
          includes = ["main"]
        }
        file_paths {
          includes = ["frontend/**"]
        }
      }
    }
  }

  stage {
    name = "Source"
    action {
      name             = "GitHub_Source"
      category         = "Source"
      owner            = "AWS"
      provider         = "CodeStarSourceConnection"
      version          = "1"
      output_artifacts = ["SourceArtifact"]

      configuration = {
        ConnectionArn        = aws_codestarconnections_connection.github.arn
        FullRepositoryId     = "AryaSingh1008/intraday_trading"
        BranchName           = "main"
        OutputArtifactFormat = "CODE_ZIP"
        DetectChanges        = "false"
      }
    }
  }

  stage {
    name = "Deploy"
    action {
      name            = "Deploy_Frontend"
      category        = "Build"
      owner           = "AWS"
      provider        = "CodeBuild"
      version         = "1"
      input_artifacts = ["SourceArtifact"]

      configuration = {
        ProjectName = aws_codebuild_project.frontend_deploy.name
      }
    }
  }
}

# ─────────────────────────────────────────────────────────────────────────────
# Outputs — useful for verifying setup in the console
# ─────────────────────────────────────────────────────────────────────────────
output "infra_pipeline_name" {
  value       = aws_codepipeline.infra.name
  description = "Name of the infrastructure CodePipeline"
}

output "frontend_pipeline_name" {
  value       = aws_codepipeline.frontend.name
  description = "Name of the frontend CodePipeline"
}

output "github_connection_arn" {
  value       = aws_codestarconnections_connection.github.arn
  description = "CodeStar GitHub connection ARN — must be manually activated in the console"
}

output "pipeline_artifacts_bucket" {
  value       = aws_s3_bucket.pipeline_artifacts.bucket
  description = "S3 bucket used as CodePipeline artifact store"
  sensitive   = true
}

*/
