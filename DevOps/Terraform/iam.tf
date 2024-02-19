# CI/CD User + Keys/Roles
resource "aws_iam_user" "cicd_user" {
  name = local.user_cicd_key_name
}

resource "aws_iam_access_key" "cicd_key" {
  user = aws_iam_user.cicd_user.name
}

resource "aws_iam_policy" "assume_terraform_policy" {
  name = "cicd-assume-terraform"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Sid    = "STSAssumeTerraformRole",
        Effect = "Allow",
        Action = [
          "iam:GetRole",
          "iam:PassRole",
          "sts:AssumeRole",
        ],
        Resource = local.user_cicd_trust_account_roles
      },
      {
        Sid    = "ECR",
        Effect = "Allow",
        Action = [
          "ecr:DescribeImages",
        ],
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_user_policy_attachment" "attach_assume_to_user" {
  user       = aws_iam_user.cicd_user.name
  policy_arn = aws_iam_policy.assume_terraform_policy.arn
}



# Codebuild Execution Role
resource "aws_iam_role" "cicd_execution_role" {
  name               = "cicd-codebuild-execution-role"
  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "codebuild.amazonaws.com",
        "AWS" : "${aws_iam_user.cicd_user.arn}"
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
EOF

  managed_policy_arns = []

  inline_policy {
    name   = "cicd-codebuild-policy"
    policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": [
        "logs:CreateLogStream",
        "logs:CreateLogGroup",
        "logs:PutLogEvents",
        "logs:GetLogEvents",
        "ssm:GetParameters"
      ],
      "Effect": "Allow",
      "Resource": "*"
    }
  ]
}
EOF
  }
}

# Lambda Execution Role
resource "aws_iam_role" "cicd_lambda_execution_role" {
  name               = "cicd-lambda-execution-role"
  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "lambda.amazonaws.com",
        "AWS" : "${aws_iam_user.cicd_user.arn}"
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
EOF

  managed_policy_arns = []

  inline_policy {
    name   = "cicd-lambda-policy"
    policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": [
        "logs:CreateLogStream",
        "logs:CreateLogGroup",
        "logs:PutLogEvents",
        "logs:GetLogEvents"
      ],
      "Effect": "Allow",
      "Resource": "*"
    },
    {
      "Action": [
        "codebuild:BatchGetBuilds",
        "codebuild:ListBuildsForProject",
        "codebuild:StartBuild"
      ],
      "Effect": "Allow",
      "Resource": "*"
    },
    {
      "Action": [
        "ses:SendEmail"
      ],
      "Effect": "Allow",
      "Resource": "*"
    },
    {
      "Action": [
        "s3:GetObject"
      ],
      "Effect": "Allow",
      "Resource": [
        "arn:aws:s3:::streamlyne-cicd/*"
      ]
    },
    {
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:Scan",
        "dynamodb:DeleteItem"
      ],
      "Effect": "Allow",
      "Resource": [
        "arn:aws:dynamodb:us-east-1:632114636116:table/trigger_codebuild_random"
      ]
    }
  ]
}
EOF
  }
}