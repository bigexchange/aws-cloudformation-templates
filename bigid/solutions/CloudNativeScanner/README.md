# Cloud Native scanners on ECS

## Requirements


* BigID Scanner Images Uploaded to the ECR account where the cluster will be deployed

* The Security Group with Egress Access to the Public Internet & A Subnet Corresponding with the same Security group within the same VPC


## Using Cloudformation



Using the cloud formation template provided, kindly navigate to the Cloudformation AWS option to start creating the required stack.

### Creating a Stack

**Cloudformation** **>** **Stack** **>** **Create a New Stack**

![image](https://github.com/bigexchange/aws-cloudformation-templates/assets/34100385/28b47a8c-e271-4fa0-97b4-4aded668195e)


Upload the Cloudformation Template, and input the following variables below.

```
https://raw.githubusercontent.com/bigexchange/aws-cloudformation-templates/main/bigid/solutions/CloudNativeScanner/scanner.yaml
```

## Input Variables for Cloudformation


### Repository Configuration

| Parameter            | Description                                                                                                                     | Type   |
|----------------------|---------------------------------------------------------------------------------------------------------------------------------|--------|
| ScannerRepository    | The full replacement repository URL for the scanner (excluding tag), Example: 1234567890.dkr.ecr.us-east-1.amazonaws.com/bigid/bigid-scanner | String |
| NerRepository        | The full replacement repository URL for the NER scanner (excluding tag), Example: 1234567890.dkr.ecr.us-east-1.amazonaws.com/bigid/bigid-ner | String |
| LabelerRepository    | The full replacement repository URL for the labeler (excluding tag), Example: 1234567890.dkr.ecr.us-east-1.amazonaws.com/bigid/bigid-labeler | String |
| ImageTagVersion      | The tag of the release, please make sure your images versions correctly tagged. E.G: release-123.45                            | String |

### Scanner Configuration

| Parameter                 | Description                                                                                                                                            | Type    |
|---------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------|---------|
| BigIDUIProtocol           | The protocol to connect to BigID UI (either HTTP or HTTPS).                                                                                            | String  |
| BigIDHostname             | The hostname for BigID (e.g., test.bigid.cloud). Please DO NOT include the protocol (http:// or https://).                                              | String  |
| NerEnabled                | Enable Named Entity Recognition (NER).                                                                                                                 | String  |
| ScannerGroupOption        | Option to set the Scanner Group Name. Custom: will be whatever the custom value set is. Region: Will be named after the region the scanner is deploying in. AccountID: Will be the account ID of the account the scanner is located in. AccountID-Region: Will be the AccountID-Region the scanner is currently deployed in | String  |
| ScannerCPU                | The amount of CPU units to allocate for the scanner. Use increments provided by Amazon (e.g., 256, 512, 1024, 2048).                                   | Number  |
| ScannerMemory             | The amount of memory (in MB) to allocate for the scanner. Use increments provided by Amazon (e.g., 256, 512, 1024, 2048).                              | Number  |
| CustomScannerGroupName    | The Scanner Group Name if Custom option is selected.                                                                                                   | String  |
| BigIDRefreshToken         | The refresh token for BigID. This will create an AWS Secret in Secrets Manager which will be referenced in the deployment.                              | String  |
| BigIDRefreshSecretArn     | The ARN of the existing secret to use for BigID Scanner Token (Optional). You will need to have created an AWS Secret and specify it with the full ARN for the secret. | String  |
| MaximumScannerCount       | The maximum number of BigID scanner instances (replicas) to run.                                                                                       | Number  |
| MinimumScannerCount       | The minimum number of scanner replicas. To scale from 0, set VALIDATE_SCANNER_GROUP=false for Orch in the BigID UI.                                    | Number  |
| ScheduleExpression        | The schedule expression for the scaling Lambda. Choose from predefined rates or select 'custom' to specify your own rate in minutes.                    | String  |
| CustomScheduleMinutes     | Custom schedule in minutes.                                                                                                                            | Number  |

### Scanner ARN Policy Configuration

| Parameter              | Description                                                                                                                           | Type   |
|------------------------|---------------------------------------------------------------------------------------------------------------------------------------|--------|
| AttachManagedPolicy    | Indicate whether to attach a managed policy to the role. This policy is a requirement. If you have an external policy to attach directly to the scanner role to allow it to scan resources inside/outside the account, this is optional. | String |
| ManagedPolicyArn       | The ARN of the managed policy to attach to the role. Provide a value for this parameter only if 'AttachManagedPolicy' is set to 'true'. | String |

### Scanner and Lambda Network Configuration

| Parameter          | Description                                                                                                                             | Type                      |
|--------------------|-----------------------------------------------------------------------------------------------------------------------------------------|---------------------------|
| VpcID              | The VPC ID to use for the ECS Task Definition for the Scanner and Scaler.                                                              | AWS::EC2::VPC::Id         |
| Subnet1            | The first subnet ID to use for the ECS Task Definition for the Scaler and for the Lambda. These will need to be configured privately with VPC Endpoints or Subnet with a NAT, NOTE: do not use a IGW. | AWS::EC2::Subnet::Id      |
| Subnet2            | The second subnet ID to use for the ECS Task Definition for the Scaler and for the Lambda. These will need to be configured privately with VPC Endpoints or Subnet with a NAT, NOTE: do not use a IGW. | AWS::EC2::Subnet::Id      |
| Subnet3            | The third subnet ID to use for the ECS Task Definition for the Scaler and for the Lambda. These will need to be configured privately with VPC Endpoints or Subnet with a NAT, NOTE: do not use a IGW. | AWS::EC2::Subnet::Id      |
| SecurityGroupName  | The name of the security group to use for the ECS Task Definition for the Scaler. This will require egress over port 443.               | AWS::EC2::SecurityGroup::Id|

### Scanner / Lambda Network Proxy Configuration

| Parameter       | Description                                                                                                                                                 | Type   |
|-----------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------|--------|
| AssignPublicIp  | If set to DISABLED, scanners won't have public IPs. Ensure a NAT or IGW is configured for egress. This Public IP allocation is specifically for allowing ECS Service to be assigned a public IP address. | String |
| HttpsProxyHost  | If utilizing an HTTPS Proxy, specify so your scanner/scaler can reach out to the internet using a proxy instance. You will need to specify the string as http://your.proxy.example.com:$PORT_NUMBER. It must use the HTTP protocol; do not change to HTTPS. | String |
| HttpsProxyPort  | Port that will be appended to your proxy string http://your.proxy.example.com:$PORT_NUMBER.                                                                  | String |
| HttpProxyHost   | If utilizing an HTTP Proxy, specify so your scanner/scaler can reach out to the internet using a proxy instance. You will need to specify the string as http://your.proxy.example.com:$PORT_NUMBER.   | String |
| HttpProxyPort   | Port that will be appended to your proxy string http://your.proxy.example.com:$PORT_NUMBER.                                                                  | String |





## Enable Scaling from Zero
In order to scale from 0, there are some preliminary things that will need to be done in order to get the functionality of scale to zero to work. We will need to work in the following steps.

### Edit the BigID UI
#### Step 1.a
 Go to the BigID UI and go to the Advanced Tools Section
#### Step 2.a
Search for `VALIDATE_SCANNER_GROUP`
### Step 3.a
Change the environemnt variable from `true` to `false`

**Once this is completed, you will have to modify your DataSource to be able to be pointed to whichever scanner group is designated within the Cloudformation Template `ScannerGroupName`(Dependent on the Option Chosen, I.E Custom..Etc..Etc.), this will allow the Scanner to be able to recieve work. If you do not set this the scanner will never recieve work, please consult your Services Engineer, if you need any assistance in modifying this datasources group name.**


## ECS Diagram

![ecsdiagram](https://github.com/bigexchange/aws-cloudformation-templates/assets/34100385/6d972dba-70bc-4f90-b407-56762a8581ed)


### ECS Diagram Explanation

#### customer.bigid.cloud
The customer tenant hosted in the cloud.

#### ECS Scaler Lambda
This is the required Lambda that is being utilized for scaling up and scaling down the ECS Scanner Containers. This is created specifically to interact with your cloud tenant, and monitor your tenant to see if there are any active jobs currently available. The lambda communicates with the ECS Scanner Task Definitions and based upon the parameter Scanner Count, which when a scan job kicks off, it will create the maximum amount of scanners to pick up work from the BigID Tenant, and then be assigned to running a scan during that time. Once it has completed its job, it will return back to 1, which is the minimum scanner count.

#### ECS Scanner Cluster
This is the hierachical object that is required to spin up the following resources which are the ECS Scanner Task Definitions / ECS Scanner Services.

##### Scanner Task Definition

This Task Definition is responsible for the configuration of the Scanner, this sets all of the container environment variables, and is responsible for the amount of replicas of scanners.

##### BigID Scanner

Scanner Pod that is scaled out from the Task Definition

##### BigID Ner 

Sidecar container in tandem with scanner pod that utilizes NER
