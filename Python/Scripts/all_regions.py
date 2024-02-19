#Get VMs in the Regions List
import boto3
my_aws_regions = ['us-east-1','us-east-2','us-west-1','us-west-2']
for region in my_aws_regions:
    client = boto3.client('ec2',
    aws_access_key_id='AKIA2QEFLENWD6VGAJOS',
    aws_secret_access_key='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',
    region_name = region)
    all_vms = client.describe_instances().get('Reservations',[])
    instance_types = []
    for vms in all_vms:
      for vm in vms['Instances']:
        instance_types.append(vm['InstanceId'])
    print(f'The VMs in region {region} are {instance_types}')