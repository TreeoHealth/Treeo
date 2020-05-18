import boto3

dynamo_client = boto3.client('dynamodb')

def get_items():
    return dynamo_client.scan(
        TableName='YourTestTable'
    )
