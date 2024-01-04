"""Launch a proxy network to use for webscraping."""
import time
import concurrent
from typing import List

import boto3
from botocore.exceptions import ClientError
import requests

from .utils import time_elapsed

REGION = "us-west-1"
REGION_TO_SUBNET = {
    "us-east-2": "subnet-051e362c32e0c763d",
    "us-west-1": "subnet-0c3a9d15276945c69",
}
REGION_TO_AMI = {
    "us-east-2": "ami-0375da2d88c05cd63",
    "us-west-1": "ami-09021b2eeefde369c",
}
SECURITY_GROUP_TO_AMI = {
    "us-east-2": "sg-04f20d4ee640d31cc",
    "us-west-1": "sg-015a3f2aa1c00e2af",
}

INSTANCE_TYPE = "t2.micro"
AMI_ID = REGION_TO_AMI[REGION]
SUBNET_ID = REGION_TO_SUBNET[REGION]
SECURITY_GROUP_ID = SECURITY_GROUP_TO_AMI[REGION]


class FailedToConnectToIP(Exception):
    """Failed to connect to an IP address."""

    def __init__(self, ip):
        self.ip = ip

    def __str__(self):
        return f"Failed to connect to {self.ip}."


def _ec2_client() -> boto3.client:
    """Create an EC2 client."""
    return boto3.client("ec2", region_name=REGION)


def _ec2_resource() -> boto3.resource:
    """Create an EC2 resource."""
    return boto3.resource("ec2", region_name=REGION)


def _get_ip_list(instance_ids: List[str]) -> List[str]:
    """Get the IP addresses of the given instances."""
    ec2 = _ec2_resource()
    instances = ec2.instances.filter(InstanceIds=instance_ids)
    return [instance.public_ip_address for instance in instances]


def _terminate_cluster(instance_ids: List[str]) -> None:
    """Terminate a cluster of proxy servers."""
    ec2_client = _ec2_client()
    ec2_client.terminate_instances(InstanceIds=instance_ids)
    print(f"\tTerminated {len(instance_ids)} instances.")


def _launch_cluster(num: int = 10):
    """Launch a cluster of EC2 instances."""
    ec2 = _ec2_client()
    try:
        response = ec2.request_spot_instances(
            InstanceCount=num,
            LaunchSpecification={
                "ImageId": AMI_ID,
                "InstanceType": INSTANCE_TYPE,
                "SecurityGroupIds": [SECURITY_GROUP_ID],
                "SubnetId": SUBNET_ID,
            },
            SpotPrice="0.005",
        )
    except ClientError as e:
        print(e)
        raise e

    # Get the spot instance request IDs
    spot_instance_request_ids = [
        request["SpotInstanceRequestId"] for request in response["SpotInstanceRequests"]
    ]

    while True:
        desc_response = ec2.describe_spot_instance_requests(
            SpotInstanceRequestIds=spot_instance_request_ids
        )
        fulfilled = [
            request["State"] == "active"
            for request in desc_response["SpotInstanceRequests"]
        ]

        if all(fulfilled):
            # All requests are fulfilled, break the loop
            break
        else:
            # Wait for some time before checking again
            time.sleep(5)  # for example, wait for 30 seconds

    # After the loop, you can retrieve the instance IDs
    instance_ids = [
        request["InstanceId"] for request in desc_response["SpotInstanceRequests"]
    ]
    ec2.create_tags(
        Resources=instance_ids, Tags=[{"Key": "Service", "Value": "Proxy-Cluster"}]
    )
    return instance_ids


def _wait_for_ip(ip: str):
    """Wait for the IP address to be operational."""
    proxy = {"http": f"http://{ip}:8888", "https": f"http://{ip}:8888"}

    start = time.perf_counter()
    curr = time.perf_counter()
    while curr - start < 120:
        try:
            response = requests.get("http://google.com", proxies=proxy, timeout=5)
            if response.status_code == 200:
                return ip
        except:  # pylint: disable=bare-except
            pass
        curr = time.perf_counter()

    raise FailedToConnectToIP(ip)


def await_cluster(instance_ids: List[str]):
    """Wait for the cluster of EC2 instances to be operational."""
    ip_addresses = _get_ip_list(instance_ids)
    print(f"\tAwaiting cluster of {len(ip_addresses)} instances...")
    start = time.perf_counter()

    # Create a ThreadPoolExecutor
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_ip = {executor.submit(_wait_for_ip, ip): ip for ip in ip_addresses}
        count = 0
        for future in concurrent.futures.as_completed(future_to_ip):
            ip = future_to_ip[future]
            count += 1
            print(
                f"\t[{count:02d} / {len(ip_addresses)} - {time_elapsed(start):.2f}s] Successfully connected to {ip}"
            )

    # Otherwise, if the cluster is operational, then return the IP addresses
    print(f"\tCluster operational in {time_elapsed(start)} seconds.")
    return ip_addresses


def get_cluster(num: int = 10):
    """Get the IP addresses of the cluster currently running. Launch additional
    spot instances if necessary to reach the desired number of instances.
    """

    ec2_resource = _ec2_resource()

    print("\tSetting up Proxy Cluster.")

    # Get all the instances with the 'Service' tag and are running
    instances = ec2_resource.instances.filter(
        Filters=[
            {"Name": "tag:Service", "Values": ["Proxy-Cluster"]},
            {"Name": "instance-state-name", "Values": ["running"]},
        ]
    )

    # Get the instance IDs and IP addresses
    instance_ids = [instance.id for instance in instances]
    instances_required = num - len(instance_ids)

    # If there are more instances than we need
    if instances_required < 0:
        # Trim back the list of instance_ids
        instance_ids = instance_ids[:num]
        instances_required = 0

    print(
        f"\tFound {len(instance_ids)} instances. {instances_required} still required."
    )

    # If there are additional instances required, then launch them
    if instances_required:
        # Launch additional instances
        instance_ids.extend(_launch_cluster(instances_required))

    # Wait for all the instances to be operational
    ip_addresses = await_cluster(instance_ids)
    return ip_addresses


