variable "aws_access_key" {
  type = string
}

variable "aws_account_number" {
  type    = string
  default = "632114636116"
}

variable "aws_region_primary" {
  type    = string
  default = "us-east-1"
}

variable "aws_secret_key" {
  type = string
  # sensitive = true
}

variable "aws_session_token" {
  type = string
  # sensitive = true
}

variable "target_id" {
  type    = string
  default = "SendToLambda"
}

variable "build_images" {
  type = map(string)
  default = {
    "success.png" = "files/build_status_images/success.png",
    "failed.png"  = "files/build_status_images/failed.png"
  }
}

variable "teams_webhook_url" {
  type    = string
  default = "https://vivantech.webhook.office.com/webhookb2/8cd21dc6-62ae-47e5-9772-259fdaf5c708@9794d907-c605-4910-9050-02b9980d3e7a/IncomingWebhook/806301631f9347b7aa58b7447904638c/b3691802-f075-45f0-9e42-47b02642f96c"
}

variable "projects" {
  type    = string
  default = "internal_dev_report_deploy"
}
