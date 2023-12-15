import boto3
import requests


# Function to get the system token
def get_token(refresh_token, hostname):
    # Check if the hostname is set
    if hostname is None:
        print("Error: 'hostname' variable is not set")
        return None

    # Construct the URL for token retrieval
    url = f"https://{hostname}/api/v1/refresh-access-token"
    headers = {"Authorization": refresh_token, "Content-Type": "application/json"}
    # Send a request to obtain the system token
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        system_token = data.get("systemToken")
        if system_token is not None:
            return system_token
        else:
            print("Error: 'systemToken' not found in the JSON response")
            return None
    else:
        print(f"Error: HTTP request failed with status code {response.status_code}")
        return None


# Function to scale the ECS task definition
def scale_ecs_task_definition(cluster_name, service_name, desired_count, region_name):
    # Create an ECS client
    ecs_client = boto3.client("ecs", region_name=region_name)

    # Update the service with the new desired count
    response = ecs_client.update_service(
        cluster=cluster_name,
        service=service_name,
        desiredCount=desired_count,
    )
    print(f"{response=}")
    return response  # Return the response from the update_service call


# Function to Get Scan Jobs


def get_scans_jobs(hostname, system_token):
    url = f"https://{hostname}/api/v1/scanner_jobs"
    headers = {"Authorization": system_token}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        return bool(data.get("results"))
    raise Exception(f"Scanner Jobs Return:{response.status_code}")


def get_scanners(system_token, url):
    headers = {"Authorization": system_token}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise RuntimeError(f"Recieved invalid status_code {response.status_code}")
    data = response.json()
    return data


def iterate_scanners(system_token, hostname, scanner_group):
    url = f"https://{hostname}/api/v1/scanner-status"
    scanners = get_scanners(system_token, url)
    scanners = scanners.get("data")
    scanners = [
        scanner for scanner in scanners if scanner.get("scanner_group") == scanner_group
    ]
    running = []
    for scanner in scanners:
        scanner_id = scanner.get("scanner_id")
        scanner_status_url = f"{url}/{scanner_id}"
        status = get_scanners(system_token, scanner_status_url)
        running.append(status.get("data")[0].get("running", 0))
    return any(running)


def main(
    refresh_token,
    hostname,
    cluster_name,
    service_name,
    desired_count,
    region_name,
    scanner_group,
):
    system_token = get_token(refresh_token, hostname)
    if system_token:
        jobs = get_scans_jobs(hostname, system_token)
        if not jobs:
            return "No Jobs"

        running = iterate_scanners(system_token, hostname, scanner_group)
        
        if not running:
            desired_count = 1
        # Get scans and scale ECS task definition based on the result
        result = scale_ecs_task_definition(
            cluster_name,
            service_name,
            desired_count,
            region_name,
        )
        return result
    else:
        return None


# Lambda entry point
def lambda_handler(event, context):
    hostname = event.get("host_name")
    refresh_token = event.get("refresh_token")
    cluster_name = event.get("cluster_name")
    service_name = event.get("service_name")
    region_name = event.get("region_name")
    desired_count = event.get("desired_count")
    scanner_group = event.get("scanner_group")
    result = main(
        refresh_token,
        hostname,
        cluster_name,
        service_name,
        desired_count,
        region_name,
        scanner_group,
    )
    if result == "No Jobs":
        return {
            "statusCode": 202,
            "body": "No Jobs Running",
        }
    elif result is not None:
        # Return a 200 response with a success message
        return {
            "statusCode": 200,
            "body": "Function executed successfully",
        }
    else:
        # Handle the case where there was an error
        return {
            "statusCode": 500,
            "body": "Internal Server Error",
        }
