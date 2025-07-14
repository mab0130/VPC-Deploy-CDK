# AWS CDK VPC Deployment Script

This repository contains a reusable AWS CDK Python project that deploys a VPC with multiple CIDR blocks, subnets, and optional NAT Gateway configuration. The script uses context variables so you can easily adapt it to different environments (e.g., Prod, UAT, Test, Dev) and regions (e.g., region1 vs. region2).

## Contents

- **env_vpc_stack.py**: The main CDK script that defines your VPC, subnets, IGW, route tables, and optional NAT Gateway.
- **cdk.json**: The CDK project configuration file.
- **requirements.txt**: A list of Python dependencies required for the project.
- **README.md**: This file.

## Prerequisites

Before you begin, ensure you have the following installed:

1. **Node.js & NPM**  
   Download and install from [nodejs.org](https://nodejs.org/).

2. **AWS CLI**  
   Follow the instructions [here](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html) to install the AWS CLI.

3. **AWS CDK**  
   Install globally with:
   ```bash
   npm install -g aws-cdk
   ```

4. **Python 3.x**  
   Python 3 should be installed. We recommend using a virtual environment.

## Setup Instructions

### 1. Extract or Clone the Repository

Extract the zipped directory (or clone the repository) into your working directory.

### 2. Create and Activate a Python Virtual Environment

Navigate to your project directory and create a virtual environment:

```bash
python -m venv .venv
```

Activate the environment:

- On Linux/macOS:
  ```bash
  source .venv/bin/activate
  ```
- On Windows:
  ```powershell
  .\.venv\Scripts\activate
  ```

### 3. Install Dependencies

Install the required Python packages:

```bash
pip install -r requirements.txt
```

### 4. Configure the CDK Project

Ensure you have a file named **cdk.json** in the project root with this content:

```json
{
  "app": "python env_vpc_stack.py"
}
```

### 5. Setup AWS CLI Credentials

Make sure your AWS CLI is configured correctly. To set up a profile, run:

```bash
aws configure --profile your_profile_name
or
aws configure sso (follow prompts)
```

### 6. Bootstrap the Environment

Before you deploy, ensure your target AWS account and region is bootstrapped. Run:
This needs to be done ONLY ONCE PER Account/Region.

```bash
cdk bootstrap aws://<ACCOUNT_ID>/<REGION> --profile your_profile_name
```

For example:

```bash
cdk bootstrap aws://123456789012/us-east-1 --profile your_profile_name
```

Repeat for any additional regions (e.g., us-west-2) if needed.

### 7. Deploy the Stack

To deploy the VPC stack, use the `cdk deploy` command with the appropriate context variables. For example:

```bash
cdk deploy -c envType=prod -c cidrGroup=region1 -c useNatGateway=true -c accountId=123456789012 -c deployRegion=us-east-1 --profile your_profile_name
```

**Context Variables Explained:**

- `envType`: Should be one of `prod`, `uat`, `test`, `dev`, or `shared` (case-insensitive).
- `cidrGroup`: Either `region1` or `region2` (selects the CIDR prefix).
- `useNatGateway`: Set to `true` or `false` to enable/disable a NAT Gateway.
- `accountId`: The AWS account ID where the stack will be deployed.
- `deployRegion`: The AWS region for deployment.
- `--profile`: Specifies the AWS CLI profile to use.

### 8. Deploying Multiple Stacks in Parallel

To speed up deployments across multiple accounts or regions, you can run multiple `cdk deploy` commands concurrently. For example, you can create a shell script like the following (for Linux/macOS):

```bash

# Deploy a Production VPC to region1
cdk deploy EnvVpcStack --profile prod_profile -c envType=prod -c cidrGroup=region1 -c accountId=123456789012 -c deployRegion=us-east-1

# Deploy a UAT VPC to region2
cdk deploy EnvVpcStack --profile uat_profile -c envType=uat -c cidrGroup=region2 -c accountId=123456789012 -c deployRegion=us-west-2 

```

## Customization

You can modify the VPC configuration, CIDR mappings, subnet configurations, and resource tagging in the `env_vpc_stack.py` file to suit your needs. To make changes permanent, update the mappings or even embed additional logic based on your environment requirements.

## Summary

This project was created by RTS & provides a flexible, reusable AWS CDK VPC deployment solution. By following the steps above and supplying the necessary context values, you can deploy your VPC into multiple AWS accounts and regions quickly and efficiently.

Now, Go Build
RTS