import os
import json
import boto3
import botocore
from datetime import datetime

s3 = boto3.client("s3", region_name=os.environ["AWS_REGION"])


def lambda_handler(event, context):
    print(json.dumps(event, default=str))
    boto3_client_name = event["boto3_client_name"]
    boto3_method_name = event["boto3_method_name"]
    boto3_method_kwargs = event.get("boto3_method_kwargs", {})
    boto3_paginator_response_items_key = event.get("boto3_paginator_response_items_key")
    boto3_response_key = event.get("boto3_response_key")
    boto3_response_data = None
    boto3_client = boto3.client(boto3_client_name, region_name=os.environ["AWS_REGION"])

    # Get items from paginated API
    if boto3_paginator_response_items_key:
        print(f"Calling paginated API {boto3_client_name}.{boto3_method_name}")
        paginator = boto3_client.get_paginator(boto3_method_name)
        boto3_response_data = []
        pg_count = 0
        for pg in paginator.paginate(**boto3_method_kwargs):
            boto3_response_data += pg[boto3_paginator_response_items_key]
            pg_count += 1
            print(
                f"{boto3_client_name}.{boto3_method_name} response pages retrieved: {pg_count},"
                f" items count: {len(boto3_response_data)}"
            )

    # Get non-paginated API response
    else:
        if boto3_client.can_paginate(boto3_method_name):
            result_keys = [k.parsed["value"] for k in boto3_client.get_paginator(boto3_method_name).result_keys]
            print(
                f"Warning - API {boto3_client_name}.{boto3_method_name} can paginate, but"
                f" 'boto3_paginator_response_items_key' was not specified in event. Specify one of"
                f" {result_keys} to retrieve all results from this paginated API."
            )
        print(f"Calling API {boto3_client_name}.{boto3_method_name} without pagination")
        boto3_response_data = getattr(boto3_client, boto3_method_name)(**boto3_method_kwargs)
        if boto3_response_key:
            boto3_response_data = boto3_response_data[boto3_response_key]

    s3_bucket = event.get("response_s3_bucket")
    if not s3_bucket:
        s3_bucket = os.environ["RESPONSE_S3_BUCKET"]

    s3_key = event.get("response_s3_key")
    if not s3_key:
        s3_key = os.environ.get("RESPONSE_S3_PREFIX", "")
        s3_key += os.environ["AWS_LAMBDA_FUNCTION_NAME"]
        s3_key += datetime.now().strftime("/%Y/%m/%d/")
        s3_key += f"{context.aws_request_id}.json"

    json_indent = int(event.get("resonse_s3_body_json_indent", os.environ.get("RESPONSE_S3_BODY_JSON_INDENT", 2)))
    s3_body = json.dumps(boto3_response_data, default=str, indent=json_indent)

    s3_uri = f"s3://{s3_bucket}/{s3_key}"
    print(f"Putting boto3 api response data into S3 at {s3_uri}")
    s3.put_object(
        Bucket=s3_bucket,
        Key=s3_key,
        Body=s3_body,
    )

    return {
        "response_s3_uri": s3_uri,
        "response_s3_bucket": s3_bucket,
        "response_s3_key": s3_key,
    }
