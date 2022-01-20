build:
	sam build --use-container --cached --parameter-overrides CloudWatchLogsArchiveBucket=$(BUCKET)
deploy:
	sam deploy \
	--resolve-s3 \
	--stack-name cloudwatch-logs-s3-archive \
	--capabilities CAPABILITY_IAM \
	--parameter-overrides CloudWatchLogsArchiveBucket=$(BUCKET)

test:
	pytest code/*/test_*.py
test-verbose:
	pytest --capture=no --verbose --log-cli-level=INFO code/*/test_*.py
