import boto3

def lambda_handler(event, context):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('trigger_codebuild_random')

    scan = table.scan()
    items = scan['Items']

    for item in items:
        key = {'id': item['id']}
        response = table.delete_item(Key=key)

        print(f"Deleted Item: {key}, response: {response}")

    return {
        'statusCode': 200,
        'body': f'Successfully Deleted {len(items)} items.'
    }
