resource "aws_codebuild_project" "codebuild_project" {
  for_each = { for project in local.build_projects : "${project.project_type}_${project.client_name}_${project.instance_type}_deploy" => project }

  name           = each.key
  description    = "${each.value.client_name}_${each.value.instance_type}"
  build_timeout  = local.timeout
  queued_timeout = local.timeout
  service_role   = aws_iam_role.cicd_execution_role.arn

  artifacts {
    type = "NO_ARTIFACTS"
  }

  environment {
    compute_type = local.compute_type
    image        = local.build_image
    type         = local.type

    # Environment variables
    environment_variable {
      name  = "TAINT_TASK_DEF"
      value = local.taint_task_def
    }

    environment_variable {
      name  = "RECREATE_SOURCE_DB_SNAPSHOT"
      value = local.recreate_source_db_snapshot
    }

    environment_variable {
      name  = "AUTO_APPROVE"
      value = local.auto_approve
    }

    environment_variable {
      name  = "AUTO_SHUTDOWN"
      value = local.auto_shutdown
    }

    environment_variable {
      name  = "CLIENT_NAME"
      value = each.value.client_name
    }

    environment_variable {
      name  = "INSTANCE_TYPE"
      value = each.value.instance_type
    }

    environment_variable {
      name  = "AWS_ACCESS_KEY_ID"
      value = aws_ssm_parameter.cicd_access_key.name
      type  = "PARAMETER_STORE"
    }

    environment_variable {
      name  = "AWS_SECRET_ACCESS_KEY"
      value = aws_ssm_parameter.cicd_secret_key.name
      type  = "PARAMETER_STORE"
    }

    environment_variable {
      name  = "nexus_username"
      value = aws_ssm_parameter.nexus_username.name
      type  = "PARAMETER_STORE"
    }

    environment_variable {
      name  = "nexus_password"
      value = aws_ssm_parameter.nexus_password.name
      type  = "PARAMETER_STORE"
    }

    environment_variable {
      name  = "TERRAFORM"
      value = local.terraform_version
    }
  }

  source {
    type            = "GITHUB"
    location        = local.repository
    git_clone_depth = 1
    buildspec       = local.buildspec
  }

  source_version = each.value.source_version

  tags = {
    Name    = each.key
    Project = local.project_tag_value
  }
}