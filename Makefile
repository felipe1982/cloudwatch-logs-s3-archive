build:
	sam build --use-container
deploy:
	sam deploy \
	--resolve-s3 \
	--stack-name cloudwatch-logs-s3-archive \
	--parameter-overrides CloudWatchLogsArchiveBucket=${BUCKET}
