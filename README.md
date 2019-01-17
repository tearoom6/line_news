# NotifyNewsToLine

Notify to LINE channel of latest news matched by keywords in Yahoo! Japan.

## Environments

- Python 2.7.10
- AWS Lambda
- Amazon API Gateway

## How to run

Install Python dependencies to local directory:

```sh
pip install pytz -t ./libs
pip install requests -t ./libs
pip install beautifulsoup4 -t ./libs
pip install feedparser -t ./libs
```

Setup AWS environment using CloudFormation:

```sh
S3_BUCKET="<BUCKET>"
FUNCTION_NAME="NotifyNewsToLine"
STACK_NAME="NotifyNewsToLine"
OPERATOR="<IAM_USER>"
KEY_ALIAS="LINE_NOTIFY_BEARER_TOKEN"
ENCRYPTED_TOKEN="<ENCRYPTED_TOKEN>"

# Package Lambda code and upload it to S3 bucket.
aws cloudformation package \
  --template-file cloudformation-template.yml \
  --s3-bucket $S3_BUCKET \
  --s3-prefix "Lambda/$FUNCTION_NAME" \
  --output-template-file packaged-template.yml

# Deploy all resources in AWS. (Also create CloudFormation stack)
aws cloudformation deploy \
  --template-file packaged-template.yml \
  --stack-name $STACK_NAME \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides "LineNotifyBearerTokenKeyAliasName=$KEY_ALIAS" "EncryptedLineNotifyBearerToken=$ENCRYPTED_TOKEN" "Operator=$OPERATOR"
```

Register LINE Token to KMS:

```sh
ACCOUNT_ID=`aws sts get-caller-identity | jq -r '.Account'`
KEY_ID=arn:aws:kms:ap-northeast-1:$ACCOUNT_ID:alias/$KEY_ALIAS
ORIGINAL_BEARER_TOKEN="<LINE_ACCESS_TOKEN>"

# Register (Encrypt) key.
# Replace Lambda's environment variable with this value.
ENCRYPTED_TOKEN=`aws kms encrypt --key-id $KEY_ID --plaintext $ORIGINAL_BEARER_TOKEN --query CiphertextBlob --output text`

# Decrypt key.
aws kms decrypt --ciphertext-blob fileb://<(echo $ENCRYPTED_TOKEN | base64 -D) --query Plaintext --output text | base64 -D
```

Execute:

```sh
curl -X POST -d "{\"keywords\":\"赤ちゃん,保育園,育児\", \"period\":\"1\"}" https://<API_ID>.execute-api.ap-northeast-1.amazonaws.com/prod/line_news
```

Cleanup:

```sh
# Destroy all resources in AWS. (Also delete CloudFormation stack)
aws cloudformation delete-stack --stack-name $STACK_NAME
```

