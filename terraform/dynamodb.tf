resource "aws_dynamodb_table" "dynamodb_table" {
  name             = var.dynamodb_table_name
  read_capacity    = 1
  write_capacity   = 1
  hash_key         = "event_id"
  stream_enabled   = true
  stream_view_type = "NEW_IMAGE"

  attribute {
    name = "event_id"
    type = "N"
  }
}

resource "aws_lambda_event_source_mapping" "dynamodb_table" {
  batch_size        = 1
  event_source_arn  = aws_dynamodb_table.dynamodb_table.stream_arn
  enabled           = true
  function_name     = module.send_lambda.arn
  starting_position = "LATEST"
}
