import boto3
import requests

def get_secret(refresh_token_secret_id, region_name):
    secret_name = refresh_token_secret_id
    region_name = region_name  # Replace with your AWS region

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except Exception as e:
        print(f"An error occurred while fetching the secret: {e}")
        return None

    # Extract the secret string
    if 'SecretString' in get_secret_value_response:
        secret = get_secret_value_response['SecretString']
    else:
        print("Secret string not found")
        return None

    return secret


def get_proxies(http_proxy_host, http_proxy_port, https_proxy_host, https_proxy_port):
    http_proxy = f"{http_proxy_host}:{http_proxy_port}" if http_proxy_host else None
    https_proxy = f"{https_proxy_host}:{https_proxy_port}" if https_proxy_host else None
    proxies = {
        'http': http_proxy,
        'https': https_proxy,
    }
    if http_proxy_host or https_proxy_host:
        print(f"Using proxies: HTTP: {http_proxy}, HTTPS: {https_proxy}")
    else:
        print("No proxy hosts provided.")
    return proxies

# Function to get the system token
def get_token(refresh_token, hostname, proxies):
    # Check if the hostname is set
    if hostname is None:
        print("Error: 'hostname' variable is not set")
        return None

    # Construct the URL for token retrieval
    url = f"{hostname}/api/v1/refresh-access-token"
    headers = {"Authorization": refresh_token, "Content-Type": "application/json"}
    try:
        print(f"proxies: {proxies}")
        print(f"url: {url}")
        response = requests.get(url, headers=headers, proxies=proxies)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx and 5xx)
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        if 300 <= response.status_code < 400:
            redirect_url = response.headers.get('Location')
            print(f"Redirected to: {redirect_url}")
            response = requests.get(redirect_url, headers=headers, proxies=proxies)
            response.raise_for_status()
        else:
            return None
    except Exception as err:
        print(f"Other error occurred: {err}")
        return None

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
def get_scans_jobs(hostname, system_token, scanner_group, proxies):
    if proxies.get('http') or proxies.get('https'):
        print(f"Using proxies: HTTP: {proxies.get('http')}, HTTPS: {proxies.get('https')}")
    url = f"{hostname}/api/v1/scanner_jobs"
    headers = {"Authorization": system_token}
    try:
        response = requests.get(url, headers=headers, proxies=proxies)
        response.raise_for_status()
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        if 300 <= response.status_code < 400:
            redirect_url = response.headers.get('Location')
            print(f"Redirected to: {redirect_url}")
            response = requests.get(redirect_url, headers=headers, proxies=proxies)
            response.raise_for_status()
        else:
            return None
    except Exception as err:
        print(f"Other error occurred: {err}")
        return None

    if response.status_code == 200:
        data = response.json()
        scanner_group_jobs = [r for r in data.get("results") if r.get("group") == scanner_group]
        return bool(scanner_group_jobs)
    else:
        print(f"Error: HTTP request failed with status code {response.status_code}")
        return None

def get_scanner_list(system_token, hostname, scanner_group, proxies):
    scanners = get_scanners(system_token, hostname, proxies)
    scanners = scanners.get("data")
    scanners = [
        scanner for scanner in scanners if scanner.get("scanner_group") == scanner_group
    ]
    return scanners

def get_scanners(system_token, hostname, proxies, scanner_id=None):
    if proxies.get('http') or proxies.get('https'):
        print(f"Using proxies: HTTP: {proxies.get('http')}, HTTPS: {proxies.get('https')}")
    url = f"{hostname}/api/v1/scanner-status"
    if scanner_id:
        url = f"{url}/{scanner_id}"
    headers = {"Authorization": system_token}
    try:
        response = requests.get(url, headers=headers, proxies=proxies, allow_redirects=False)
        response.raise_for_status()
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        if 300 <= response.status_code < 400:
            redirect_url = response.headers.get('Location')
            print(f"Redirected to: {redirect_url}")
            response = requests.get(redirect_url, headers=headers, proxies=proxies)
            response.raise_for_status()
        else:
            return None
    except Exception as err:
        print(f"Other error occurred: {err}")
        return None

    if response.status_code == 200:
        data = response.json()
        return data
    else:
        print(f"Error: HTTP request failed with status code {response.status_code}")
        return None

