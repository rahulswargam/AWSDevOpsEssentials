import boto3
import sys

def delete_dns_records(client_name, instance_type=None):

    # Boto3 client for Route 53
    client = boto3.client('route53')

    # List of DNS Records
    if instance_type:
        record_names = [
            f"{instance_type}-primary-db.{client_name}.streamlyne.org",
            f"{instance_type}-ro-db.{client_name}.streamlyne.org",
            f"{instance_type}-db.{client_name}.streamlyne.org",
            f"{instance_type}-research.{client_name}.streamlyne.org",
            f"{instance_type}-research-us-east-1.{client_name}.streamlyne.org",
            f"{instance_type}-reporting.{client_name}.streamlyne.org",
            f"{instance_type}-reporting-us-east-1.{client_name}.streamlyne.org"
        ]
    else:
        record_names = [f"db.{client_name}.streamlyne.org"]

    # Hosted Zone
    zones = client.list_hosted_zones_by_name()

    if zones and zones['HostedZones']:
        zone_id = zones['HostedZones'][0]['Id']

        for record_name in record_names:
            response = client.list_resource_record_sets(
                HostedZoneId=zone_id,
                StartRecordName=record_name,
                StartRecordType="A"
            )
            found = False
            for record in response.get('ResourceRecordSets', []):
                if record['Name'] == record_name:
                    found = True

                    # To DELETE the DNS Record
                    client.change_resource_record_sets(
                        HostedZoneId=zone_id,
                        ChangeBatch={
                            'Changes': [
                                {
                                    'Action': 'DELETE',
                                    'ResourceRecordSet': record
                                }
                            ]
                        }
                    )
                    break

            if found:
                print(f"The DNS Record with the name '{record_name}' has been successfully removed")
            else:
                print(f"The DNS Record with the name '{record_name}' does not exists")

# It will check if the correct arguments are given or not
if len(sys.argv) < 2:
    print("Usage: python script_name.py [client_name] [instance_type]")
    sys.exit(1)

client_name = sys.argv[1]
instance_type = sys.argv[2] if len(sys.argv) > 2 else None
delete_dns_records(client_name, instance_type)
