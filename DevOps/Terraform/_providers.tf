terraform {
  required_version = ">= 0.14.2"

  backend "s3" {
    bucket = "streamlyne-terraform-us-east-1"
    key    = "terraform.tfstate"
    region = "us-east-1"

    encrypt    = true
    kms_key_id = "dd24309d-db51-422f-9c2c-916abe631091"

    dynamodb_table = "streamlyne-terraform"

    role_arn = "arn:aws:iam::608692395687:role/terraform"
  }

  required_providers {
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.0"
    }
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
}

provider "aws" {
  region     = var.aws_region_primary
  access_key = var.aws_access_key
  secret_key = var.aws_secret_key
  token      = var.aws_session_token
}
