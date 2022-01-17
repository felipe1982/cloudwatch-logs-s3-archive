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
def f_os_environ():
    os.environ["S3_BUCKET"] = "mybucket2"
    os.environ["ACCOUNT_ID"] = "123412341234"


@pytest.fixture
def f_create_export_task():
    return {
        "logGroups": [
            {
                "logGroupName": "/aws/codebuild/hugo-blog",
                "creationTime": 1544587722233,
                "metricFilterCount": 0,
                "arn": "arn:aws:logs:ap-southeast-2:638088845137:log-group:/aws/codebuild/hugo-blog:*",  # noqa
                "storedBytes": 178,
            },
            {
                "logGroupName": "/aws/lambda/felipe-test-ServerlessFunction-KyEtQReUd8FA",
                "creationTime": 1642382703058,
                "metricFilterCount": 0,
                "arn": "arn:aws:logs:ap-southeast-2:638088845137:log-group:/aws/lambda/felipe-test-ServerlessFunction-KyEtQReUd8FA:*",  # noqa
                "storedBytes": 6877,
            },
        ],
        "ResponseMetadata": {
            "RequestId": "f303de04-8572-4667-8a29-6c42c0326cc9",
            "HTTPStatusCode": 200,
            "HTTPHeaders": {
                "x-amzn-requestid": "f303de04-8572-4667-8a29-6c42c0326cc9",
                "content-type": "application/x-amz-json-1.1",
                "content-length": "476",
                "date": "Tue, 18 Jan 2022 00:55:09 GMT",
            },
            "RetryAttempts": 0,
        },
    }


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


@moto.mock_ssm
@moto.mock_logs
def test_lambda_function(f_os_environ, f_aws_credentials, f_create_export_task):
    ##########################################################################
    # ARRANGE
    ##########################################################################
    import cloudwatch_logs_s3_archive

    os.environ["S3_BUCKET"] = "mybucket2"
    os.environ["ACCOUNT_ID"] = "123412341234"
    logs = boto3.client("logs")
    logs.create_log_group(logGroupName="mock_my_log_group_name")
    ##########################################################################
    # ACTIONS
    ##########################################################################
    with mock.patch(
        target="cloudwatch_logs_s3_archive.logs.create_export_task",
        return_value={"taskId": "I am mocked via mock.patch"},
        autospec=True,
    ) as create_export_task:
        # logs.create_export_task() isn't implemented yet in mock_logs, so
        # we resort to using unittest.mock.patch for this.
        # http://docs.getmoto.org/en/latest/docs/services/logs.html
        #
        # patch("autospec=True"): This causes any mocks to raise an exception if a
        # method, function, property, or attribute of the object being mocked does not
        # exist in the original object.
        # https://docs.python.org/3/library/unittest.mock.html#auto-speccing
        #
        cloudwatch_logs_s3_archive.lambda_handler(None, None)
    ##########################################################################
    # ASSERTIONS
    ##########################################################################
    assert os.getenv("S3_BUCKET")
    assert os.getenv("S3_BUCKET") is not None
    logger.info("call count is: {}".format(create_export_task.call_count))
    logger.info("call_args is: {}".format(create_export_task.call_args))
    logger.info("call_args_list is : {}".format(create_export_task.call_args_list))
    create_export_task.assert_called_once()


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
