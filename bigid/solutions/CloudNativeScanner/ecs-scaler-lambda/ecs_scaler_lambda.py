import boto3
import requests


# Function to get the system token
def get_token(refresh_token, host_name):
    # Check if the host_name is set
    if host_name is None:
        print("Error: 'host_name' variable is not set")
        return None

    # Construct the URL for token retrieval
    url = f"https://{host_name}/api/v1/refresh-access-token"
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
    pprint(response.json())
    if response.status_code == 200:
        data = response.json()
        return bool(data.get("results"))
    raise Exception(f"Scanner Jobs Return:{response.status_code}")


def main(
    refresh_token,
    host_name,
    cluster_name,
    service_name,
    desired_count,
    region_name,
):
    system_token = get_token(refresh_token, host_name)
    if system_token:
        if not get_scans_jobs(host_name, system_token):
            desired_count = 0
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
    host_name = event.get("host_name")
    refresh_token = event.get("refresh_token")
    cluster_name = event.get("cluster_name")
    service_name = event.get("service_name")
    region_name = event.get("region_name")
    desired_count = event.get("desired_count")
    result = main(
        refresh_token,
        host_name,
        cluster_name,
        service_name,
        desired_count,
        region_name,
    )
    if result is not None:
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
