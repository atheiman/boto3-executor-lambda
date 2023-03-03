# Boto3 Executor Lambda

AWS Lambda function to make AWS API calls using Boto3 and store the response in S3. The Lambda function response specifies where the Boto3 API response data was stored in S3.

This Lambda function can be useful from other tools that can not run AWS API calls or can only handle responses up to a certain size. For example, [Step Functions AWS SDK service integrations](https://docs.aws.amazon.com/step-functions/latest/dg/supported-services-awssdk.html) can only handle responses up to 256 KB. If you are hitting the Step Functions State Machine error `The state/task returned a result with a size exceeding the maximum number of bytes service limit.`, this Lambda function is for you!

## Example Event Payloads

### [EC2 - DescribeInstanceTypes (paginated)](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2/paginator/DescribeInstanceTypes.html)
```javascript
{
  // Specify a Boto3 client and method
  "boto3_client_name": "ec2",
  "boto3_method_name": "describe_instance_types",

  // Supply any arguments you would normally pass to the Boto3 client method in dictionary format
  "boto3_method_kwargs": {
    "Filters": [
      {"Name": "bare-metal", "Values": ["false"]},
      {"Name": "current-generation", "Values": ["true"]}
    ]
  },
  // Enables paginated API call - must specify the key in the response containing items to aggregate
  "boto3_paginator_response_items_key": "InstanceTypes"
}
```

### [DynamoDB - Scan (paginated)](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb/paginator/Scan.html)
```javascript
{
  "boto3_client_name": "dynamodb",
  "boto3_method_name": "scan",
  "boto3_method_kwargs": {
    "TableName": "MyTable"
  },
  "boto3_paginator_response_items_key": "Items"
}
```

### [Lambda - GetFunction (non-paginated)](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/lambda/client/get_function.html)
```javascript
{
  "boto3_client_name": "lambda",             // Use boto3 client "lambda"
  "boto3_method_name": "get_function",       // Execute lambda client boto3 method "get_function"
  "boto3_method_kwargs": {                   // Specify lambda.get_function() parameters
    "FunctionName": "MyFunction"
  },
  "boto3_response_key": "Configuration",     // Store only the data within the response key "Configuration"
  "response_s3_bucket": "my-bucket",         // Response will be stored in s3 bucket "my-bucket"
  "response_s3_key": "path/to/response.json" // Response will be stored in s3 prefix "path/to/response.json"
}
```

## Example Response

```javascript
{
  "response_s3_uri": "s3://my-bucket/boto3-executor/2023/02/19/2933f454-71f3-4297-b0ac-81fccc410403.json",
  "response_s3_bucket": "my-bucket",
  "response_s3_key": "boto3-executor/2023/02/19/2933f454-71f3-4297-b0ac-81fccc410403.json"
}
```

## Invoking Event Payload Format

When invoking the Lambda function, the below keys can be provided in the event payload:

### `boto3_client_name`

Required. [Boto3 client name](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/index.html). Examples: `"ec2"`, `"dynamodb"`.

### `boto3_method_name`

Required. Boto3 client method. Examples: `"describe_vpcs"`, `"scan"`.

### `boto3_method_kwargs`

Optional. Method parameters in map/dictionary format. Examples: `{"VpcIds": ["vpc-aaaaaaaa"]}`, `{"TableName": "MyTable", "IndexName": "MyIndex"}`.

### `boto3_paginator_response_items_key`

Optional. If specified, the [Boto3 method will be executed using a paginator](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/paginators.html). The value should be the paginator response key including items to aggregate. Be sure to specify this to enable pagination, or else result sets from large lists will be incomplete. Examples: `"Vpcs"`, `"Items"`.

### `boto3_response_key`

Optional. For non-paginated methods, specify this value to filter down the response to a specific key. Examples: `"Vpcs", "Items"`.

### `response_s3_bucket`

Optional. S3 bucket name to store response in. Defaults to Lambda function environment variable `"RESPONSE_S3_BUCKET"`. Example: `"my-bucket"`

### `response_s3_key`

Optional. S3 bucket key / prefix to store response in. Defaults to Lambda function environment variable `"RESPONSE_S3_PREFIX"` + Lambda function name + `"/YYYY/MM/DD/` + `<lambda-request-id>.json`. Examples: `"my-response.json"`, `"path/to/my-response.json"`.

### `resonse_s3_body_json_indent`

Optional. Integer specifying number of spaces to use in JSON indents in saved S3 response file. [See `indent` arg in `json.dumps()`](https://docs.python.org/3.9/library/json.html#json.dumps). Defaults to Lambda function environment variable `"RESPONSE_S3_BODY_JSON_INDENT"`, which defaults to `2`. Specify `0` to save the JSON data on one line (most compact). Examples: `0`, `2`.

## Terraform Quickstart

To easily deploy this project, clone it and then deploy with [Terraform](https://developer.hashicorp.com/terraform/tutorials/aws-get-started/install-cli). [The Terraform AWS provider will use your active AWS credentials](https://registry.terraform.io/providers/hashicorp/aws/latest/docs#authentication-and-configuration). Note that [deploying the Lambda function requires Python in your `$PATH`](https://github.com/terraform-aws-modules/terraform-aws-lambda/#build).

```bash
git clone git@github.com:atheiman/boto3-executor-lambda.git
cd boto3-executor-lambda

terraform init
terraform apply

# Review the plan output and type 'yes' to apply the plan

# Print an AWS CLI command you can run to invoke the Lambda function
terraform output -raw cli_invoke_1

# Review the printed command, then run it to invoke the deployed Lambda function.

# The lambda response JSON includes `response_s3_uri`, which you can download to see the boto3 API response
cat ./lambda-response.json

# Download the boto3 API response
aws s3 cp <response_s3_uri> ./boto3-response-data.json

# The boto3 API response is big. Much too big to be retrieved directly in Step Functions or some other tools
ls -lh ./boto3-response-data.json
head ./boto3-response-data.json

# Destroy created infrastructure
terraform destroy
```
