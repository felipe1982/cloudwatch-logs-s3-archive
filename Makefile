build:
	sam build --use-container --cached --parameter-overrides CloudWatchLogsArchiveBucket=$(BUCKET)
deploy:
	sam deploy \
	--resolve-s3 \
	--stack-name cloudwatch-logs-s3-archive \
	--capabilities CAPABILITY_IAM \
	--parameter-overrides CloudWatchLogsArchiveBucket=$(BUCKET)
delete:
	sam delete --stack-name cloudwatch-logs-s3-archive
test:
	pytest tests/test_*.py
test-verbose:
	pytest --capture=no --verbose --log-cli-level=INFO tests/test_*.py
