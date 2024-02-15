import pymysql
import os
import requests
import json

def send_message_to_teams(client_name, instance_type, request_timestamp, deployed_by, deployer_object_id, project_name, lambda_function_url, config_values):
    teams_webhook_url = os.environ['TEAMS_WEBHOOK_URL']
    headers = {"Content-Type": "application/json"}
    
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
                            "type": "TextBlock",
                            "text": "Deployment Approval Request",
                            "size": "Large",
                            "weight": "Bolder",
                            "color": "Accent"
                        },
                        {
                            "type": "ColumnSet",
                            "columns": [
                                {
                                    "type": "Column",
                                    "width": "auto",
                                    "items": [
                                        {"type": "TextBlock", "text": "Last Deployer", "weight": "Bolder", "spacing": "Small"},                                        
                                        {"type": "TextBlock", "text": "Client Name", "weight": "Bolder"},
                                        {"type": "TextBlock", "text": "Instance Type", "weight": "Bolder", "spacing": "Small"},
                                        {"type": "TextBlock", "text": "Timestamp of Deploy", "weight": "Bolder", "spacing": "Small"},
                                        {"type": "TextBlock", "text": "ETL Automation", "weight": "Bolder", "spacing": "Small"},
                                        {"type": "TextBlock", "text": "ETL V2 App", "weight": "Bolder", "spacing": "Small"},
                                        {"type": "TextBlock", "text": "Version Category", "weight": "Bolder", "spacing": "Small"},
                                        {"type": "TextBlock", "text": "App Version Override", "weight": "Bolder", "spacing": "Small"}
                                    ]
                                },
                                {
                                    "type": "Column",
                                    "width": "auto",
                                    "items": [
                                        {"type": "TextBlock", "text": ":", "weight": "Bolder"},
                                        {"type": "TextBlock", "text": ":", "weight": "Bolder", "spacing": "Small"},
                                        {"type": "TextBlock", "text": ":", "weight": "Bolder", "spacing": "Small"},
                                        {"type": "TextBlock", "text": ":", "weight": "Bolder", "spacing": "Small"},
                                        {"type": "TextBlock", "text": ":", "weight": "Bolder", "spacing": "Small"},
                                        {"type": "TextBlock", "text": ":", "weight": "Bolder", "spacing": "Small"},
                                        {"type": "TextBlock", "text": ":", "weight": "Bolder", "spacing": "Small"},
                                        {"type": "TextBlock", "text": ":", "weight": "Bolder", "spacing": "Small"}
                                    ]
                                },
                                {
                                    "type": "Column",
                                    "width": "stretch",
                                    "items": [
                                        {"type": "TextBlock", "text": f"<at>{deployed_by}</at>", "spacing": "Small"},
                                        {"type": "TextBlock", "text": f"{client_name}", "spacing": "Small"},
                                        {"type": "TextBlock", "text": f"{instance_type}", "spacing": "Small"},
                                        {"type": "TextBlock", "text": f"{request_timestamp}", "spacing": "Small"},
                                        {"type": "TextBlock", "text": f"{config_values.get('etl_automation_enabled', 'N/A')}", "spacing": "Small"},
                                        {"type": "TextBlock", "text": f"{config_values.get('etl_v2_application_enabled', 'N/A')}", "spacing": "Small"},
                                        {"type": "TextBlock", "text": f"{config_values.get('version_category', 'N/A')}", "spacing": "Small"},
                                        {"type": "TextBlock", "text": f"{config_values.get('application_version_override', 'N/A')}", "spacing": "Small"}
                                    ]
                                }
                            ]
                        }
                    ],
                    "actions": [
                        {
                            "type": "Action.OpenUrl",
                            "title": "Approve",
                            "url": f"{lambda_function_url}?action=approve&project_name={project_name}",
                            "role": "Button",
                            "style": "positive"
                        },
                        {
                            "type": "Action.OpenUrl",
                            "title": "Decline",
                            "url": f"{lambda_function_url}?action=decline&project_name={project_name}",
                            "role": "Button",
                            "style": "destructive"
                        }
                    ],
                    "msteams": {
                        "width": "Full",
                        "entities": [
                            {
                                "type": "mention",
                                "text": f"<at>{deployed_by}</at>",
                                "mentioned": {
                                    "id": deployer_object_id,
                                    "name": deployed_by
                                }
                            }
                        ]
                    }
                }
            }
        ]
    }

    response = requests.post(teams_webhook_url, headers=headers, json=adaptive_card_content)
    
    if response.status_code != 200:
        print(f"Failed to send message to Teams. Status Code: {response.status_code}, Response: {response.text}")

