"""Test Cloud Watch Logs S3 Archive Python Lambda Function"""

import logging
import os
from unittest import mock

import boto3
import moto
import pytest

from cloudwatch_logs_s3_archive import CloudWatchLogsS3Archive

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


@pytest.fixture
def f_env_vars():
    os.environ["S3_BUCKET"] = "mybucket2"
    os.environ["ACCOUNT_ID"] = "123412341234"


@pytest.fixture
def f_aws_credentials():
    """Mocked AWS Credentials for moto.

    This is a "side effect" function and None is returned because we are
    modifying the environment in which other downstream functions are excuting
    """
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"


def test_throw_exception_with_invalid_or_insufficient_inputs():
    with pytest.raises((NameError, ValueError, TypeError)):
        c = CloudWatchLogsS3Archive()  # type: ignore
        c.check_valid_inputs()


@moto.mock_logs
def test_get_a_generator_of_logs_groups():
    # ARRANGE
    logs = boto3.client("logs")
    logs.create_log_group(logGroupName="first")
    logs.create_log_group(logGroupName="second")
    logs.create_log_group(logGroupName="third")
    c = CloudWatchLogsS3Archive("bucket", 123412341234)
    # ACT
    log_groups = c.collect_log_groups_list()
    # ASSERT
    assert next(log_groups) == "first"  # type: ignore
    assert next(log_groups) == "second"  # type: ignore
    assert next(log_groups) == "third"  # type: ignore


@moto.mock_ssm
def test_get_last_export_time_from_ssm_parameter():
    from time import time

    expected = str(round(time() * 1000))
    ssm = boto3.client("ssm")
    ssm.put_parameter(Name="/log-exporter-last-export/first", Value=expected)
    c = CloudWatchLogsS3Archive("bucket", "123412341234")
    last_export_time = c.get_last_export_time(Name="/log-exporter-last-export/first")
    assert last_export_time == expected


@moto.mock_ssm
def test_set_start_time_zero_when_parameter_does_not_exist():
    c = CloudWatchLogsS3Archive("bucket", "123412341234")
    last_export_time = c.get_last_export_time(Name="/doesnotexist")
    assert last_export_time == "0"


def test_set_export_time():
    c = CloudWatchLogsS3Archive("bucket", "123412341234")
    from time import time

    assert pytest.approx(round(time() * 1000)) == c.set_export_time()


@moto.mock_ssm
def test_put_export_time():
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
    c = CloudWatchLogsS3Archive("bucket", "123412341234")
    # ssm = boto3.client("ssm")
    logs = boto3.client("logs")
    logs.create_log_group(logGroupName="/log-exporter-last-export/first")
    logs.create_log_group(logGroupName="/log-exporter-last-export/second")
    logs.create_log_group(logGroupName="/log-exporter-last-export/third")
    toTime = c.put_export_time(
        1642568042037,
        Name="/log-exporter-last-export/first",
    )
    fromTime = c.get_last_export_time(Name="/log-exporter-last-export/first")

    with mock.patch(
        target="cloudwatch_logs_s3_archive.CloudWatchLogsS3Archive.logs",
        return_value={"taskId": "I am mocked via mock.patch"},
        autospec=True,
    ):
        c.create_export_tasks(
            "/log-exporter-last-export/first", fromTime, toTime, "s3_bucket", 123412341234
        )
#         target="cloudwatch_logs_s3_archive.CloudWatchLogsS3Archive.create_export_tasks",


def test_try_catch_LimitExceededException():
    ...


##############################################################################

# TODO
# assert called_with(destination='mybucket2',
#                     destinationPrefix='123412341234/mock_my_log_group_name',
#                     fromTime=0,
#                     logGroupName='mock_my_log_group_name',
#                     to=1642488495636)

# TODO assert ssm parameter for "fromTime" is present, and shows up in the
# code, in the call to "create_export_task"

# TODO
# expected_calls = [call(...), call("pos1", "pos2", ID=1234, Name="felipe")]
# investiage self.assert_has_calls(expected_calls)


# # THIS IS FAILING : TODO: create_export_task.assert_any_call()
# #
# # MagicMock Methods
# #
# LOGS = mock.MagicMock()
# # LOGS.assert_called()  (self.call_count == 0; raise AssertionError)
# # LOGS.assert_has_calls()  # Required parameters
# # LOGS.assert_any_call()  # raise AssertionError
# LOGS.call_count  # int
# LOGS.call_args  # Any
# LOGS.call_args_list  # _Call_List
# # LOGS.called  # bool (self.call_count == 0; raise AssertionError)