def terminate_cluster():
    """Terminate the cluster of EC2 instances."""
    ec2_resource = _ec2_resource()

    # Get all the instances with the 'Service' tag and are running
    instances = ec2_resource.instances.filter(
        Filters=[
            {"Name": "tag:Service", "Values": ["Proxy-Cluster"]},
            {"Name": "instance-state-name", "Values": ["running"]},
        ]
    )
    instance_ids = [instance.id for instance in instances]
    _terminate_cluster(instance_ids)
    # Terminate the instances


class EC2Client:
    pass


class ProxyCluster:
    """A cluster of proxy servers."""

    def __init__(self, num: int = 10):
        self._start = time.perf_counter()
        self._size = num
        instance_ids = self._get_cluster()
        ip_addresses = self._await_cluster(instance_ids)

        self._active_proxies = {
            _ip: _id for _ip, _id in zip(ip_addresses, instance_ids)
        }
        self._warm_pool = []

    def _log(self, message: str):
        curr = time.perf_counter()
        print(f"\t[ProxyCluster - {curr - self._start:.2f}s] {message}")

    def _get_cluster(self, offset: int = 0, warm_pool: bool = False):
        """Get the IP addresses of the cluster currently running. Launch additional
        spot instances if necessary to reach the desired number of instances.
        """

        ec2_resource = _ec2_resource()

        msg = "Filling proxy warm pool." if warm_pool else "Setting up Proxy Cluster."
        self._log(f"{msg} with {self._size} instances.")

        # Get all the instances with the 'Service' tag and are running
        instances = ec2_resource.instances.filter(
            Filters=[
                {"Name": "tag:Service", "Values": ["Proxy-Cluster"]},
                {"Name": "instance-state-name", "Values": ["running"]},
            ]
        )

        # Get the instance IDs and IP addresses
        instance_ids = [instance.id for instance in instances]
        if warm_pool:
            # We don't want to count any ids that are in the active cluster
            instance_ids = [
                _id for _id in instance_ids if _id not in self._active_proxies.values()
            ]

        # Calculate the number of instances required
        instances_required = (self._size - offset) - len(instance_ids)

        # If there are more instances than we need
        if instances_required < 0:
            # Trim back the list of instance_ids
            instance_ids = instance_ids[: self._size - offset]
            instances_required = 0

        resource = "warm pool" if warm_pool else "cluster"
        self._log(
            f"Found {len(instance_ids)} instances for {resource}. {instances_required} still required."
        )

        # If there are additional instances required, then launch them
        if instances_required:
            # Launch additional instances
            instance_ids.extend(_launch_cluster(instances_required))
            self._log(f"Launched {instances_required} instances for {resource}.")

        # Wait for all the instances to be operational
        return instance_ids

    def _await_cluster(self, instance_ids: List[str]):
        """Wait for the cluster of EC2 instances to be operational."""
        ip_addresses = _get_ip_list(instance_ids)

        self._log("Awaiting cluster to become active.")

        # Create a ThreadPoolExecutor
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_ip = {
                executor.submit(_wait_for_ip, ip): ip for ip in ip_addresses
            }
            count = 0
            for future in concurrent.futures.as_completed(future_to_ip):
                ip = future_to_ip[future]
                count += 1
                self._log(
                    f"({count:02d} / {len(ip_addresses):02d}) Successfully connected to {ip}"
                )

        # Otherwise, if the cluster is operational, then return the IP addresses
        self._log(
            f"Cluster operational in {time.perf_counter() - self._start:.2f} seconds."
        )
        return ip_addresses

    def _terminate_cluster(self, total: bool = False) -> None:
        """Terminate a cluster of proxy servers."""
        instance_ids = list(self._active_proxies.values())
        if total:
            instance_ids.extend(self._warm_pool)

        ec2_client = _ec2_client()
        ec2_client.terminate_instances(InstanceIds=instance_ids)
        self._log(f"\tTerminated {len(instance_ids)} instances.")

    @property
    def ips(self):
        """Return the IP addresses of the active proxies."""
        return list(self._active_proxies.keys())

    def reboot(self):
        """Reboot the cluster of proxy servers."""
        self._start = time.perf_counter()
        self._log(f"Rebooting cluster with {self._size} instances.")
        # Clear all the active proxies
        self._terminate_cluster()

        # Reset the _actives_procies and _warm_pool
        self._active_proxies = {}
        instance_ids = self._get_cluster()
        ip_addresses = self._await_cluster(instance_ids)
        self._active_proxies = {
            _ip: _id for _ip, _id in zip(ip_addresses, instance_ids)
        }
        return ip_addresses

    def activate_warm_pool(self):
        """Activate the warm pool of proxies."""
        self._start = time.perf_counter()
        self._log(f"Activating warm pool with {self._size} instances.")

        self._terminate_cluster()

        ip_addresses = self._await_cluster(self._warm_pool)
        self._active_proxies = {
            _ip: _id for _ip, _id in zip(ip_addresses, self._warm_pool)
        }
        self._warm_pool = []
        return ip_addresses

    def fill_warm_pool(self):
        """Fill the warm pool with proxies."""
        self._start = time.perf_counter()
        self._log(f"Filling warm pool with {self._size} instances.")

        # Get the number of

        # Reset the _warm_pool
        instance_ids = self._get_cluster(offset=len(self._warm_pool), warm_pool=True)
        self._warm_pool = instance_ids
