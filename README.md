# CloudWatch Logs S3 Achive

> _Archive CLoudWatch Logs to S3 on a Schedule_

## Install for local development including dependencies

`pip install --editable .`

## Test with `pytest`

```sh
pip install pytest
pytest code/cloudwatch_logs_s3_archive/test_mock_cloudwatch_logs_s3_archive.py`
```

## Lambda Environment Variables

This requires 2 environent variables to be configured on Lambda FUnction:

1. `S3_BUCKET`: name of s3 bucket
2. `ACCOUNT_ID`: 12-digit AWS account id

## S3 Bucket Policies

### Same Account

Use this policy for buckets in the same account as the logs

```json

{
    "Version": "2012-10-17",
    "Statement": [
      {
          "Action": "s3:GetBucketAcl",
          "Effect": "Allow",
          "Resource": "arn:aws:s3:::my-exported-logs",
          "Principal": { "Service": "logs.us-west-2.amazonaws.com" }
      },
      {
          "Action": "s3:PutObject" ,
          "Effect": "Allow",
          "Resource": "arn:aws:s3:::my-exported-logs/random-string/*",
          "Condition": { "StringEquals": { "s3:x-amz-acl": "bucket-owner-full-control" } },
          "Principal": { "Service": "logs.us-west-2.amazonaws.com" }
      }
    ]
}
```

### Different Account

Use this policy for buckets in a different account from the logs:

```json
{
    "Version": "2012-10-17",
    "Statement": [
      {
          "Action": "s3:GetBucketAcl",
          "Effect": "Allow",
          "Resource": "arn:aws:s3:::my-exported-logs",
          "Principal": { "Service": "logs.us-west-2.amazonaws.com" }
      },
      {
          "Action": "s3:PutObject" ,
          "Effect": "Allow",
          "Resource": "arn:aws:s3:::my-exported-logs/random-string/*",
          "Condition": { "StringEquals": { "s3:x-amz-acl": "bucket-owner-full-control" } },
          "Principal": { "Service": "logs.us-west-2.amazonaws.com" }
      },
      {
          "Action": "s3:PutObject" ,
          "Effect": "Allow",
          "Resource": "arn:aws:s3:::my-exported-logs/random-string/*",
          "Condition": { "StringEquals": { "s3:x-amz-acl": "bucket-owner-full-control" } },
          "Principal": { "AWS": "arn:aws:iam::SendingAccountID:user/CWLExportUser" }
      }
    ]
}
```

## Deploy to AWS

```sh
pip install aws-sam-cli
make build
make deploy
```

Automatically deploys Lambda function, IAM roles, and Event Bridge Schedule to run the Lambda periodically.
