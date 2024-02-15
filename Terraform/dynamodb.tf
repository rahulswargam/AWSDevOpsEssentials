resource "aws_dynamodb_table" "trigger_codebuild_random" {
  name           = "trigger_codebuild_random"
  billing_mode   = "PROVISIONED"
  read_capacity  = 2
  write_capacity = 2
  hash_key       = "id"

  attribute {
    name = "id"
    type = "S"
  }
}
