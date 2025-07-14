# VPC-Deploy-CDK

A Python-based AWS CDK script for deploying environment-specific VPCs with standardized CIDR blocks and subnet configurations.

## Overview

This CDK application creates a VPC with dual CIDR blocks, public and private subnets across two availability zones, and optional NAT gateway functionality. The CIDR blocks are automatically assigned based on environment type and region group.

## Features

- **Environment-specific CIDR allocation**: Automatic CIDR block assignment based on environment type (prod, uat, test, dev, shared)
- **Dual CIDR blocks**: Primary block for public subnets, additional block for private subnets
- **Multi-AZ deployment**: Subnets across two availability zones for high availability
- **Optional NAT Gateway**: Configurable NAT gateway for private subnet internet access
- **Comprehensive tagging**: All resources tagged with descriptive names for easy identification

## CIDR Block Allocation

### Region 1 (Default)
- **Production**: `10.10.x.x`
- **UAT**: `10.20.x.x`
- **Test**: `10.30.x.x`
- **Development**: `10.40.x.x`
- **Shared**: `10.50.x.x`

### Region 2
- **Production**: `10.100.x.x`
- **UAT**: `10.120.x.x`
- **Test**: `10.130.x.x`
- **Development**: `10.140.x.x`
- **Shared**: `10.150.x.x`

## Subnet Configuration

For each environment, the following subnets are created:

- **Public Subnet A**: `{prefix}.60.0/25` (AZ-A)
- **Public Subnet B**: `{prefix}.60.128/25` (AZ-B)
- **Private Subnet A**: `{prefix}.70.0/25` (AZ-A)
- **Private Subnet B**: `{prefix}.70.128/25` (AZ-B)

## Prerequisites

- Python 3.7+
- AWS CDK CLI installed
- AWS credentials configured
- Valid AWS account with appropriate permissions

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd VPC-Deploy-CDK
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Bootstrap CDK (if not already done):
```bash
cdk bootstrap
```

## Usage

### Basic Deployment

Deploy a development VPC in region1:
```bash
cdk deploy -c envType=dev
```

### Configuration Options

The deployment accepts the following context parameters:

- `envType` (required): Environment type - `prod`, `uat`, `test`, `dev`, or `shared`
- `cidrGroup` (optional): Region group - `region1` (default) or `region2`
- `useNatGateway` (optional): Enable NAT Gateway - `true` (default) or `false`
- `accountId` (optional): AWS account ID (defaults to "YOUR_ACCOUNT_ID")
- `deployRegion` (optional): Deployment region (defaults to "us-east-1")

### Deployment Examples

**Production VPC in region2 with NAT Gateway:**
```bash
cdk deploy -c envType=prod -c cidrGroup=region2 -c useNatGateway=true
```

**Test VPC without NAT Gateway:**
```bash
cdk deploy -c envType=test -c useNatGateway=false
```

**UAT VPC with specific account and region:**
```bash
cdk deploy -c envType=uat -c accountId=123456789012 -c deployRegion=us-west-2
```

## Architecture

The deployed infrastructure includes:

- **VPC** with primary and additional CIDR blocks
- **Internet Gateway** for public internet access
- **Public Subnets** (2) with auto-assigned public IPs
- **Private Subnets** (2) without public IPs
- **Route Tables** for public and private subnets
- **NAT Gateway** (optional) with Elastic IP for private subnet internet access

## File Structure

```
VPC-Deploy-CDK/
├── env_vpc_stack.py    # Main CDK stack implementation
├── cdk.json           # CDK configuration
├── requirements.txt   # Python dependencies
└── README.md         # This file
```

## Development

To modify the stack:

1. Edit `env_vpc_stack.py` to customize the VPC configuration
2. Update `requirements.txt` if adding new dependencies
3. Test changes with `cdk diff` before deployment
4. Use `cdk synth` to generate CloudFormation templates

## Troubleshooting

**Common Issues:**

1. **Missing envType**: Ensure you provide the `-c envType=<env>` parameter
2. **Invalid environment**: Check that envType is one of: prod, uat, test, dev, shared
3. **Permission errors**: Verify AWS credentials have VPC creation permissions
4. **Region availability**: Ensure the target region has at least 2 availability zones

## Clean Up

To destroy the deployed resources:
```bash
cdk destroy
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License.