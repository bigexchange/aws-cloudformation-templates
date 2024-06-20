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


| Key                      | Value                                        | Type   | Description                                                                                                          |
|--------------------------|----------------------------------------------|--------|----------------------------------------------------------------------------------------------------------------------|
| BigIDRefreshToken        | `TOKEN`                                      | String | The refresh token for BigID. This will create an AWS Secret in Secrets Manager to be referenced in the deployment.   |
| ImageRepository          | `1234567890.dkr.ecr.us-east-1.amazonaws.com` | String | The full replacement repository URL for the scanner (including tag).                                                 |
| ImageTagVersion          | `release-xxx`                                | String | The tag of the scanner version.                                                                                      |
| SecurityGroupName        | `sg-123456`                                  | String | The name of the security group to use for the ECS Task Definition for the Scaler. Requires egress over port 443.     |                                      |
| NerEnabled               | `false`                                      | Bool   |  Enable BigID Named Entity Recognition (NER).(NER).                                                                               |
| ScannerCount             | `3`                                          | Int    | The number of scanner instances to run.                                                                              |
| VpcID                    | `vpc-0a1b2c3d4e5f6g7h`                       | String | The VPC ID to use for the ECS Task Definition for the Scanner and Scaler.                                            |
| Subnet1                  | `subnet-0a1b2c3d4e5f6g7h`                    | String | The first subnet ID to use for the ECS Task Definition for the Scaler and Lambda.                                    |
| Subnet2                  | `subnet-1a2b3c4d5e6f7g8h`                    | String | The second subnet ID to use for the ECS Task Definition for the Scaler and Lambda.                                   |
| Subnet3                  | `subnet-2a3b4c5d6e7f8g9h`                    | String | The third subnet ID to use for the ECS Task Definition for the Scaler and Lambda.                                    |
| ScannerGroupOption       | `Custom`                                     | String | Custom: Any Custom Scanner Group Name Region: Region, which you are deploying the scanner e.g(us-east-1), Account: This will utilize the AWS AccountID where the scanner is being deployed, AccountID-Region: This will be for example dynamically set to 1234567890-us-east-1                                                                                |
| ScannerCPU               | `8192`                                       | Int    | The amount of CPU units to allocate for the scanner.                                                                |
| ScannerMemory            | `32768`                                      | Int    | The amount of memory (in MB) to allocate for the scanner.                                                           |
| ScannerHostName          | `remote-scanner`                             | String | The hostname for the BigID Scanner.                                                                                  |
| CustomScannerGroupName   | `remote-scanner`                             | String | The Scanner Group Name if the Custom option is selected.                                                            |
| BigIDRefreshSecretArn    | `arn:aws:secretsmanager:us-east-1:123456789012:secret:scanner-secret-AbCdEf`                                           | String | The ARN of the existing secret to use for BigID Scanner Token (Optional).                                            |
| BigIDHostname            | `customer.bigid.cloud`                       | String | The hostname for BigID (e.g., https://test.bigid.cloud). Please include the protocol (http:// or https://).          |
| MaximumScannerCount      | `3`                                          | Int    | The maximum number of BigID scanner instances (replicas) to run.                                                     |
| MinimumScannerCount      | `1`                                          | Int    | The minimum number of scanner instances to run in the ECS Task Definition if you would like to run 1 scanner all the time set this to 1. If you would like to scale from zero you will need to Set VALIDATE_SCANNER_GROUP=false for Orch in the BigID UI. |
| ScheduleExpression       | `rate(10 minutes)`                           | String | The schedule expression for the scaling Lambda.                                                                     |
| AttachManagedPolicy      | `false`                                      | String | Indicate whether to attach a custom managed policy to the role.                                                            |
| ManagedPolicyArn         | ``                                           | String | The ARN of the managed policy to attach to the role. This is required to access either specific resources that wouldn't be allowed or policies to allow cross account resources                                                               |
| ReplacementRepository    | `1234567890.dkr.ecr.us-east-1.amazonaws.com/bigid/bigid-scanner:release-xxx`                                           | String | The full replacement repository URL for the scanner (including tag).                                                 |
| NerReplacementRepository | `1234567890.dkr.ecr.us-east-1.amazonaws.com/bigid/bigid-ner:release-xxx`                                           | String | The full replacement repository URL for the NER scanner (including tag).                                             |
| AssignPublicIp           | `ENABLED`                                    | String | If set to DISABLED, scanners won't have public IPs. Ensure a NAT or IGW is configured for egress.                    |





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
