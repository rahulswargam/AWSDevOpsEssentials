resource "aws_ssm_parameter" "nexus_username" {
  name  = "/ci-cd/nexus/username"
  type  = "SecureString"
  value = local.nexus_username
}

resource "aws_ssm_parameter" "nexus_password" {
  name  = "/ci-cd/nexus/password"
  type  = "SecureString"
  value = local.nexus_password
}

resource "aws_ssm_parameter" "cicd_access_key" {
  name  = "/ci-cd/aws/access_key"
  type  = "SecureString"
  value = aws_iam_access_key.cicd_key.id
}

resource "aws_ssm_parameter" "cicd_secret_key" {
  name  = "/ci-cd/aws/secret_key"
  type  = "SecureString"
  value = aws_iam_access_key.cicd_key.secret
}
