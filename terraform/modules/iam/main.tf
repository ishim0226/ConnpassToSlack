# Lambda Role
resource "aws_iam_role" "lambda_role" {
  name = "${var.name}-lambda-role"

  assume_role_policy = <<POLICY
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Effect": "Allow"
    }
  ]
}
POLICY
}

# Lambda Policy Data
## for CWL
data "aws_iam_policy_document" "lambda_for_cwl_policy_document" {
  statement {
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]

    effect    = "Allow"
    resources = ["*"]
  }
}
resource "aws_iam_policy" "lambda_for_cwl_policy" {
  name        = "${var.name}_lambda_for_cwl_policy"
  description = "lambda for cwl policy"

  policy = data.aws_iam_policy_document.lambda_for_cwl_policy_document.json
}

## for Dynamodb
data "aws_iam_policy_document" "lambda_for_dynamo_policy_document" {
  statement {
    actions = [
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
      "dynamodb:ListStreams",
      "dynamodb:DescribeStream",
      "dynamodb:GetShardIterator",
      "dynamodb:GetRecords"
    ]

    effect    = "Allow"
    resources = [
      "arn:aws:dynamodb:*:*:table/${var.name}",
      "arn:aws:dynamodb:*:*:table/${var.name}/*"
    ]
  }
}
resource "aws_iam_policy" "lambda_for_dynamo_policy" {
  name        = "${var.name}_lambda_for_dynamo_policy"
  description = "lambda for dynamo policy"

  policy = data.aws_iam_policy_document.lambda_for_dynamo_policy_document.json
}

# Lambda Attach Role to Policy
## for CWL
resource "aws_iam_policy_attachment" "lambda_for_cwl_policy_attach" {
  name       = "lambda_for_cwl_policy_attach"
  roles      = [aws_iam_role.lambda_role.name]
  policy_arn = aws_iam_policy.lambda_for_cwl_policy.arn
}

## for Dynamodb
resource "aws_iam_policy_attachment" "lambda_for_dynamo_policy_attach" {
  name       = "lambda_for_dynamo_policy_attach"
  roles      = [aws_iam_role.lambda_role.name]
  policy_arn = aws_iam_policy.lambda_for_dynamo_policy.arn
}

# output
output "lambda_role_arn" {
  value = aws_iam_role.lambda_role.arn
}