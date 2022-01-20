# CloudWatch Logs S3 Achive

> _Archive CLoudWatch Logs to S3 on a Schedule_

Install for local development including dependencies:

`pip install --editable .`

Test with `pytest`:

```sh
pip install pytest
pytest code/cloudwatch_logs_s3_archive/test_mock_cloudwatch_logs_s3_archive.py`
```

This requires 2 environent variables to be configured on Lambda FUnction:

1. `S3_BUCKET`: name of s3 bucket
2. `ACCOUNT_ID`: 12-digit AWS account id

Deploy to AWS:

```sh
pip install aws-sam-cli
make build
make deploy
```
