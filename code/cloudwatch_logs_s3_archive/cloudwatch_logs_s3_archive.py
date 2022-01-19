"""Export CloudWatch Logs to S3 every 24 hours."""
import logging
import os
from time import time
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
# logs = boto3.client("logs")
# ssm = boto3.client("ssm")


class CloudWatchLogsS3Archive:
    botocore_config = Config(retries={"max_attempts": 10, "mode": "adaptive"})
    logs = boto3.client("logs", config=botocore_config)
    ssm = boto3.client("ssm", config=botocore_config)

    def __init__(self, s3_bucket, account_id) -> None:
        self.s3_bucket = s3_bucket
        self.account_id = account_id
        self.extra_args = {}
        self.log_groups = []
        self.log_groups_to_export = []

    def check_valid_inputs(self):
        """Check that required inputs are present and valid"""
        if len(self.account_id) != 12:
            logging.error("Account Id must be valid 12-digit AWS account id")
            raise ValueError("Account Id must be valid 12-digit AWS account id")

    def collect_log_groups_list(self):
        """Capture the names of all of the CloudWatch Log Groups"""
        paginator = self.__class__.logs.get_paginator("describe_log_groups")
        page_it = paginator.paginate()
        for p in page_it:
            return (lg["logGroupName"] for lg in p["logGroups"])  # type: ignore

    def get_last_export_time(self, Name) -> str:
        """Get time of the last export from SSM Parameter Store"""
        try:
            return self.__class__.ssm.get_parameter(Name=Name)["Parameter"]["Value"]
        except (self.__class__.ssm.exceptions.ParameterNotFound, ClientError) as exc:
            logger.warning(*exc.args)
            if exc.response["Error"]["Code"] == "ParameterNotFound":  # type: ignore
                return "0"
            else:
                raise

    def set_export_time(self):
        """Set current export time"""

        return round(time() * 1000)

    def put_export_time(self, put_time, Name):
        """Put current export time to SSM Parameter Store"""
        self.__class__.ssm.put_parameter(Name=Name, Value=str(put_time))

    def create_export_tasks(
        self, log_group_name, fromTime, toTime, s3_bucket, account_id
    ):
        """Create new CloudWatchLogs Export Tasks"""
        # try:
        response = self.__class__.logs.create_export_task(
            logGroupName=log_group_name,
            fromTime=int(fromTime),
            to=toTime,
            destination=s3_bucket,
            destinationPrefix="{}/{}".format(account_id, log_group_name.strip("/")),
        )
        logger.info("✔   Task created: %s" % response["taskId"])
        # except logs.exceptions.LimitExceededException:
        #     """The Boto3 standard retry mode will catch throttling errors and
        #     exceptions, and will back off and retry them for you."""
        #     logger.warning(
        #         "⚠   Too many concurrently running export tasks "
        #         "(LimitExceededException); backing off and retrying..."
        #     )
        #     return False
        # except Exception as e:
        #     logger.exception(
        #         "✖   Error exporting %s: %s",
        #         log_group_name,
        #         getattr(e, "message", repr(e)),
        #     )

        # ssm_response = self.__class__.ssm.put_parameter(
        #     Name=ssm_parameter_name,
        #     Type="String",
        #     Value=str(export_to_time),
        #     Overwrite=True,
        # )


def lambda_handler(event, context):
    os.environ["S3_BUCKET"] = "mybucket2"
    os.environ["ACCOUNT_ID"] = "123412341234"
