import boto3
import random
import os
from datetime import datetime

def lambda_handler(event, context):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('trigger_codebuild_random')
    today_date = datetime.now().strftime('%Y-%m-%d')

    # Retrieve the Details of Projects Triggered
    triggered_today = table.get_item(Key={'id': 'triggered_' + today_date}).get('Item')
    triggered_projects = triggered_today['projects'] if triggered_today else []

    projects_str = os.environ.get('PROJECTS', '')
    projects = projects_str.split(',')

    projects = [project for project in projects if project not in triggered_projects]

    if projects:
        selected_project = random.choice(projects)
        codebuild = boto3.client('codebuild')
        response = codebuild.start_build(projectName=selected_project)

        triggered_projects.append(selected_project)
        table.put_item(Item={'id': 'triggered_' + today_date, 'projects': triggered_projects})

        return {
            "message": f"Triggered Build for Project: {selected_project}",
            "buildId": response['build']['id'] if 'build' in response and 'id' in response['build'] else 'No Build ID'
        }
    else:
        return {
            "message": "There is no new CodeBuild Project left to Trigger"
        }
