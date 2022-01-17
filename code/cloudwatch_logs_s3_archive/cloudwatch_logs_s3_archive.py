"""Export CloudWatch Logs to S3 every 24 hours."""
import logging
import os
import time

import boto3

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
logs = boto3.client("logs")
ssm = boto3.client("ssm")

print(f"logs is : {logs}")
print(f"ssm is: {ssm}")


def lambda_handler(event, context):
    extra_args = {}
    log_groups = []
    log_groups_to_export = []

    if "S3_BUCKET" not in os.environ:
        logger.error("Error: S3_BUCKET environment variable not defined")
        raise Exception  # return False

    logger.debug("--> S3_BUCKET=%s" % os.environ["S3_BUCKET"])

    ACCOUNT_ID = os.environ["ACCOUNT_ID"]
    logger.debug("--> ACCOUNT_ID=%s", ACCOUNT_ID)

    while True:
        response = logs.describe_log_groups(**extra_args)
        log_groups = log_groups + response["logGroups"]

        if "nextToken" not in response:
            break
        extra_args["nextToken"] = response["nextToken"]

    for log_group in log_groups:
        log_groups_to_export.append(log_group["logGroupName"])

    for log_group_name in log_groups_to_export:
        ssm_parameter_name = ("/log-exporter-last-export/%s" % log_group_name).replace(
            "//", "/"
        )
        try:
            ssm_response = ssm.get_parameter(Name=ssm_parameter_name)
            ssm_value = ssm_response["Parameter"]["Value"]
        except ssm.exceptions.ParameterNotFound:
            ssm_value = "0"

        export_to_time = int(round(time.time() * 1000))

        logger.info("--> Exporting %s to %s" % (log_group_name, os.environ["S3_BUCKET"]))

        if export_to_time - int(ssm_value) < (24 * 60 * 60 * 1000):
            # Haven't been 24hrs from the last export of this log group
            logger.warning("    Skipped until 24hrs from last export is completed")
            continue

        try:
            response = logs.create_export_task(
                logGroupName=log_group_name,
                fromTime=int(ssm_value),
                to=export_to_time,
                destination=os.environ["S3_BUCKET"],
                destinationPrefix="%s/%s" % (ACCOUNT_ID, log_group_name.strip("/")),
            )
            logger.info("✔   Task created: %s" % response["taskId"])
            time.sleep(5)

        except logs.exceptions.LimitExceededException:
            logger.warning(
                "⚠   Too many concurrently running export tasks "
                "(LimitExceededException). Aborting..."
            )
            return False

        except Exception as e:
            logger.exception(
                "✖   Error exporting %s: %s"
                % (log_group_name, getattr(e, "message", repr(e)))
            )
            continue

        ssm_response = ssm.put_parameter(
            Name=ssm_parameter_name,
            Type="String",
            Value=str(export_to_time),
            Overwrite=True,
        )
