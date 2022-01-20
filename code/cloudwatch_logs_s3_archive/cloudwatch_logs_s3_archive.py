"""Export CloudWatch Logs to S3 every 24 hours."""
import logging
import os
from time import time

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class CloudWatchLogsS3Archive:
    botocore_config = Config(retries={"max_attempts": 10, "mode": "adaptive"})

    def __init__(self, s3_bucket, account_id) -> None:
        self.s3_bucket = s3_bucket
        self.account_id = account_id
        self.extra_args = {}
        self.log_groups = []
        self.log_groups_to_export = []
        self.logs = boto3.client("logs", config=self.botocore_config)
        self.ssm = boto3.client("ssm", config=self.botocore_config)
        self.ssm_parameter_prefix = "/log-exporter-last-export/"

    def check_valid_inputs(self):
        """Check that required inputs are present and valid"""
        if len(self.account_id) != 12:
            logging.error("Account Id must be valid 12-digit AWS account id")
            raise ValueError("Account Id must be valid 12-digit AWS account id")

    def collect_log_groups(self):
        """Capture the names of all of the CloudWatch Log Groups"""
        paginator = self.logs.get_paginator("describe_log_groups")
        page_it = paginator.paginate()
        for p in page_it:
            for lg in p["logGroups"]:
                yield lg["logGroupName"]  # type: ignore

    def get_last_export_time(self, logGroupName) -> str:
        """Get time of the last export from SSM Parameter Store"""
        try:
            resp = self.ssm.get_parameter(
                Name=self.prepend_ssm_parameter_prefix(logGroupName)
            )
            return resp["Parameter"]["Value"]

        except (self.ssm.exceptions.ParameterNotFound, ClientError) as exc:
            logger.warning(*exc.args)
            if exc.response["Error"]["Code"] == "ParameterNotFound":  # type: ignore
                return "0"
            else:
                raise

    @staticmethod
    def set_export_time():
        """Set current export time"""
        return round(time() * 1000)

    def put_export_time(self, logGroupName, Value):
        """Put current export time to SSM Parameter Store"""
        self.ssm.put_parameter(
            Name=self.prepend_ssm_parameter_prefix(logGroupName),
            Value=str(Value),
            Overwrite=True,
        )

    def create_export_tasks(
        self, log_group_name, fromTime, toTime, s3_bucket, account_id
    ):
        """Create new CloudWatchLogs Export Tasks"""
        try:
            response = self.logs.create_export_task(
                logGroupName=log_group_name,
                fromTime=int(fromTime),
                to=toTime,
                destination=s3_bucket,
                destinationPrefix="{}/{}".format(account_id, log_group_name.strip("/")),
            )
            self.put_export_time(log_group_name, toTime)
            logger.info("✔   Task created: %s" % response["taskId"])
        except self.logs.exceptions.LimitExceededException:
            """The Boto3 standard retry mode will catch throttling errors and
            exceptions, and will back off and retry them for you."""
            logger.warning(
                "⚠   Too many concurrently running export tasks "
                "(LimitExceededException); backing off and retrying..."
            )
            # return False
        except Exception as e:
            logger.exception(
                "✖   Error exporting %s: %s",
                log_group_name,
                getattr(e, "message", repr(e)),
            )

    def prepend_ssm_parameter_prefix(self, *args: str):
        result = self.ssm_parameter_prefix + ''.join(args)
        return result.replace("//", "/")


def lambda_handler(event: dict, context: dict):
    s3_bucket = os.environ["S3_BUCKET"]
    account_id = os.environ["ACCOUNT_ID"]
    c = CloudWatchLogsS3Archive(s3_bucket, account_id)
    c.check_valid_inputs()
    log_groups = c.collect_log_groups()
    for log_group_name in log_groups:
        fromTime = c.get_last_export_time(log_group_name)
        toTime = c.set_export_time()
        c.create_export_tasks(log_group_name, fromTime, toTime, s3_bucket, account_id)
