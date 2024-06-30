import boto3
import requests
import json

def get_secret(secret_arn, region_name):
    secret_name = secret_arn

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

def get_certificates(cert_secret_arn, region_name, cert_keys):
    """
    Fetches the CA certificate, private certificate, and public certificate from AWS Secrets Manager using the provided ARNs.

    :param cert_secret_arn: The ARNs of the secrets.
    :param region_name: The AWS region where the secrets are stored.
    :param cert_keys: The dictionary containing the keys for ca_cert_key, private_cert_key, and public_cert_key.
    :return: A dictionary with the certificates, or None if an error occurs.
    """
    certs = {cert_keys['ca_cert_key']: None, cert_keys['private_cert_key']: None, cert_keys['public_cert_key']: None}
    
    for secret_arn in cert_secret_arn:
        secret = get_secret(secret_arn, region_name)
        if secret:
            try:
                secret_dict = json.loads(secret)
                for key in certs.keys():
                    if secret_dict.get(key):
                        certs[key] = secret_dict.get(key)
                        print(f"cert found: {key}")
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON from secret: {e}")
        else:
            print(f"Error fetching secret with ARN: {secret_arn}")
         
    return certs

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
        return {}
    return proxies

# Function to get the system token
def get_token(refresh_token, hostname, proxies, certs=None, cert_keys=None):
    # Check if the hostname is set
    if hostname is None:
        print("Error: 'hostname' variable is not set")
        return None

    # Construct the URL for token retrieval
    url = f"{hostname}/api/v1/refresh-access-token"
    headers = {"Authorization": refresh_token, "Content-Type": "application/json"}

    verify = True  # Default to using the system CA bundle
    cert = None  # Default to not using client certificates
    if certs:
        # If ca_cert_key is available, use it as the CA bundle
        if certs.get(cert_keys['ca_cert_key']):
            verify = certs[cert_keys['ca_cert_key']]
        # If both private_cert_key and public_cert_key are available, use them as a tuple
        if certs.get(cert_keys['private_cert_key']) and certs.get(cert_keys['public_cert_key']):
            cert = (certs[cert_keys['public_cert_key']], certs[cert_keys['private_cert_key']])

    try:
        print(f"proxies: {proxies}")
        print(f"url: {url}")
        response = requests.get(url, headers=headers, proxies=proxies, verify=verify, cert=cert)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx and 5xx)
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        if 300 <= response.status_code < 400:
            redirect_url = response.headers.get('Location')
            print(f"Redirected to: {redirect_url}")
            response = requests.get(redirect_url, headers=headers, proxies=proxies, verify=verify, cert=cert)
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
def get_scans_jobs(hostname, system_token, scanner_group, proxies, certs=None, cert_keys=None):
    verify = True  # Default to using the system CA bundle
    cert = None  # Default to not using client certificates
    if certs:
        # If ca_cert_key is available, use it as the CA bundle
        if certs.get(cert_keys['ca_cert_key']):
            verify = certs[cert_keys['ca_cert_key']]
        # If both private_cert_key and public_cert_key are available, use them as a tuple
        if certs.get(cert_keys['private_cert_key']) and certs.get(cert_keys['public_cert_key']):
            cert = (certs[cert_keys['public_cert_key']], certs[cert_keys['private_cert_key']])

    if proxies.get('http') or proxies.get('https'):
        print(f"Using proxies: HTTP: {proxies.get('http')}, HTTPS: {proxies.get('https')}")
    url = f"{hostname}/api/v1/scanner_jobs"
    headers = {"Authorization": system_token}
    try:
        response = requests.get(url, headers=headers, proxies=proxies, verify=verify, cert=cert)
        response.raise_for_status()
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        if 300 <= response.status_code < 400:
            redirect_url = response.headers.get('Location')
            print(f"Redirected to: {redirect_url}")
            response = requests.get(redirect_url, headers=headers, proxies=proxies, verify=verify, cert=cert)
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

def get_scanner_list(system_token, hostname, scanner_group, proxies, certs=None, cert_keys=None):
    scanners = get_scanners(system_token, hostname, proxies, certs, cert_keys)
    scanners = scanners.get("data")
    scanners = [
        scanner for scanner in scanners if scanner.get("scanner_group") == scanner_group
    ]
    return scanners

def get_scanners(system_token, hostname, proxies, certs=None, cert_keys=None, scanner_id=None):
    verify = True  # Default to using the system CA bundle
    cert = None  # Default to not using client certificates
    if certs:
        # If ca_cert_key is available, use it as the CA bundle
        if certs.get(cert_keys['ca_cert_key']):
            verify = certs[cert_keys['ca_cert_key']]
        # If both private_cert_key and public_cert_key are available, use them as a tuple
        if certs.get(cert_keys['private_cert_key']) and certs.get(cert_keys['public_cert_key']):
            cert = (certs[cert_keys['public_cert_key']], certs[cert_keys['private_cert_key']])

    if proxies.get('http') or proxies.get('https'):
        print(f"Using proxies: HTTP: {proxies.get('http')}, HTTPS: {proxies.get('https')}")
    url = f"{hostname}/api/v1/scanner-status"
    if scanner_id:
        url = f"{url}/{scanner_id}"
    headers = {"Authorization": system_token}
    try:
        response = requests.get(url, headers=headers, proxies=proxies, verify=verify, cert=cert)
        response.raise_for_status()
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        if 300 <= response.status_code < 400:
            redirect_url = response.headers.get('Location')
            print(f"Redirected to: {redirect_url}")
            response = requests.get(redirect_url, headers=headers, proxies=proxies, verify=verify, cert=cert)
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
def iterate_scanners(system_token, hostname, scanner_group, proxies, certs=None, cert_keys=None):
    scanners = get_scanner_list(system_token, hostname, scanner_group, proxies, certs, cert_keys)
    running = []
    for scanner in scanners:
        scanner_id = scanner.get("scanner_id")
        status = get_scanners(system_token, hostname, proxies, certs, cert_keys, scanner_id)
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
    cert_secret_arn,  
    ca_cert_key,  
    private_cert_key, 
    public_cert_key  
):
    proxies = get_proxies(http_proxy_host, http_proxy_port, https_proxy_host, https_proxy_port)
    print(f"Proxies used: {proxies}")
    refresh_token = get_secret(refresh_token_secret_id, region_name)

    cert_keys = {
        'ca_cert_key': ca_cert_key,
        'private_cert_key': private_cert_key,
        'public_cert_key': public_cert_key
    }

    # Fetch the certificates
    certs = get_certificates(cert_secret_arn, region_name, cert_keys)

    system_token = get_token(refresh_token, hostname, proxies, certs=certs, cert_keys=cert_keys)
    if system_token:
        jobs = get_scans_jobs(hostname, system_token, scanner_group, proxies, certs, cert_keys)
        scanners = get_scanner_list(system_token, hostname, scanner_group, proxies, certs, cert_keys)
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
    cert_secret_arn = event.get("cert_secret_arn") 
    ca_cert_key = event.get("ca_cert_key")  
    private_cert_key = event.get("private_cert_key")  
    public_cert_key = event.get("public_cert_key")  

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
        minimum_desired_count,
        cert_secret_arn,
        ca_cert_key,
        private_cert_key,
        public_cert_key
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
