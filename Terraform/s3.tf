# S3 Bucket for CodeBuild Notifications
resource "aws_s3_bucket" "streamlyne_cicd" {
  bucket = "streamlyne-cicd"
}

resource "aws_s3_object" "build_status_success_image" {
  for_each = var.build_images
  bucket   = aws_s3_bucket.streamlyne_cicd.bucket
  key      = "build_status_images/${each.key}"
  source   = each.value
}