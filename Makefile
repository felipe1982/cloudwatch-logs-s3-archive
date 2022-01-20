build:
	sam build --use-container
deploy:
	sam deploy \
	--resolve-s3 \
	--stack-name cloudwatch-logs-s3-archive \
	--capabilities CAPABILITY_IAM \
	--parameter-overrides CloudWatchLogsArchiveBucket=${BUCKET}
