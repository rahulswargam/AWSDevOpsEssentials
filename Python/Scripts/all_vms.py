#This program gets the VM regions list and VMs list and type also evaluate user input.
import boto3
my_aws_regions = []
client = boto3.client('ec2',
aws_access_key_id='AKIA2QEFLENWD6VGAJOS',
aws_secret_access_key='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')
all_regions = client.describe_regions().get('Regions',[])
for region in all_regions:
    my_aws_regions.append(region['RegionName'])
all_vms = client.describe_instances().get('Reservations',[])
instance_types = []
for vms in all_vms:
    for vm in vms['Instances']:
        instance_types.append(vm['InstanceType'])
user_input = str(input("Please Enter The Instance Type:"))
if user_input in instance_types:
    print(f'Machine with type {user_input} exists..!!')
else:
    print(f'Machine with type {user_input} dont exists..!!')

