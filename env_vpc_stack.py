#!/usr/bin/env python3
"""
This CDK script creates a VPC with two CIDR blocks based on the environment type and region group.
The mapping (all lower-case) is defined as follows:

region1:
  - prod = 10.10.x.x
  - uat  = 10.20.x.x
  - test = 10.30.x.x
  - dev  = 10.40.x.x

region2:
  - prod = 10.100.x.x
  - uat  = 10.120.x.x
  - test = 10.130.x.x
  - dev  = 10.140.x.x

The VPC is built with:
  - Primary CIDR: {prefix}.60.0/23   (used for public subnets)
  - Additional CIDR: {prefix}.70.0/23  (used for private subnets)

Subnets:
  - Public Subnet A: {prefix}.60.0/25   in AZ-A
  - Public Subnet B: {prefix}.60.128/25  in AZ-B
  - Private Subnet A: {prefix}.70.0/25   in AZ-A
  - Private Subnet B: {prefix}.70.128/25  in AZ-B

Optionally, if useNatGateway is true, a NAT gateway is created in Public Subnet A.
All major resources are tagged with a "Name" so they’re identifiable in the AWS Console.
"""

import aws_cdk as cdk
from aws_cdk import Stack, Environment, Tags
from constructs import Construct
from aws_cdk.aws_ec2 import (
    CfnVPC,
    CfnVPCCidrBlock,
    CfnSubnet,
    CfnInternetGateway,
    CfnVPCGatewayAttachment,
    CfnRouteTable,
    CfnRoute,
    CfnSubnetRouteTableAssociation,
    CfnEIP,
    CfnNatGateway,
)

class EnvVpcStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # 1. Retrieve context variables.
        # envType should be one of "prod", "uat", "test", "dev", or "shared" (in lower-case)
        env_type = self.node.try_get_context("envType")
        cidr_group = self.node.try_get_context("cidrGroup") or "region1"
        use_nat = self.node.try_get_context("useNatGateway")
        if use_nat is None:
            use_nat = True
        else:
            use_nat = str(use_nat).lower() == "true"

        if not env_type:
            raise ValueError("Please supply a context variable 'envType' (prod, uat, test, dev, or shared).")

        # Normalize env_type to lower-case
        env_type_clean = env_type.lower()

        # 2. Define the mapping (keys in lower-case)
        cidr_map = {
            "prod": {"region1": "10.10", "region2": "10.100"},
            "uat":  {"region1": "10.20", "region2": "10.120"},
            "test": {"region1": "10.30", "region2": "10.130"},
            "dev":  {"region1": "10.40", "region2": "10.140"},
            "shared": {"region1": "10.50", "region2": "10.150"},
        }

        if env_type_clean not in cidr_map:
            raise ValueError(f"Unsupported envType '{env_type}'. Must be one of {list(cidr_map.keys())}.")

        # Get the appropriate CIDR prefix.
        prefix = cidr_map[env_type_clean][cidr_group]

        # 3. Compute the two VPC CIDRs.
        primary_vpc_cidr = f"{prefix}.60.0/23"    # For public subnets.
        additional_vpc_cidr = f"{prefix}.70.0/23"   # For private subnets.

        # 4. Create the VPC with the primary CIDR block.
        vpc = CfnVPC(
            self,
            "Vpc",
            cidr_block=primary_vpc_cidr
        )
        # Tag the VPC.
        Tags.of(vpc).add("Name", f"{env_type_clean.capitalize()}-VPC-{cidr_group}")

        # 5. Associate the additional CIDR block.
        vpc_additional = CfnVPCCidrBlock(
            self,
            "VpcAdditionalCidr",
            vpc_id=vpc.ref,
            cidr_block=additional_vpc_cidr
        )

        # 6. Create an Internet Gateway and attach it.
        igw = CfnInternetGateway(
            self,
            "InternetGateway"
        )
        Tags.of(igw).add("Name", f"{env_type_clean.capitalize()}-IGW-{cidr_group}")

        igw_attachment = CfnVPCGatewayAttachment(
            self,
            "IgwAttachment",
            vpc_id=vpc.ref,
            internet_gateway_id=igw.ref
        )

        # 7. Determine Availability Zones (assumes AZ naming convention like us-east-1a, us-east-1b, etc.)
        region = self.region if self.region is not None else "us-east-1"
        az_a = f"{region}a"
        az_b = f"{region}b"

        # 8. Create Public Subnets (from the primary CIDR block).
        public_subnet_a = CfnSubnet(
            self,
            "PublicSubnetA",
            cidr_block=f"{prefix}.60.0/25",
            vpc_id=vpc.ref,
            availability_zone=az_a,
            map_public_ip_on_launch=True
        )
        Tags.of(public_subnet_a).add("Name", f"{env_type_clean.capitalize()}-PublicSubnet-A-{cidr_group}")

        public_subnet_b = CfnSubnet(
            self,
            "PublicSubnetB",
            cidr_block=f"{prefix}.60.128/25",
            vpc_id=vpc.ref,
            availability_zone=az_b,
            map_public_ip_on_launch=True
        )
        Tags.of(public_subnet_b).add("Name", f"{env_type_clean.capitalize()}-PublicSubnet-B-{cidr_group}")

        # 9. Create Private Subnets (from the additional CIDR block).
        private_subnet_a = CfnSubnet(
            self,
            "PrivateSubnetA",
            cidr_block=f"{prefix}.70.0/25",
            vpc_id=vpc.ref,
            availability_zone=az_a,
            map_public_ip_on_launch=False
        )
        Tags.of(private_subnet_a).add("Name", f"{env_type_clean.capitalize()}-PrivateSubnet-A-{cidr_group}")

        private_subnet_b = CfnSubnet(
            self,
            "PrivateSubnetB",
            cidr_block=f"{prefix}.70.128/25",
            vpc_id=vpc.ref,
            availability_zone=az_b,
            map_public_ip_on_launch=False
        )
        Tags.of(private_subnet_b).add("Name", f"{env_type_clean.capitalize()}-PrivateSubnet-B-{cidr_group}")

        # Ensure the additional CIDR is associated before creating private subnets.
        private_subnet_a.add_dependency(vpc_additional)
        private_subnet_b.add_dependency(vpc_additional)

        # 10. Create a Public Route Table with a default route via the IGW.
        public_rt = CfnRouteTable(
            self,
            "PublicRouteTable",
            vpc_id=vpc.ref
        )
        Tags.of(public_rt).add("Name", f"{env_type_clean.capitalize()}-PublicRT-{cidr_group}")
        CfnRoute(
            self,
            "PublicDefaultRoute",
            route_table_id=public_rt.ref,
            destination_cidr_block="0.0.0.0/0",
            gateway_id=igw.ref
        )
        CfnSubnetRouteTableAssociation(
            self,
            "PublicSubnetA_RT_Assoc",
            subnet_id=public_subnet_a.ref,
            route_table_id=public_rt.ref
        )
        CfnSubnetRouteTableAssociation(
            self,
            "PublicSubnetB_RT_Assoc",
            subnet_id=public_subnet_b.ref,
            route_table_id=public_rt.ref
        )

        # 11. Configure Private Subnet route tables.
        if use_nat:
            # Create a NAT gateway in Public Subnet A.
            nat_eip = CfnEIP(
                self,
                "NatEip",
                domain="vpc"
            )
            nat_gw = CfnNatGateway(
                self,
                "NatGateway",
                subnet_id=public_subnet_a.ref,
                allocation_id=nat_eip.attr_allocation_id
            )
            Tags.of(nat_gw).add("Name", f"{env_type_clean.capitalize()}-NATGateway-{cidr_group}")

            # Private Subnet A route table with NAT.
            private_rt_a = CfnRouteTable(
                self,
                "PrivateRouteTableA",
                vpc_id=vpc.ref
            )
            Tags.of(private_rt_a).add("Name", f"{env_type_clean.capitalize()}-PrivateRT-A-{cidr_group}")
            CfnRoute(
                self,
                "PrivateDefaultRouteA",
                route_table_id=private_rt_a.ref,
                destination_cidr_block="0.0.0.0/0",
                nat_gateway_id=nat_gw.ref
            )
            CfnSubnetRouteTableAssociation(
                self,
                "PrivateSubnetA_RT_Assoc",
                subnet_id=private_subnet_a.ref,
                route_table_id=private_rt_a.ref
            )

            # Private Subnet B route table with NAT.
            private_rt_b = CfnRouteTable(
                self,
                "PrivateRouteTableB",
                vpc_id=vpc.ref
            )
            Tags.of(private_rt_b).add("Name", f"{env_type_clean.capitalize()}-PrivateRT-B-{cidr_group}")
            CfnRoute(
                self,
                "PrivateDefaultRouteB",
                route_table_id=private_rt_b.ref,
                destination_cidr_block="0.0.0.0/0",
                nat_gateway_id=nat_gw.ref
            )
            CfnSubnetRouteTableAssociation(
                self,
                "PrivateSubnetB_RT_Assoc",
                subnet_id=private_subnet_b.ref,
                route_table_id=private_rt_b.ref
            )
        else:
            # Without NAT, create empty route tables for private subnets.
            private_rt_a = CfnRouteTable(
                self,
                "PrivateRouteTableA_NoNat",
                vpc_id=vpc.ref
            )
            Tags.of(private_rt_a).add("Name", f"{env_type_clean.capitalize()}-PrivateRT-A-NoNAT-{cidr_group}")
            CfnSubnetRouteTableAssociation(
                self,
                "PrivateSubnetA_RT_Assoc_NoNat",
                subnet_id=private_subnet_a.ref,
                route_table_id=private_rt_a.ref
            )

            private_rt_b = CfnRouteTable(
                self,
                "PrivateRouteTableB_NoNat",
                vpc_id=vpc.ref
            )
            Tags.of(private_rt_b).add("Name", f"{env_type_clean.capitalize()}-PrivateRT-B-NoNAT-{cidr_group}")
            CfnSubnetRouteTableAssociation(
                self,
                "PrivateSubnetB_RT_Assoc_NoNat",
                subnet_id=private_subnet_b.ref,
                route_table_id=private_rt_b.ref
            )


app = cdk.App()

# Set the environment for deployment. You can pass account and region via context,
# or replace "YOUR_ACCOUNT_ID" with your actual account number.
env_params = Environment(
    account=app.node.try_get_context("accountId") or "YOUR_ACCOUNT_ID",
    region=app.node.try_get_context("deployRegion") or "us-east-1"
)

EnvVpcStack(app, "EnvVpcStack", env=env_params)

app.synth()