# Gets all the scanner ID's for a given scanner group and returns 0 if there are no scanners working
def iterate_scanners(system_token, hostname, scanner_group, proxies):
    scanners = get_scanner_list(system_token, hostname, scanner_group, proxies)
    running = []
    for scanner in scanners:
        scanner_id = scanner.get("scanner_id")
        status = get_scanners(system_token, hostname, proxies, scanner_id)
        running.append(status.get("data")[0].get("running", 0))
    return any(running)


def main(
    refresh_token_secret_id,
    hostname,
    http_proxy_host,
    http_proxy_port,
    https_proxy_host,
    https_proxy_port,
    cluster_name,
    service_name,
    desired_count,
    region_name,
    scanner_group,
    minimum_desired_count,
):
    proxies = get_proxies(http_proxy_host, http_proxy_port, https_proxy_host, https_proxy_port)
    print(f"Proxies used: {proxies}")
    refresh_token = get_secret(refresh_token_secret_id, region_name)
    system_token = get_token(refresh_token, hostname, proxies)
    if system_token:
        jobs = get_scans_jobs(hostname, system_token, scanner_group, proxies)
        scanners = get_scanner_list(system_token, hostname, scanner_group, proxies)
        scale = False
        print(f"jobs: {jobs}")
        print(f"scanners: {len(scanners)}")
        print(f"min: {minimum_desired_count}")
        print(f"desired_count: {desired_count}")
        # If there are no queued scans and active scanners are present,
        # check if the number of active scanners exceeds the desired minimum count.
        # If there are more active scanners than needed, scale down the scanner count.
        if not jobs and len(scanners) > minimum_desired_count:
            desired_count = minimum_desired_count
            scale = True
            print("Scaling Down")
        elif jobs and len(scanners) < int(desired_count):
            desired_count = desired_count
            scale = True
            print("Scaling up Scanners")
        if scale:
            #  Get scans and scale ECS task definition based on the result
            print("Calling ECS Task Definition")
            result = scale_ecs_task_definition(
                cluster_name,
                service_name,
                desired_count,
                region_name,
            )
            return result
        return "Nothing to do"
    else:
        return None

# Lambda entry point
def lambda_handler(event, context):
    hostname = event.get("host_name")
    refresh_token_secret_id = event.get("refresh_token_secret_id")
    cluster_name = event.get("cluster_name")
    service_name = event.get("service_name")
    region_name = event.get("region_name")
    desired_count = event.get("desired_count")
    scanner_group = event.get("scanner_group")
    minimum_desired_count = event.get("minimum_desired_count")
    http_proxy_host = event.get("http_proxy_host")
    http_proxy_port = event.get("http_proxy_port")
    https_proxy_host = event.get("https_proxy_host")
    https_proxy_port = event.get("https_proxy_port")
    result = main(
        refresh_token_secret_id,
        hostname,
        http_proxy_host,
        http_proxy_port,
        https_proxy_host,
        https_proxy_port,
        cluster_name,
        service_name,
        desired_count,
        region_name,
        scanner_group,
        minimum_desired_count
    )
    
    if result == "Nothing to do": 
            return {
            "statusCode": 200,
            "body": "Function executed successfully, nothing to do",
        }
    elif result is not None:
        # Check if scaling down
        if desired_count == minimum_desired_count:
            return {
                "statusCode": 202,
                "body": "Scaling scanners down to minimum count",
            }
        # Scaling up or maintaining the desired count
        return {
            "statusCode": 200,
            "body": "Function executed successfully and scaling performed",
        }
    else:
        # Handle the case where there was an error or no scaling was needed
        return {
            "statusCode": 500,
            "body": "Internal Server Error or no scaling performed",
        }
