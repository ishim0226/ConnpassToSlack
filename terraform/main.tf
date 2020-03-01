provider "aws" {
  region  = var.region
  version = "2.45.0"
}

terraform {
  required_version = ">= 0.12"
}

module "iam" {
  source = "./modules/iam"
  name   = var.app_name
}

module "get_lambda" {
  source                = "./modules/lambda"
  name                  = var.get_lambda_name
  role_arn              = module.iam.lambda_role_arn
  lambda_source_dir     = "../lambda_src_${var.get_lambda_name}"
  lambda_handler        = "lambda_function.lambda_handler"
  function_runtime      = "python3.8"
  memory_size           = 256
  timeout               = 180
  log_retention_in_days = 14
  environment           = var.get_lambda_environment
}

module "send_lambda" {
  source                = "./modules/lambda"
  name                  = var.send_lambda_name
  role_arn              = module.iam.lambda_role_arn
  lambda_source_dir     = "../lambda_src_${var.send_lambda_name}"
  lambda_handler        = "lambda_function.lambda_handler"
  function_runtime      = "python3.8"
  memory_size           = 128
  timeout               = 30
  log_retention_in_days = 14
  environment           = var.send_lambda_environment
}

module "get_cloudwatch_event" {
  source     = "./modules/cloudwatch"
  name       = var.get_lambda_name
  schedule   = var.triggerd_get_lambda
  input      = ""
  lambda_arn = module.get_lambda.arn
}

resource "aws_lambda_permission" "allow_cloudwatch_for_get_lambda" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = module.get_lambda.function_name
  principal     = "events.amazonaws.com"
  source_arn    = module.get_cloudwatch_event.rule_arn
}