def extract_config_values(config_json, default_values=None):
   
    keys_of_interest = {
        'etl_automation_enabled': ('etl', 'etl_automation_enabled'),
        'etl_v2_application_enabled': ('etl', 'etl_v2_application_enabled'),
        'version_category': ('shared', 'version_category'),
        'application_version_override': ('shared', 'application_version_override')
    }

    if default_values is None:
        default_values = {key: 'N/A' for key in keys_of_interest}
    
    extracted_values = default_values.copy()

    if isinstance(config_json, str):
        config = json.loads(config_json) if config_json else {}
    else:
        config = config_json

    for key, path in keys_of_interest.items():
        nested_config = config

        for step in path:
            if isinstance(nested_config, dict):
                nested_config = nested_config.get(step, {})
            else:
                nested_config = None
                break

        if nested_config is not None and not isinstance(nested_config, dict):
            extracted_values[key] = nested_config

    return extracted_values


def lambda_handler(event, context):
    host = os.environ['DB_HOST']
    user = os.environ['DB_USERNAME']
    password = os.environ['DB_PASSWORD']
    db_name = os.environ['DB_NAME']
    
    deployment_table = 'self_service_app_codebuilddeployment'
    user_table = 'self_service_app_sluser'
    lambda_function_url = os.environ.get('LAMBDA_FUNCTION_URL')

    connection = pymysql.connect(host=host, user=user, password=password, database=db_name, cursorclass=pymysql.cursors.DictCursor)

    try:
        with connection:
            with connection.cursor() as cursor:
                query = f"""
                    SELECT client_name, instance_type, request_timestamp, user_id 
                    FROM {deployment_table} 
                    ORDER BY request_timestamp DESC 
                    LIMIT 1
                """
                cursor.execute(query)
                latest_deployment = cursor.fetchone()

                if latest_deployment:
                    latest_deployment['request_timestamp'] = latest_deployment['request_timestamp'].isoformat()
                    deployer_name = None
                    deployer_object_id = None

                    query = f"""
                        SELECT u.first_name, u.sso_object_id
                        FROM {user_table} u
                        JOIN {deployment_table} d ON u.id = d.user_id
                        WHERE d.client_name = %s AND d.instance_type = %s AND d.request_timestamp < %s
                        ORDER BY d.request_timestamp DESC
                        LIMIT 1
                    """
                    cursor.execute(query, (latest_deployment['client_name'], latest_deployment['instance_type'], latest_deployment['request_timestamp']))
                    previous_deployer = cursor.fetchone()

                    if previous_deployer:
                        deployer_name = previous_deployer['first_name']
                        deployer_object_id = previous_deployer['sso_object_id']
                    else:
                        query = f"""
                            SELECT first_name, sso_object_id
                            FROM {user_table} 
                            WHERE id = %s
                        """
                        cursor.execute(query, (latest_deployment['user_id'],))
                        current_deployer = cursor.fetchone()
                        if current_deployer:
                            deployer_name = current_deployer['first_name']
                            deployer_object_id = current_deployer['sso_object_id']
                        else:
                            deployer_name = "Unknown"
                            deployer_object_id = None

                    project_type = "dev"
                    client_name = latest_deployment['client_name']
                    instance_type = latest_deployment['instance_type']
                    project_name = f"{project_type}_{client_name}_{instance_type}_deploy"
                    
                    query = f"""
                        SELECT original_deploy_config, updated_deploy_config 
                        FROM {deployment_table} 
                        WHERE client_name = %s AND instance_type = %s
                        ORDER BY request_timestamp DESC 
                        LIMIT 1
                    """
                    cursor.execute(query, (client_name, instance_type))
                    config_result = cursor.fetchone()

                    if config_result:
                
                        updated_config = json.loads(config_result['updated_deploy_config']) if config_result['updated_deploy_config'] else {}
                        original_config = json.loads(config_result['original_deploy_config']) if config_result['original_deploy_config'] else {}
                
                        config_values = extract_config_values(config_result['updated_deploy_config'])
                        original_config_values = extract_config_values(config_result['original_deploy_config'])
                
                        for key in original_config_values:
                            if key not in config_values or config_values[key] in [None, 'N/A']:
                                config_values[key] = original_config_values[key]

                        send_message_to_teams(client_name=client_name, instance_type=instance_type, request_timestamp=latest_deployment['request_timestamp'], deployed_by=deployer_name, deployer_object_id=deployer_object_id, project_name=project_name, lambda_function_url=lambda_function_url, config_values=config_values)
                    
                    else:
                        print("No config details found.")

                else:
                    print("No deployment details found.")
                    return {
                        'statusCode': 200,
                        'body': {}
                    }

        return {
            'statusCode': 200,
            'body': latest_deployment
        }

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return {
            'statusCode': 500,
            'body': {
                'error': str(e)
            }
        }