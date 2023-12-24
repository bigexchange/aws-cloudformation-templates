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
| SecurityGroupName | `sg-123456`                                 | String |
| SubnetName        | `subnet-123456`                              | String |
| NerEnabled        | `false`                                      | Bool   |
