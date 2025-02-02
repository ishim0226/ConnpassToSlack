resource "aws_cloudwatch_event_rule" "event_rule" {
  name                = var.name
  schedule_expression = var.schedule
}

resource "aws_cloudwatch_event_target" "event_target" {
  rule = aws_cloudwatch_event_rule.event_rule.name
  arn  = var.lambda_arn
  input = var.input
}

output "rule_arn" {
  value = aws_cloudwatch_event_rule.event_rule.arn
}
