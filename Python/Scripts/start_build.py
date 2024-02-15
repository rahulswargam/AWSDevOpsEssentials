import json
import boto3
import requests

codebuild = boto3.client('codebuild')

def send_teams_notification(message):
    payload = {
        "@type": "MessageCard", 
        "@context": "http://schema.org/extensions", 
        "summary": "Build Notification", 
        "title": "Build Approval Status", 
        "text": message
    }
    response = requests.post(teams_webhook_url, data=json.dumps(payload), headers={'Content-Type': 'application/json'})
    return response

def lambda_handler(event, context):
    params = event.get('queryStringParameters', {})
    action = params.get('action')
    project_name = params.get('project_name')
    
    if action == 'approve' and project_name:
        try:
            codebuild.start_build(projectName=project_name)
            send_teams_notification(f"**Approved:** Build Started for Project **{project_name}**")
            return {'statusCode': 200, 'body': json.dumps('Build triggered successfully!')}
            
        except Exception as e:
            print("An error occurred:", str(e))
            send_teams_notification(f"Failed to Start Build: {project_name}")
            return {'statusCode': 500, 'body': json.dumps('Failed to start the build.')}
            
    elif action == 'decline' and project_name:
        
        send_teams_notification(f"**Declined:** Build will not Start for Project **{project_name}**")
        return {'statusCode': 200, 'body': json.dumps('Build declined.')}
    else:
        return {'statusCode': 400, 'body': json.dumps('Invalid action or missing project name.')}

teams_webhook_url = "https://vivantech.webhook.office.com/webhookb2/8cd21dc6-62ae-47e5-9772-259fdaf5c708@9794d907-c605-4910-9050-02b9980d3e7a/IncomingWebhook/806301631f9347b7aa58b7447904638c/b3691802-f075-45f0-9e42-47b02642f96c"