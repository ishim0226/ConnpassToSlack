variable "region" {
  default = "ap-northeast-1"
}
variable "app_name" {
  default = "connpass_to_slack"
}
variable "dynamodb_table_name" {
  default = "connpass_to_slack"
}
variable "triggerd_get_lambda" {
  default = "cron(10 * * * ? *)"
}
variable "get_lambda_name" {
  default = "get_from_connpass"
}
variable "send_lambda_name" {
  default = "send_to_slack"
}
variable "get_lambda_environment" {
  type = map
  default = {
    "CONNPASS_URL" = "https://connpass.com/api/v1/event/"
    "DYNAMO_TABLE" = "connpass_to_slack"
    "KEYWORD"      = "meetup,aws,gcp"
  }
}
variable "send_lambda_environment" {
  type = map
  default = {
    "CONNPASS_URL"   = "https://connpass.com/api/v1/event/"
    "DYNAMO_TABLE"   = "connpass_to_slack"
    "ADDRESS_FILTER" = "東京,神奈川"
    "WEBHOOK_URL"    = "https://hooks.slack.com/services/dummy"
  }
}
