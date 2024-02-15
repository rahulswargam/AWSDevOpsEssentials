import boto3
import requests
import json
import base64
from datetime import datetime


codebuild = boto3.client('codebuild')
ses = boto3.client('ses')
logs = boto3.client('logs')
sns = boto3.client('sns')

def extract_environment_variable(build, key_name):
    env_vars = build['environment']['environmentVariables']
    for var in env_vars:
        if var['name'] == key_name:
            return var['value']
    return 'Unknown'

def get_instance_config_from_s3(client_name, instance_type):
    bucket_name = f"{client_name}-streamlyne-files-us-east-1"
    s3_key = f"config/{instance_type}.json"
    s3 = boto3.client('s3')
    
    try:
        response = s3.get_object(Bucket=bucket_name, Key=s3_key)
        data = json.loads(response['Body'].read())
        
        db_snapshot_source_instance = data.get('shared', {}).get('db_snapshot_source_instance', 'N/A') or 'N/A'
        etl_application_enabled = str(data.get('etl', {}).get('etl_application_enabled', 'N/A'))
        etl_v2_application_enabled = str(data.get('etl', {}).get('etl_v2_application_enabled', 'N/A'))
        application_version_override = data.get('shared', {}).get('application_version_override', 'false') or 'false'
        
        return db_snapshot_source_instance, etl_application_enabled, etl_v2_application_enabled, application_version_override
    except Exception as e:
        print(f"Error fetching data from S3: {e}")
        return 'N/A', 'N/A', 'N/A', 'false'

def get_base64_image(s3_bucket, build_status):
    status_to_image = {
        'SUCCEEDED': 'image-files/success.png',
        'FAILED': 'image-files/failure.png',
        'IN_PROGRESS': 'image-files/inprogress.png'
    }

    s3 = boto3.client('s3')
    s3_key = status_to_image.get(build_status)

    if not s3_key:
        return None

    file_obj = s3.get_object(Bucket=s3_bucket, Key=s3_key)
    file_content = file_obj['Body'].read()

    base64_image = base64.b64encode(file_content).decode('utf-8')
    return base64_image

def send_notification_to_teams(build, build_status, webhook_url, base64_image, aad_id, timestamp, status, client_name, instance_type, branch, recreate_snapshot, db_source, etl_enabled, etl_v2_enabled, app_version_override, log_link=None):
    color = "Good" if build_status == "SUCCEEDED" else "Accent" if build_status == "IN_PROGRESS" else "Attention"    

    details = [
        {"title": "Triggered by", "value": f"<at>{aad_id}</at>"},
        {"title": "Timestamp of Deploy", "value": timestamp},
        {"title": "Status", "value": status},
        {"title": "Client Name", "value": client_name},
        {"title": "Instance Type", "value": instance_type},
        {"title": "Branch", "value": branch},
        {"title": "Refresh Database", "value": recreate_snapshot},
        {"title": "Database Source", "value": db_source},
        {"title": "Deploy with ETL", "value": etl_enabled},
        {"title": "Deploy with ETLv2", "value": etl_v2_enabled},
        {"title": "Application Version Override", "value": app_version_override}
    ]
    
    if log_link:
        details.append({"title": "Build Logs", "value": f"[View Logs]({log_link})"})
    
    adaptive_card_content = {
        "type": "message",
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": {
                    "type": "AdaptiveCard",
                    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                    "version": "1.2",
                    "body": [
                        {
                            "type": "ColumnSet",
                            "columns": [
                                {
                                    "type": "Column",
                                    "width": "auto",
                                    "items": [
                                        {
                                            "type": "Image",
                                            "url": f"data:image/png;base64,{base64_image}",
                                            "size": "Medium",
                                            "style": "person"
                                        }
                                    ]
                                },
                                {
                                    "type": "Column",
                                    "width": "stretch",
                                    "items": [
                                        {
                                            "type": "RichTextBlock",
                                            "inlines": [
                                                {
                                                    "type": "TextRun",
                                                    "text": "Status of Latest Build: ",
                                                    "weight": "Bolder",
                                                    "size": "Large",
                                                    "style": "default"
                                                },
                                                {
                                                    "type": "TextRun",
                                                    "text": build_status.upper(),
                                                    "weight": "Bolder",
                                                    "size": "Large",
                                                    "color": color,
                                                    "style": "default"
                                                }
                                            ]
                                        },
                                        {
                                            "type": "TextBlock",
                                            "text": "Details of the CodeBuild Project:",
                                            "size": "medium",
                                            "style": "default"
                                        },
                                        {
                                            "type": "ColumnSet",
                                            "spacing": "Small",
                                            "columns": [
                                                {
                                                    "type": "Column",
                                                    "width": "50%",
                                                    "items": [
                                                        {"type": "TextBlock", "text": detail["title"], "wrap": True, "weight": "Bolder", "size": "Medium", "spacing": "Small", "horizontalAlignment": "left"}
                                                        for detail in details
                                                    ]
                                                },
                                                {
                                                    "type": "Column",
                                                    "width": "100%",
                                                    "items": [
                                                        {"type": "TextBlock", "text": ": " + detail["value"], "wrap": True, "size": "Medium", "spacing": "Small", "horizontalAlignment": "Left"}
                                                        for detail in details
                                                    ]
                                                }
                                            ]
                                        }
                                    ]
                                }
                            ]
                        }
                    ],
                    "msteams": {
                        "width": "Full",
                        "entities": [
                            {
                                "type": "mention",
                                "text": f"<at>{aad_id}</at>",
                                "mentioned": {
                                    "id": aad_id,
                                    "name": "Janior"
                                }
                            }
                        ]
                    }
                }
            }
        ]
    }

    response = requests.post(webhook_url, json=adaptive_card_content)
    print("Response from MS Teams:", response.status_code, response.text)
    return response.text

