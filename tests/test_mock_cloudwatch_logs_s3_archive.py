"""Test Cloud Watch Logs S3 Archive Python Lambda Function"""
import os
from time import time
from unittest import mock

import boto3
import moto
import pytest


@pytest.fixture
def f_aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    # cannot use us-east-1 with s3.create_bucket LocationConstraint
    os.environ["AWS_DEFAULT_REGION"] = "us-east-2"


@pytest.fixture
def logs(f_aws_credentials):
    with moto.mock_logs():
        yield boto3.client("logs")


@pytest.fixture
def ssm(f_aws_credentials):
    with moto.mock_ssm():
        yield boto3.client("ssm")


@pytest.fixture
def s3(f_aws_credentials):
    with moto.mock_s3():
        yield boto3.client("s3")


@pytest.fixture
def instance(logs, ssm):
    from src.cloudwatch_logs_s3_archive import CloudWatchLogsS3Archive

    return CloudWatchLogsS3Archive("bucket", "123412341234")


@pytest.fixture
def cwlog_resources(logs):
    logs.create_log_group(logGroupName="/moto/test/log/group")


@pytest.fixture
def s3_resources(s3):
    bucket = "moto_bucket"
    region = os.environ["AWS_DEFAULT_REGION"]
    s3.create_bucket(
        Bucket=bucket,
        CreateBucketConfiguration={"LocationConstraint": region},
    )
    return bucket


def test_get_a_generator_of_logs_groups(instance, logs, ssm):
    # ARRANGE
    logs.create_log_group(logGroupName="first")
    logs.create_log_group(logGroupName="second")
    logs.create_log_group(logGroupName="third")
    # instance = CloudWatchLogsS3Archive("bucket", 123412341234)
    # ACT
    log_groups = instance.collect_log_groups()
    # ASSERT
    assert next(log_groups) == "first"  # type: ignore
    assert next(log_groups) == "second"  # type: ignore
    assert next(log_groups) == "third"  # type: ignore


def test_get_last_export_time_from_ssm_parameter(ssm, instance):
    expected = str(round(time() * 1000))
    ssm.put_parameter(Name="/log-exporter-last-export/first", Value=expected)
    last_export_time = instance.get_last_export_time("first")
    assert last_export_time == expected


def test_set_start_time_zero_when_parameter_does_not_exist(instance):
    last_export_time = instance.get_last_export_time("/doesnotexist")
    assert last_export_time == "0"


def test_set_export_time(instance):
    assert pytest.approx(round(time() * 1000)) == instance.set_export_time()


def test_put_export_time(ssm, instance):
    put_time = 1642568042037
    instance.put_export_time("first", put_time)
    resp = ssm.get_parameter(Name="/log-exporter-last-export/first")
    actual = resp["Parameter"]["Value"]
    assert actual == str(put_time)


def test_create_export_tasks(ssm, logs, instance):
    log_group_name = "first"
    s3_bucket = "s3_bucket"
    account_id = 123412341234
    toTime = instance.put_export_time(
        "first",
        1642568042037,
    )
    fromTime = instance.get_last_export_time("first")
    with mock.patch.object( instance.logs, 'create_export_task', return_value={"taskId": "I am mocked via mock.Mock"} ):
        instance.create_export_tasks(
            "/log-exporter-last-export/first", fromTime, toTime, "s3_bucket", 123412341234
        )
        # assert instance.logs.create_export_task.called
    # instance.create_export_tasks("first", fromTime, toTime, "s3_bucket", 123412341234)
        assert instance.logs.create_export_task.called
        instance.logs.create_export_task.assert_called
    instance.logs.create_export_task.assert_called_with(
        logGroupName=log_group_name,
        fromTime=int(fromTime),
        to=toTime,
        destination=s3_bucket,
        destinationPrefix="{}/{}".format(account_id, log_group_name.strip("/")),
    )


def test_ssm_get_parameter_prefx_applied_to_log_group_name(ssm, logs, instance):
    log_group_name = "fourth"
    logs.create_log_group(logGroupName=log_group_name)
    toTime = instance.set_export_time()
    ssm.put_parameter(
        Name=f"/log-exporter-last-export/{log_group_name}", Value=str(toTime)
    )
    actual = instance.get_last_export_time(log_group_name)
    expected = toTime
    assert pytest.approx(actual) == str(expected)


def test_ssm_put_parameter_prefx_applied_to_log_group_name(ssm, logs, instance):
    log_group_name = "fifth"
    logs.create_log_group(logGroupName=log_group_name)
    toTime = instance.set_export_time()
    instance.put_export_time(log_group_name, toTime)
    resp = ssm.get_parameter(Name=f"/log-exporter-last-export/{log_group_name}")
    actual = resp["Parameter"]["Value"]
    expected = toTime
    assert pytest.approx(actual) == str(expected)


def test_prepend_prefix_automatically_to_log_group_name(instance):
    log_group_name = "/aws/codebuild/hugo-blog/"
    actual = instance._prepend_ssm_parameter_prefix(log_group_name)
    expected = instance.ssm_parameter_prefix + "aws/codebuild/hugo-blog/"
    assert actual == expected


@pytest.mark.skip
def test_lambda_handler_function_from_import(ssm, logs):
    from cloudwatch_logs_s3_archive import lambda_handler

    # import cloudwatch_logs_s3_archive

    event = context = {}
    os.environ["S3_BUCKET"] = "mybucket"
    os.environ["ACCOUNT_ID"] = "123412341234"

    lambda_handler(event, context)


def test_lambda_handler_function_import_bad_account_id(
    ssm, logs, cwlog_resources, s3_resources
):
    # from cloudwatch_logs_s3_archive import lambda_handler
    import src.cloudwatch_logs_s3_archive

    event = context = {}
    os.environ["S3_BUCKET"] = s3_resources
    os.environ["ACCOUNT_ID"] = "1"

    with pytest.raises(ValueError):
        src.cloudwatch_logs_s3_archive.lambda_handler(event, context)

