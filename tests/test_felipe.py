"""Test Cloud Watch Logs S3 Archive Python Lambda Function"""
import os
from time import time
from unittest import mock

import boto3
import moto
import pytest


@pytest.fixture
def f_aws_credentials(autouse=True):
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"


@pytest.fixture
def logs(f_aws_credentials):
    with moto.mock_logs():
        yield boto3.client("logs")


@pytest.fixture
def ssm(f_aws_credentials):
    with moto.mock_ssm():
        yield boto3.client("ssm")

@pytest.fixture
def instance(logs, ssm):
    from src.cloudwatch_logs_s3_archive import CloudWatchLogsS3Archive
    return CloudWatchLogsS3Archive("bucket", "123412341234")


def test_describe_log_groups(logs, ssm):
    logs.create_log_group(logGroupName="felipe/log/group")
    print(logs.describe_log_groups())

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
