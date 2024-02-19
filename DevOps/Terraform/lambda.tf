# Lambda Function for CodeBuild Status Notifications
resource "aws_lambda_function" "codebuild_status_notifications" {
  filename         = "files/build_status_notifications.zip"
  function_name    = "cicd_build_status_notifications"
  role             = aws_iam_role.cicd_lambda_execution_role.arn
  handler          = "build_status_notification.lambda_handler"
  source_code_hash = filebase64sha256("files/build_status_notifications.zip")
  runtime          = "python3.9"
  timeout          = 30

  environment {
    variables = {
      TEAMS_WEBHOOK_URL = var.teams_webhook_url
      S3_BUCKET         = aws_s3_bucket.streamlyne_cicd.bucket
    }
  }
}

# CloudWatch Event Rule for CodeBuild Status Change
resource "aws_cloudwatch_event_rule" "codebuild_event_rule" {
  name        = "codebuild_status_event_rule"
  description = "This Rule is used to send CodeBuild Status notifications whenever the Build status is changed"
  event_pattern = jsonencode({
    source      = ["aws.codebuild"],
    detail-type = ["CodeBuild Build State Change"],
    detail = {
      "build-status" = ["FAILED", "STOPPED", "SUCCEEDED"]
    }
  })
}

# CloudWatch Event Target CodeBuild Status Change
resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.codebuild_event_rule.name
  target_id = var.target_id
  arn       = aws_lambda_function.codebuild_status_notifications.arn
}

# Invoke Lambda Function
resource "aws_lambda_permission" "allow_cloudwatch_to_call_lambda" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.codebuild_status_notifications.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.codebuild_event_rule.arn
}

# SNS
resource "aws_sns_topic" "sns_topic" {
  name = "codebuild_status_notification"
}

resource "aws_sns_topic_subscription" "sns_lambda_subscription" {
  topic_arn = aws_sns_topic.sns_topic.arn
  protocol  = "lambda"
  endpoint  = aws_lambda_function.codebuild_status_notifications.arn
}

# Lambda Function file for CodeBuild Trigger random times
data "archive_file" "trigger_codebuild_random_file" {
  type        = "zip"
  source_file = "files/trigger_codebuild.py"
  output_path = "files/trigger_codebuild.zip~"
}

# Lambda function Code to Trigger during Business Hours but at Random Times
resource "aws_lambda_function" "trigger_codebuild_random_times" {
  filename         = data.archive_file.trigger_codebuild_random_file.output_path
  function_name    = "trigger_codebuild_random_times"
  role             = aws_iam_role.cicd_lambda_execution_role.arn
  handler          = "trigger_codebuild.lambda_handler"
  source_code_hash = data.archive_file.trigger_codebuild_random_file.output_base64sha256
  runtime          = "python3.9"
  timeout          = 30

  environment {
    variables = {
      PROJECTS = var.projects
    }
  }
}

# CloudWatch Event Rule for CodeBuild Random Trigger
resource "aws_cloudwatch_event_rule" "trigger_lambda_random_times" {
  name                = "trigger_codebuild_random_times"
  description         = "This Rule is used to trigger Lambda Function that triggers selected CodeBuild Projects random times"
  schedule_expression = "cron(0/15 8-16 ? * MON-FRI *)"
}

# CloudWatch Event Target CodeBuild Random Trigger
resource "aws_cloudwatch_event_target" "trigger_lambda_random_times_target" {
  rule      = aws_cloudwatch_event_rule.trigger_lambda_random_times.name
  target_id = var.target_id
  arn       = aws_lambda_function.trigger_codebuild_random_times.arn
}

# Lambda Permission for CloudWatch Event
resource "aws_lambda_permission" "cloudwatch_to_trigger_lambda" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.trigger_codebuild_random_times.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.trigger_lambda_random_times.arn
}

# Lambda Function file to Delete CodeBuild Triggered Items in DynamoDB
data "archive_file" "delete_dynamodb_items_file" {
  type        = "zip"
  source_file = "files/delete_dynamodb_items.py"
  output_path = "files/delete_dynamodb_items.zip~"
}

# Lambda Function to Delete CodeBuild Triggered Items in DynamoDB
resource "aws_lambda_function" "delete_dynamodb_items" {
  filename         = data.archive_file.delete_dynamodb_items_file.output_path
  function_name    = "delete_dynamodb_codebuild_items"
  role             = aws_iam_role.cicd_lambda_execution_role.arn
  handler          = "delete_dynamodb_items.lambda_handler"
  source_code_hash = data.archive_file.delete_dynamodb_items_file.output_base64sha256
  runtime          = "python3.9"
  timeout          = 30
}

# CloudWatch Event Rule for Delete DynamoDB Items of CodeBuild
resource "aws_cloudwatch_event_rule" "trigger_lambda_after_business_hours" {
  name                = "trigger_lambda_after_business_hours"
  description         = "This Rule is used to delete the items in DynamoDB at specific time"
  schedule_expression = "cron(0 17 ? * MON-FRI *)"
}

# CloudWatch Event Target for Deleting DynamoDB Items of CodeBuild
resource "aws_cloudwatch_event_target" "delete_dynamodb_items_target" {
  rule      = aws_cloudwatch_event_rule.trigger_lambda_after_business_hours.name
  target_id = var.target_id
  arn       = aws_lambda_function.delete_dynamodb_items.arn
}

# Lambda Permission for CloudWatch Event
resource "aws_lambda_permission" "delete_dynamodb_items_lambda_trigger" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.delete_dynamodb_items.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.trigger_lambda_after_business_hours.arn
}