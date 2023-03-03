terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.20"
    }
  }
}

locals {
  project = "boto3-executor-lambda"
  lambda_managed_policy_arns = [
    "arn:${data.aws_partition.current.partition}:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
    "arn:${data.aws_partition.current.partition}:iam::aws:policy/ReadOnlyAccess"
  ]
}

provider "aws" {
  default_tags {
    tags = {
      Project = local.project
    }
  }
}

data "aws_partition" "current" {}
data "aws_region" "current" {}

resource "aws_s3_bucket" "boto3_responses" {
  bucket_prefix = local.project
  force_destroy = true
}

module "lambda_function" {
  source = "terraform-aws-modules/lambda/aws"

  function_name = local.project
  handler       = "boto3_executor_lambda.lambda_handler"
  runtime       = "python3.9"
  source_path   = "./boto3_executor_lambda.py"
  timeout       = 30

  cloudwatch_logs_retention_in_days = 60

  attach_policies    = true
  policies           = local.lambda_managed_policy_arns
  number_of_policies = length(local.lambda_managed_policy_arns)

  attach_policy_json = true
  policy_json = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action   = "s3:PutObject"
        Effect   = "Allow"
        Resource = "${aws_s3_bucket.boto3_responses.arn}/*"
      },
    ]
  })

  environment_variables = {
    RESPONSE_S3_BUCKET = aws_s3_bucket.boto3_responses.bucket
  }
}

output "lambda_arn" {
  value = module.lambda_function.lambda_function_arn
}
output "cli_invoke_1" {
  # value = <<-EOT
  # aws --region ${data.aws_region.current.name} lambda invoke --function-name ${module.lambda_function.lambda_function_name} --payload '{
  #   "boto3_client_name": "ec2",
  #   "boto3_method_name": "describe_instance_types",
  #   "boto3_method_kwargs": {
  #     "Filters": [
  #       {"Name": "bare-metal", "Values": ["false"]},
  #       {"Name": "current-generation", "Values": ["true"]}
  #     ]
  #   },
  #   "boto3_paginator_response_items_key": "InstanceTypes"
  # }' /dev/stdout
  # EOT
  value = join(
    "",
    [
      "aws --region ",
      data.aws_region.current.name,
      " lambda invoke --function-name ",
      module.lambda_function.lambda_function_name,
      " --cli-binary-format raw-in-base64-out --payload '",
      jsonencode({
        boto3_client_name = "ec2"
        boto3_method_name = "describe_instance_types",
        boto3_method_kwargs = {
          Filters = [
            { Name = "bare-metal", Values = ["false"] },
            { Name = "current-generation", Values = ["true"] }
          ]
        },
        boto3_paginator_response_items_key = "InstanceTypes"
      }),
      "' ./lambda-response.json\n",
    ]
  )
}
