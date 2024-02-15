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

## Mandatory Input Variables for Cloudformation


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
This is the required Lambda that is being utilized for scaling up and scaling down the ECS Scanner Containers. This is created specifically to interact with your cloud tenant, and monitor your tenant to see if there are any active jobs currently available. The lambda communicates with the ECS Scanner Task Definitions and based upon the parameter Scanner Count, which when a scan job kicks off, it will create the maximum amount of scanners to pick up work from the BigID Tenant, and then be assigned to running a scan during that time. Once it has completed its job, it will return back to 1, which is the minimum scanner count.

#### ECS Scanner Cluster
This is the hierachical object that is required to spin up the following resources which are the ECS Scanner Task Definitions / ECS Scanner Services.

##### Scanner Task Definition

This Task Definition is responsible for the configuration of the Scanner, this sets all of the container environment variables, and is responsible for the amount of replicas of scanners.

##### BigID Scanner

Scanner Pod that is scaled out from the Task Definition

##### BigID Ner 

Sidecar container in tandem with scanner pod that utilizes NER
