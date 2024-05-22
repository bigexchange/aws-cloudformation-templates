# Cloud Native Scanners on ECS

## Requirements

* BigID Scanner Images Uploaded to the ECR account where the cluster will be deployed.
* A Security Group with Egress Access to the Public Internet and a Subnet Corresponding with the same Security Group within the same VPC (if you have an existing VPC you would like to utilize).

## Using CloudFormation

## Creating a Stack for Your Networking Infrastructure

Using the provided CloudFormation template, navigate to the CloudFormation AWS option to start creating the required stack for your ECS Cluster Infrastructure (Your VPC). This will create 3 private subnets and 1 public subnet, which will contain your NAT Gateway and an Internet Gateway, required to access the public internet from the 3 private subnets. You can use this infrastructure to provision what is necessary to get your ECS Cluster working.

**CloudFormation** **>** **Stack** **>** **Create a New Stack**

Using the provided CloudFormation template, navigate to the CloudFormation AWS option to start creating the required stack for your ECS Cluster, and input the following required variables.

| Parameter         | Type   | Default       | Description                          |
|-------------------|--------|---------------|--------------------------------------|
| VpcCidr           | String | 10.0.0.0/16   | The CIDR block for the VPC.          |
| PrivateSubnet1Cidr| String | 10.0.1.0/24   | The CIDR block for the first private subnet. |
| PrivateSubnet2Cidr| String | 10.0.2.0/24   | The CIDR block for the second private subnet. |
| PrivateSubnet3Cidr| String | 10.0.3.0/24   | The CIDR block for the third private subnet. |
| PublicSubnetCidr  | String | 10.0.0.0/24   | The CIDR block for the public subnet.|

### Creating a Stack for Your ECS Cluster

**CloudFormation** **>** **Stack** **>** **Create a New Stack**

![image](https://github.com/bigexchange/aws-cloudformation-templates/assets/34100385/28b47a8c-e271-4fa0-97b4-4aded668195e)

Upload the CloudFormation Template, and input the following variables below.



```
https://raw.githubusercontent.com/bigexchange/aws-cloudformation-templates/main/bigid/solutions/CloudNativeScanner/scanner.yaml
```


## Mandatory Input Variables for CloudFormation ECS Cluster Creation

| Key               | Value                                        | Type   |
|-------------------|----------------------------------------------|--------|
| BigIDRefreshToken | `TOKEN`                                      | String |
| BigIDUIHostname   | `customer.bigid.cloud`                       | String |
| ImageRepository   | `1234567890.dkr.ecr.us-east-1.amazonaws.com` | String |
| ImageTagVersion   | `release-xxx`                                | String |
| SecurityGroupName | `sg-123456`                                  | String |
| SubnetName        | `subnet-123456`                              | String |
| NerEnabled        | `false`                                      | Bool   |
| ScannerCount      | `3`                                          | Int    |

## ECS Diagram

![ecsdiagram](https://github.com/bigexchange/aws-cloudformation-templates/assets/34100385/6d972dba-70bc-4f90-b407-56762a8581ed)

### ECS Diagram Explanation

#### customer.bigid.cloud
The customer tenant hosted in the cloud.

#### ECS Scaler Lambda
This is the required Lambda that is utilized for scaling up and scaling down the ECS Scanner Containers. It interacts with your cloud tenant and monitors your tenant to see if there are any active jobs currently available. The lambda communicates with the ECS Scanner Task Definitions, and based on the parameter Scanner Count, it will create the maximum number of scanners to pick up work from the BigID Tenant when a scan job kicks off. Once it has completed its job, it will return back to 1, which is the minimum scanner count.

#### ECS Scanner Cluster
This is the hierarchical object required to spin up the following resources: the ECS Scanner Task Definitions and ECS Scanner Services.

##### Scanner Task Definition
This Task Definition is responsible for the configuration of the Scanner. It sets all the container environment variables and is responsible for the number of replicas of scanners.

##### BigID Scanner
Scanner Pod that is scaled out from the Task Definition.

##### BigID Ner
Sidecar container in tandem with the scanner pod that utilizes NER.
