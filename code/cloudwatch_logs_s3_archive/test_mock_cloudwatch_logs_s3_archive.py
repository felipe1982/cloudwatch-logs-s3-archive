"""Test Cloud Watch Logs S3 Archive Python Lambda Function"""
import logging
import os
from unittest import mock

import boto3
import moto
import pytest

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


@pytest.fixture
def f_aws_credentials(autouse=True):
    """Mocked AWS Credentials for moto.

    This is a "side effect" function and None is returned because we are
    modifying the environment in which other downstream functions are excuting
    """
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"


def test_throw_TypeError_exception_with_invalid_or_insufficient_inputs():
    from cloudwatch_logs_s3_archive import CloudWatchLogsS3Archive

    with pytest.raises((TypeError)):
        c = CloudWatchLogsS3Archive()  # type: ignore
        c.check_valid_inputs()


@moto.mock_logs
def test_get_a_generator_of_logs_groups():
    # ARRANGE
    from cloudwatch_logs_s3_archive import CloudWatchLogsS3Archive

    logs = boto3.client("logs")
    logs.create_log_group(logGroupName="first")
    logs.create_log_group(logGroupName="second")
    logs.create_log_group(logGroupName="third")
    c = CloudWatchLogsS3Archive("bucket", 123412341234)
    # ACT
    log_groups = c.collect_log_groups()
    # ASSERT
    assert next(log_groups) == "first"  # type: ignore
    assert next(log_groups) == "second"  # type: ignore
    assert next(log_groups) == "third"  # type: ignore


@moto.mock_ssm
def test_get_last_export_time_from_ssm_parameter():
    from time import time

    from cloudwatch_logs_s3_archive import CloudWatchLogsS3Archive

    expected = str(round(time() * 1000))
    ssm = boto3.client("ssm")
    ssm.put_parameter(Name="/log-exporter-last-export/first", Value=expected)
    c = CloudWatchLogsS3Archive("bucket", "123412341234")
    last_export_time = c.get_last_export_time(Name="/log-exporter-last-export/first")
    assert last_export_time == expected


@moto.mock_ssm
def test_set_start_time_zero_when_parameter_does_not_exist():
    from cloudwatch_logs_s3_archive import CloudWatchLogsS3Archive

    c = CloudWatchLogsS3Archive("bucket", "123412341234")
    last_export_time = c.get_last_export_time(Name="/doesnotexist")
    assert last_export_time == "0"


def test_set_export_time():
    from cloudwatch_logs_s3_archive import CloudWatchLogsS3Archive

    c = CloudWatchLogsS3Archive("bucket", "123412341234")
    from time import time

    assert pytest.approx(round(time() * 1000)) == c.set_export_time()


@moto.mock_ssm
def test_put_export_time():
    from cloudwatch_logs_s3_archive import CloudWatchLogsS3Archive

    c = CloudWatchLogsS3Archive("bucket", "123412341234")
    put_time = 1642568042037
    c.put_export_time(
        put_time,
        Name="/log-exporter-last-export/first",
    )
    c.get_last_export_time(Name="/log-exporter-last-export/first")


@moto.mock_logs
@moto.mock_ssm
def test_create_export_tasks():
    from cloudwatch_logs_s3_archive import CloudWatchLogsS3Archive

    c = CloudWatchLogsS3Archive("bucket", "123412341234")
    # ssm = boto3.client("ssm")
    logs = boto3.client("logs")
    logs.create_log_group(logGroupName="/log-exporter-last-export/first")
    logs.create_log_group(logGroupName="/log-exporter-last-export/second")
    logs.create_log_group(logGroupName="/log-exporter-last-export/third")
    log_group_name = "/log-exporter-last-export/first"
    s3_bucket = "s3_bucket"
    account_id = 123412341234
    toTime = c.put_export_time(
        1642568042037,
        Name="/log-exporter-last-export/first",
    )
    fromTime = c.get_last_export_time(Name="/log-exporter-last-export/first")
    c.logs.create_export_task = mock.Mock(
        return_value={"taskId": "I am mocked via mock.Mock"}
    )
    c.create_export_tasks(
        "/log-exporter-last-export/first", fromTime, toTime, "s3_bucket", 123412341234
    )
    assert c.logs.create_export_task.called
    c.logs.create_export_task.assert_called
    c.logs.create_export_task.assert_called_with(
        logGroupName=log_group_name,
        fromTime=int(fromTime),
        to=toTime,
        destination=s3_bucket,
        destinationPrefix="{}/{}".format(account_id, log_group_name.strip("/")),
    )


def test_try_catch_LimitExceededException():
    ...


@moto.mock_logs
@moto.mock_s3
@moto.mock_ssm
def test_lambda_handler_function():
    from cloudwatch_logs_s3_archive import lambda_handler

    event = context = None
    os.environ["S3_BUCKET"] = "mybucket"
    os.environ["ACCOUNT_ID"] = "123412341234"

    lambda_handler(event, context)

