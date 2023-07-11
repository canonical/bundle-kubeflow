# Delete unattached EBS volumes (state=available) in all AWS regions
# source: https://towardsthecloud.com/amazon-ec2-delete-unattached-ebs-volumes
import boto3

ec2 = boto3.client("ec2")

count = 0
for region in ec2.describe_regions()["Regions"]:
    region_name = region["RegionName"]
    try:
        ec2conn = boto3.resource("ec2", region_name=region_name)
        unattached_volumes = [
            volume for volume in ec2conn.volumes.all() if (volume.state == "available")
        ]
        for volume in unattached_volumes:
            volume.delete()
            print(f"Deleted unattached volume {volume.id} in region {region_name}")
            count += 1
    except Exception as e:
        print(f"Error: {e}")

if count > 0:
    print(f"Deleted {count} unattached volumes")