def send_failure_email(build, last_100_lines):
    environment_variables = build['environment']['environmentVariables']
    build_number = build['buildNumber']
    environment_name = extract_environment_variable(build, 'ENVIRONMENT_NAME')
    instance_name = extract_environment_variable(build, 'INSTANCE_NAME')

    subject = f"{environment_name} » {instance_name} - Build # {build_number} - Failed"
    message = f"{environment_name} » {instance_name} - Build # {build_number} - Failed\n\n\nHere are the last 100 lines of the logs of the CodeBuild Project:\n\n\n{last_100_lines}"

    ses.send_email(
        Source=f"alert@{environment_name}.streamlyne.org",
        Destination={'ToAddresses': ['rswargam@streamlyne.com']},
        Message={
            'Subject': {'Data': subject},
            'Body': {'Text': {'Data': message}}
        }
    )

def lambda_handler(event, context):
    print("Received event:", event)

    sns_message = json.loads(event['Records'][0]['Sns']['Message'])
    print("SNS Message:", sns_message)

    build_id = sns_message['detail']['build-id']
    print("CodeBuild Build ID:", build_id)

    build_details_response = codebuild.batch_get_builds(ids=[build_id])
    if not build_details_response or 'builds' not in build_details_response or not build_details_response['builds']:
        return {
            'statusCode': 400,
            'body': json.dumps('Error: Unable to fetch build details.')
        }

    build = build_details_response['builds'][0]
    timestamp = build['startTime'].strftime('%Y-%m-%d %H:%M:%S')
    status = build['buildStatus']
    client_name = extract_environment_variable(build, 'CLIENT_NAME')
    instance_type = extract_environment_variable(build, 'INSTANCE_TYPE')
    branch = build.get('sourceVersion', 'Unknown Branch')
    recreate_snapshot = extract_environment_variable(build, 'RECREATE_SOURCE_DB_SNAPSHOT')
    db_source, etl_enabled, etl_v2_enabled, app_version_override = get_instance_config_from_s3(client_name, instance_type)
    
    log_link = None 
    
    if status == "FAILED":
        log_link = build['logs']['deepLink']
        log_group_name = build['logs']['groupName']
        log_stream_name = build['logs']['streamName']
        log_events = logs.get_log_events(logGroupName=log_group_name, logStreamName=log_stream_name)
        logs_data = [event['message'] for event in log_events['events']]
        last_100_lines = "\n".join(logs_data[-100:])
        send_failure_email(build, last_100_lines)

    base64_image = get_base64_image(s3_bucket, status)

    if base64_image:
        
        if log_link:
            response = send_notification_to_teams(build, status, webhook_url, base64_image, aad_id, timestamp, status, client_name, instance_type, branch, recreate_snapshot, db_source, etl_enabled, etl_v2_enabled, app_version_override, log_link=log_link)
        else:
            response = send_notification_to_teams(build, status, webhook_url, base64_image, aad_id, timestamp, status, client_name, instance_type, branch, recreate_snapshot, db_source, etl_enabled, etl_v2_enabled, app_version_override)

        print(f"Notification sent for latest build with status {status}. Response: {response}")
    else:
        print(f"No image found for status: {status}")

    return {
        'statusCode': 200,
        'body': "Notification Sent."
    }

aad_id = 'f34efb9a'
s3_bucket = 'cicd-python-files'
webhook_url = 'https://vivantech.webhook.office.com/webhookb2/8cd21dc6-62ae-47e5-9772-259fdaf5c708@9794d907-c605-4910-9050-02b9980d3e7a/IncomingWebhook/806301631f9347b7aa58b7447904638c/b3691802-f075-45f0-9e42-47b02642f96c'