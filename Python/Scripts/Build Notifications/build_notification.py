import boto3
import requests
import os
import json
import base64
from datetime import datetime

codebuild = boto3.client('codebuild')
logs = boto3.client('logs')
ses = boto3.client('ses')

def get_base64_image(build_status):
    status_to_image = {
        'SUCCEEDED': 'build_status_images/success.png',
        'FAILED': 'build_status_images/failed.png',
    }

    s3 = boto3.client('s3')
    s3_bucket = "streamlyne-cicd"
    s3_key = status_to_image.get(build_status)

    if not s3_key:
        return None

    file_obj = s3.get_object(Bucket=s3_bucket, Key=s3_key)
    file_content = file_obj['Body'].read()

    base64_image = base64.b64encode(file_content).decode('utf-8')
    return base64_image

def send_notification_to_teams(build, build_status, base64_image, log_link=None):
    env_vars = build['environment']['environmentVariables']
    client_name = next((item['value'] for item in env_vars if item['name'] == 'CLIENT_NAME'), 'Unknown')
    instance_type = next((item['value'] for item in env_vars if item['name'] == 'INSTANCE_TYPE'), 'Unknown')
    timestamp = build['endTime'].strftime('%Y-%m-%d %H:%M:%S') if isinstance(build['endTime'], datetime) else build['endTime']
    color = "good" if build_status == "SUCCEEDED" else "attention"
    webhook_url = os.environ.get('TEAMS_WEBHOOK_URL')

    build_details_items = [
        {"type": "TextBlock", "text": "Client Name", "weight": "Bolder"},
        {"type": "TextBlock", "text": "Instance Type", "weight": "Bolder", "spacing": "Small"},
        {"type": "TextBlock", "text": "Timestamp of Deploy", "weight": "Bolder", "spacing": "Small"}
    ]
    build_details_values = [
        {"type": "TextBlock", "text": ":", "weight": "Bolder", "spacing": "Small"},
        {"type": "TextBlock", "text": ":", "weight": "Bolder", "spacing": "Small"},
        {"type": "TextBlock", "text": ":", "weight": "Bolder", "spacing": "Small"}
    ]
    build_details_data = [
        {"type": "TextBlock", "text": client_name, "spacing": "Small"},
        {"type": "TextBlock", "text": instance_type, "spacing": "Small"},
        {"type": "TextBlock", "text": timestamp, "spacing": "Small"}
    ]

    if build_status == "FAILED" and log_link:
        build_log_item = {"type": "TextBlock", "text": f"[View Logs]({log_link})", "spacing": "Small"}
        build_details_items.append({"type": "TextBlock", "text": "Build Logs", "weight": "Bolder", "spacing": "Small"})
        build_details_values.append({"type": "TextBlock", "text": ":", "weight": "Bolder", "spacing": "Small"})
        build_details_data.append(build_log_item)

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
                                            "columns": [
                                                {
                                                    "type": "Column",
                                                    "width": "auto",
                                                    "items": build_details_items
                                                },
                                                {
                                                    "type": "Column",
                                                    "width": "auto",
                                                    "items": build_details_values
                                                },
                                                {
                                                    "type": "Column",
                                                    "width": "stretch",
                                                    "items": build_details_data
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
                        "entities": [ ]
                    }
                }
            }
        ]
    }

    response = requests.post(webhook_url, json=adaptive_card_content)
    print("Response from MS Teams:", response.status_code, response.text)
    return response.text

def send_status_email(build, last_50_lines, status):
    environment_variables = build['environment']['environmentVariables']
    build_number = build['buildNumber']
    client_name = extract_environment_variable(build, 'CLIENT_NAME')
    instance_type = extract_environment_variable(build, 'INSTANCE_TYPE')

    subject = f"{client_name} » {instance_type} - Build # {build_number} - {status}"
    if status in ["FAILED", "STOPPED"]:
        message = f"{subject}\n\n\nHere are the last 50 lines of the CodeBuild Project Build Log:\n\n\n{last_50_lines}"
    else:
        message = f"{client_name} » {instance_type} - Build # {build_number} - {status}"

    ses = boto3.client('ses')
    ses.send_email(
        Source=f"alert@{client_name}.streamlyne.org",
        Destination={'ToAddresses': ['DevOps@streamlyne.org']},
        Message={
            'Subject': {'Data': subject},
            'Body': {'Text': {'Data': message}}
        }
    )

def extract_environment_variable(build, key_name):
    env_vars = build['environment']['environmentVariables']
    for var in env_vars:
        if var['name'] == key_name:
            return var['value']
    return 'Unknown'

def lambda_handler(event, context):
    print("Received event:", event)

    sns_message = json.loads(event.get('Records', [{}])[0].get('Sns', {}).get('Message', '{}'))
    build_id = sns_message.get('detail', {}).get('build-id', event.get('detail', {}).get('build-id'))

    build_details_response = codebuild.batch_get_builds(ids=[build_id])
    if not build_details_response or 'builds' not in build_details_response or not build_details_response['builds']:
        return {
            'statusCode': 400,
            'body': json.dumps('Error: Unable to fetch current build details.')
        }

    current_build = build_details_response['builds'][0]
    current_build_status = current_build['buildStatus']

    base64_image = get_base64_image(current_build_status)
    log_link = current_build['logs']['deepLink'] if current_build_status == "FAILED" else None
    if base64_image:
        send_notification_to_teams(current_build, current_build_status, base64_image, log_link)

    latest_build_response = codebuild.list_builds_for_project(
        projectName=current_build['projectName'],
        sortOrder='DESCENDING'
    )
    if not latest_build_response or 'ids' not in latest_build_response or not latest_build_response['ids']:
        return {
            'statusCode': 400,
            'body': json.dumps('Error: Unable to fetch latest build details.')
        }

    latest_build_ids = latest_build_response['ids']
    latest_build_details_response = codebuild.batch_get_builds(ids=latest_build_ids[:2])
    if 'builds' not in latest_build_details_response or not latest_build_details_response['builds']:
        return {
            'statusCode': 400,
            'body': json.dumps('Error: Unable to fetch latest build details.')
        }

    latest_build_details = latest_build_details_response['builds']
    latest_build_status = latest_build_details[1]['buildStatus'] if len(latest_build_ids) > 1 else None

    if current_build_status in ["FAILED", "STOPPED"]:
        log_events = logs.get_log_events(logGroupName=current_build['logs']['groupName'], logStreamName=current_build['logs']['streamName'])
        logs_data = [event['message'] for event in log_events['events']]
        last_50_lines = "\n".join(logs_data[-50:])
        send_status_email(current_build, last_50_lines, current_build_status)
    elif latest_build_status == "FAILED" and current_build_status == "SUCCEEDED":
        send_status_email(current_build, "", "SUCCEEDED")

    return {
        'statusCode': 200,
        'body': json.dumps(f"Notifications Sent Successfully. Build Status: {current_build_status}")
    }
