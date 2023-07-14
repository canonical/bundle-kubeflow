# Delete unattached EBS volumes (state=available) in all AWS regions
# source: https://towardsthecloud.com/amazon-ec2-delete-unattached-ebs-volumes
import boto3
from tenacity import retry, stop_after_attempt, wait_fixed
import sys

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2), reraise=True)
def delete_volumes_in_region(region_name: str, count: int)-> int:
    try:
        ec2conn = boto3.resource("ec2", region_name = region_name)
        unattached_volumes = [
            volume for volume in ec2conn.volumes.all() if (volume.state == "available")
        ]
        for volume in unattached_volumes:
            volume.delete()
            print(f"Deleted unattached volume {volume.id} in region {region_name}.")
            count = count + 1
        return count
    except Exception as e:
        print(f"Error: {e}")
        raise e

def validate_region(region_name: str)-> bool:
    ec2 = boto3.client("ec2")
    regions = ec2.describe_regions()["Regions"]
    regions_names = list(map(lambda region: region["RegionName"],regions))
    return region_name in regions_names

def delete_volumes() -> None:
    count = 0
    if len(sys.argv)>1:
        region_name = sys.argv[1]
        if validate_region(region_name):
            count = delete_volumes_in_region(region_name, count)
        else:
            print("Region from input isn't being used in this AWS account.")
            raise Exception
    else:
        ec2 = boto3.client("ec2")
        for region in ec2.describe_regions()["Regions"]:
            region_name = region["RegionName"]
            count = delete_volumes_in_region(region_name, count)

    if count > 0:
        print(f"Deleted {count} unattached volumes.")
    else:
        print("No unattached volumes found for deletion.")

delete_volumes()
