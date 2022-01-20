from setuptools import setup


setup(
    name="cloudwatch-logs-s3-archive",
    version="0.1.0",
    description="Archive CLoudWatch Logs to S3 on a Schedule",
    author="Felipe Alvarez",
    author_email="felipe@example.com",
    packages=["cloudwatch_logs_s3_archive"],
    install_requires=["boto3", "botocore"],
    tests_require=["pytest", "boto3", "moto", "botocore"],
    licence="PUBLIC DOMAIN",
)
