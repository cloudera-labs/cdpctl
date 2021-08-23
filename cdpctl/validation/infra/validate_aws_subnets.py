#!/usr/bin/env python3
###
# CLOUDERA CDP Control (cdpctl)
#
# (C) Cloudera, Inc. 2021-2021
# All rights reserved.
#
# Applicable Open Source License: GNU AFFERO GENERAL PUBLIC LICENSE
#
# NOTE: Cloudera open source products are modular software products
# made up of hundreds of individual components, each of which was
# individually copyrighted.  Each Cloudera open source product is a
# collective work under U.S. Copyright Law. Your license to use the
# collective work is as provided in your written agreement with
# Cloudera.  Used apart from the collective work, this file is
# licensed for your use pursuant to the open source license
# identified above.
#
# This code is provided to you pursuant a written agreement with
# (i) Cloudera, Inc. or (ii) a third-party authorized to distribute
# this code. If you do not have a written agreement with Cloudera nor
# with an authorized and properly licensed third party, you do not
# have any rights to access nor to use this code.
#
# Absent a written agreement with Cloudera, Inc. (“Cloudera”) to the
# contrary, A) CLOUDERA PROVIDES THIS CODE TO YOU WITHOUT WARRANTIES OF ANY
# KIND; (B) CLOUDERA DISCLAIMS ANY AND ALL EXPRESS AND IMPLIED
# WARRANTIES WITH RESPECT TO THIS CODE, INCLUDING BUT NOT LIMITED TO
# IMPLIED WARRANTIES OF TITLE, NON-INFRINGEMENT, MERCHANTABILITY AND
# FITNESS FOR A PARTICULAR PURPOSE; (C) CLOUDERA IS NOT LIABLE TO YOU,
# AND WILL NOT DEFEND, INDEMNIFY, NOR HOLD YOU HARMLESS FOR ANY CLAIMS
# ARISING FROM OR RELATED TO THE CODE; AND (D)WITH RESPECT TO YOUR EXERCISE
# OF ANY RIGHTS GRANTED TO YOU FOR THE CODE, CLOUDERA IS NOT LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, PUNITIVE OR
# CONSEQUENTIAL DAMAGES INCLUDING, BUT NOT LIMITED TO, DAMAGES
# RELATED TO LOST REVENUE, LOST PROFITS, LOSS OF INCOME, LOSS OF
# BUSINESS ADVANTAGE OR UNAVAILABILITY, OR LOSS OR CORRUPTION OF
# DATA.
#
# Source File Name:  validate_aws_subnets.py
###

"""Validation of AWS Subnets."""
from typing import Any, Dict, List

import pytest
from boto3_type_annotations.iam import Client as EC2Client

from cdpctl.validation import fail, get_config_value
from cdpctl.validation.aws_utils import get_client
from cdpctl.validation.infra.issues import (
    AWS_DNS_SUPPORT_NOT_ENABLED_FOR_VPC,
    AWS_INVALID_DATA,
    AWS_INVALID_SUBNET_ID,
    AWS_NOT_ENOUGH_AZ_FOR_SUBNETS,
    AWS_NOT_ENOUGH_SUBNETS_PROVIDED,
    AWS_REQUIRED_DATA_MISSING,
    AWS_SUBNETS_DO_NOT_EXIST,
    AWS_SUBNETS_MISSING_K8S_LB_TAG,
    AWS_SUBNETS_NOT_PART_OF_VPC,
    AWS_SUBNETS_OR_VPC_WITHOUT_INTERNET_GATEWAY,
    AWS_SUBNETS_WITHOUT_INTERNET_GATEWAY,
    AWS_SUBNETS_WITHOUT_VALID_RANGE,
)

subnets_data = {}


@pytest.fixture(autouse=True, name="ec2_client")
def iam_client_fixture(config: Dict[str, Any]) -> EC2Client:
    """Return an AWS EC2 Client."""
    return get_client("ec2", config)


@pytest.mark.aws
@pytest.mark.infra
def aws_public_subnets_validation(
    config: Dict[str, Any],
    ec2_client: EC2Client,
) -> None:
    """Public subnets exist."""  # noqa: D401,E501
    public_subnets: List[str] = get_config_value(
        config,
        "infra:aws:vpc:existing:public_subnet_ids",
    )

    public_subnets = (
        [public_subnets] if isinstance(public_subnets, str) else public_subnets
    )
    if not len(public_subnets) > 2:
        fail(AWS_NOT_ENOUGH_SUBNETS_PROVIDED, subjects=["Public"])

    try:
        # query subnets
        subnets = ec2_client.describe_subnets(SubnetIds=public_subnets)
        missing_subnets = []
        for pu_id in public_subnets:
            missing_subnets.append(pu_id)
            for subnet in subnets["Subnets"]:
                if subnet["SubnetId"] == pu_id:
                    missing_subnets.remove(pu_id)
        if len(missing_subnets) > 0:
            fail(AWS_SUBNETS_DO_NOT_EXIST, subjects="Public", resources=missing_subnets)
        subnets_data["public_subnets"] = subnets["Subnets"]
        subnets_data["public_subnets_ids"] = public_subnets
    except KeyError as e:
        fail(AWS_REQUIRED_DATA_MISSING, e.args[0])
    except ec2_client.exceptions.ClientError as ce:
        fail(AWS_INVALID_SUBNET_ID, subjects=["Public", ce.args[0]])


@pytest.mark.aws
@pytest.mark.infra
@pytest.mark.dependency(depends=["aws_public_subnets_validation"])
def aws_public_subnets_availablity_zone_validation() -> None:
    """Public subnets have minimum two availability zones."""  # noqa: D401,E501
    try:
        azs = []
        for subnet in subnets_data["public_subnets"]:
            if subnet["AvailabilityZone"] not in azs:
                azs.append(subnet["AvailabilityZone"])

        # minimum two availability zones validations
        if len(azs) <= 1:
            fail(AWS_NOT_ENOUGH_AZ_FOR_SUBNETS, subjects=["Public"])
    except KeyError as e:
        fail(AWS_REQUIRED_DATA_MISSING, e.args[0])


@pytest.mark.aws
@pytest.mark.infra
@pytest.mark.dependency(depends=["aws_public_subnets_validation"])
def aws_public_subnets_route_validation(
    config: Dict[str, Any],
    ec2_client: EC2Client,
) -> None:
    """Public subnets have internet gateway(s)."""  # noqa: D401,E501
    try:
        subnets_route_tables = ec2_client.describe_route_tables(
            Filters=[
                {
                    "Name": "association.subnet-id",
                    "Values": subnets_data["public_subnets_ids"],
                },
                {
                    "Name": "route.state",
                    "Values": ["active"],
                },
            ]
        )["RouteTables"]
        vpc_id: List[str] = get_config_value(
            config,
            "infra:aws:vpc:existing:vpc_id",
        )
        Filters = [
            {
                "Name": "attachment.vpc-id",
                "Values": [vpc_id],
            },
            {
                "Name": "attachment.state",
                "Values": ["available"],
            },
        ]
        igws = ec2_client.describe_internet_gateways(Filters=Filters)[
            "InternetGateways"
        ]
        if len(igws) > 0 and len(subnets_route_tables) > 0:
            igw_ids = [i["InternetGatewayId"] for i in igws]
            gateway_ids = []
            for route_table in subnets_route_tables:
                routes = route_table["Routes"]
                for route in routes:
                    if "GatewayId" in route:
                        gateway_ids.append(route["GatewayId"])
        else:
            fail(
                AWS_SUBNETS_OR_VPC_WITHOUT_INTERNET_GATEWAY,
                subjects=["Public", vpc_id],
                resources=subnets_data["public_subnets_ids"],
            )

        if not set(igw_ids) & set(gateway_ids):
            fail(
                AWS_SUBNETS_WITHOUT_INTERNET_GATEWAY,
                subjects=["Public"],
                resources=subnets_data["public_subnets_ids"],
            )

    except KeyError as e:
        fail(AWS_REQUIRED_DATA_MISSING, e.args[0])
    except ec2_client.exceptions.ClientError as ce:
        fail(AWS_INVALID_DATA, ce.args[0])


@pytest.mark.aws
@pytest.mark.infra
@pytest.mark.dependency(depends=["aws_public_subnets_validation"])
def aws_public_subnets_range_validation() -> None:
    """Public subnets have adequate CIDR range."""  # noqa: D401,E501
    try:
        subnets_wo_valid_range = []
        for subnet in subnets_data["public_subnets"]:
            cidrblock_range = subnet["CidrBlock"].split("/")[1]
            if int(cidrblock_range) > 24:
                subnets_wo_valid_range.append(subnet["SubnetId"])

        if len(subnets_wo_valid_range) > 0:
            fail(
                AWS_SUBNETS_WITHOUT_VALID_RANGE,
                subjects=["Public"],
                resources=subnets_wo_valid_range,
            )
    except KeyError as e:
        fail(AWS_REQUIRED_DATA_MISSING, e.args[0])


@pytest.mark.aws
@pytest.mark.infra
@pytest.mark.dependency(depends=["aws_public_subnets_validation"])
def aws_public_subnets_tags_validation() -> None:
    """Public subnets contain the necessary tags."""  # noqa: D401,E501
    try:
        subnets_w_valid_tag: Dict[str, bool] = {}
        # validating tag kubernetes.io/role/elb on public subnets
        for subnet in subnets_data["public_subnets"]:
            subnets_w_valid_tag[subnet["SubnetId"]] = False
            for tag in subnet["Tags"]:
                if tag["Key"] == "kubernetes.io/role/elb" and tag["Value"] == "1":
                    subnets_w_valid_tag[subnet["SubnetId"]] = True
                continue

        subnet_missing_tags = [k for k, v in subnets_w_valid_tag.items() if not v]

        if len(subnet_missing_tags) > 0:
            fail(
                AWS_SUBNETS_MISSING_K8S_LB_TAG,
                subjects=["Public"],
                resources=subnet_missing_tags,
            )
    except KeyError as e:
        fail(AWS_REQUIRED_DATA_MISSING, e.args[0])


@pytest.mark.aws
@pytest.mark.infra
def aws_private_subnets_validation(
    config: Dict[str, Any],
    ec2_client: EC2Client,
) -> None:
    """Private subnets exist."""  # noqa: D401,E501
    private_subnets: List[str] = get_config_value(
        config,
        "infra:aws:vpc:existing:private_subnet_ids",
    )
    private_subnets = (
        [private_subnets] if isinstance(private_subnets, str) else private_subnets
    )
    if not len(private_subnets) > 2:
        fail(AWS_NOT_ENOUGH_SUBNETS_PROVIDED, subjects=["Private"])

    try:
        # query subnets
        subnets = ec2_client.describe_subnets(SubnetIds=private_subnets)
        missing_subnets = []
        for pvt_id in private_subnets:
            missing_subnets.append(pvt_id)
            for subnet in subnets["Subnets"]:
                if subnet["SubnetId"] == pvt_id:
                    missing_subnets.remove(pvt_id)
        if len(missing_subnets) > 0:
            fail(
                AWS_SUBNETS_DO_NOT_EXIST, subjects="Private", resources=missing_subnets
            )
        subnets_data["private_subnets"] = subnets["Subnets"]
        subnets_data["private_subnets_ids"] = private_subnets
    except KeyError as e:
        fail(AWS_REQUIRED_DATA_MISSING, e.args[0])
    except ec2_client.exceptions.ClientError as ce:
        fail(AWS_INVALID_SUBNET_ID, subjects=["Private", ce.args[0]])


@pytest.mark.aws
@pytest.mark.infra
@pytest.mark.dependency(depends=["aws_private_subnets_validation"])
def aws_private_subnets_availablity_zone_validation() -> None:
    """Private subnets have minimum two availability zones."""  # noqa: D401,E501
    try:
        azs = []
        for subnet in subnets_data["private_subnets"]:
            if subnet["AvailabilityZone"] not in azs:
                azs.append(subnet["AvailabilityZone"])

        # minimum two availability zones validations
        if len(azs) <= 1:
            fail(AWS_NOT_ENOUGH_AZ_FOR_SUBNETS, subjects=["Private"])

    except KeyError as e:
        fail(AWS_REQUIRED_DATA_MISSING, e.args[0])


@pytest.mark.aws
@pytest.mark.infra
@pytest.mark.dependency(depends=["aws_private_subnets_validation"])
def aws_private_subnets_route_validation(
    config: Dict[str, Any],
    ec2_client: EC2Client,
) -> None:
    """Private subnets have NAT gateway(s)."""  # noqa: D401,E501
    try:
        subnets_route_tables = ec2_client.describe_route_tables(
            Filters=[
                {
                    "Name": "association.subnet-id",
                    "Values": subnets_data["private_subnets_ids"],
                },
                {
                    "Name": "route.state",
                    "Values": ["active"],
                },
            ]
        )["RouteTables"]
        vpc_id: List[str] = get_config_value(
            config,
            "infra:aws:vpc:existing:vpc_id",
        )
        Filters = [
            {
                "Name": "vpc-id",
                "Values": [vpc_id],
            },
            {
                "Name": "state",
                "Values": ["available"],
            },
        ]
        nat_gws = ec2_client.describe_nat_gateways(Filters=Filters)["NatGateways"]
        if len(nat_gws) > 0 and len(subnets_route_tables) > 0:
            igw_ids = [i["NatGatewayId"] for i in nat_gws]
            gateway_ids = []
            for route_table in subnets_route_tables:
                routes = route_table["Routes"]
                for route in routes:
                    if "NatGatewayId" in route:
                        gateway_ids.append(route["NatGatewayId"])
        else:
            fail(
                AWS_SUBNETS_OR_VPC_WITHOUT_INTERNET_GATEWAY,
                subjects=["Private", vpc_id],
                resources=subnets_data["public_subnets_ids"],
            )
        if not set(igw_ids) & set(gateway_ids):
            fail(
                AWS_SUBNETS_WITHOUT_INTERNET_GATEWAY,
                subjects=["Private"],
                resources=subnets_data["public_subnets_ids"],
            )

    except KeyError as e:
        fail(AWS_REQUIRED_DATA_MISSING, e.args[0])
    except ec2_client.exceptions.ClientError as ce:
        fail(AWS_INVALID_DATA, ce.args[0])


@pytest.mark.aws
@pytest.mark.infra
@pytest.mark.dependency(depends=["aws_private_subnets_validation"])
def aws_private_subnets_range_validation() -> None:
    """Private subnets have adequate CIDR range."""  # noqa: D401,E501
    try:
        subnets_wo_valid_range = []
        for subnet in subnets_data["private_subnets"]:
            cidrblock_range = subnet["CidrBlock"].split("/")[1]
            if int(cidrblock_range) > 19:
                subnets_wo_valid_range.append(subnet["SubnetId"])

        if len(subnets_wo_valid_range) > 0:
            fail(
                AWS_SUBNETS_WITHOUT_VALID_RANGE,
                subjects=["Private"],
                resources=subnets_wo_valid_range,
            )
    except KeyError as e:
        fail(AWS_REQUIRED_DATA_MISSING, e.args[0])


@pytest.mark.aws
@pytest.mark.infra
@pytest.mark.dependency(depends=["aws_private_subnets_validation"])
def aws_private_subnets_tags_validation() -> None:
    """Private subnets have the necessary tags."""  # noqa: D401,E501
    try:
        subnets_w_valid_tag: Dict[str, bool] = {}
        # validating tag kubernetes.io/role/internal-elb on private subnets
        for subnet in subnets_data["private_subnets"]:
            subnets_w_valid_tag[subnet["SubnetId"]] = False
            for tag in subnet["Tags"]:
                if (
                    tag["Key"] == "kubernetes.io/role/internal-elb"
                    and tag["Value"] == "1"
                ):
                    subnets_w_valid_tag[subnet["SubnetId"]] = True
                continue

        subnet_missing_tags = [k for k, v in subnets_w_valid_tag.items() if not v]

        if len(subnet_missing_tags) > 0:
            fail(
                AWS_SUBNETS_MISSING_K8S_LB_TAG,
                subjects=["Private"],
                resources=subnet_missing_tags,
            )
    except KeyError as e:
        fail(AWS_REQUIRED_DATA_MISSING, e.args[0])


@pytest.mark.aws
@pytest.mark.infra
@pytest.mark.dependency(depends=["aws_private_subnets_validation"])
def aws_private_subnets_auto_assign_ip_validation() -> None:
    """Private subnets have auto-assign public IPs disabled."""  # noqa: D401,E501
    try:
        subnets_w_public_ips_enabled = []
        for subnet in subnets_data["private_subnets"]:
            if subnet["MapPublicIpOnLaunch"]:
                subnets_w_public_ips_enabled.append(subnet["SubnetId"])

        if len(subnets_w_public_ips_enabled) > 0:
            pytest.fail(
                f"""Private subnet(s) {subnets_w_public_ips_enabled} have
                'Auto-assign Public IPs' enabled.""",
                False,
            )
    except KeyError as e:
        pytest.fail(f"Validation error - missing required data : {e.args[0]}", False)


@pytest.mark.aws
@pytest.mark.infra
@pytest.mark.dependency(
    depends=["aws_private_subnets_validation", "aws_public_subnets_validation"]
)
def aws_vpc_subnets_validation(
    config: Dict[str, Any],
    ec2_client: EC2Client,
) -> None:
    """The VPC has the defined public and private subnets."""  # noqa: D401,E501
    vpc_id: List[str] = get_config_value(
        config,
        "infra:aws:vpc:existing:vpc_id",
    )
    try:
        vpc_d = ec2_client.describe_vpcs(VpcIds=[vpc_id])
        filters = [{"Name": "vpc-id", "Values": [vpc_d["Vpcs"][0]["VpcId"]]}]
        subnets_new = ec2_client.describe_subnets(Filters=filters)["Subnets"]
        vpc_subnets = [i["SubnetId"] for i in subnets_new]
        # check provided subnets belong to provided vpc
        missing_subnets = []
        for private_id in subnets_data["private_subnets_ids"]:
            if private_id not in vpc_subnets:
                missing_subnets.append(private_id)
        for public_id in subnets_data["public_subnets_ids"]:
            if public_id not in vpc_subnets:
                missing_subnets.append(public_id)

        if len(missing_subnets) > 0:
            fail(
                AWS_SUBNETS_NOT_PART_OF_VPC,
                subjects=[vpc_id],
                resources=missing_subnets,
            )

        # DNS names and DNS resolution enabled
        enable_dns_support = ec2_client.describe_vpc_attribute(
            VpcId=vpc_d["Vpcs"][0]["VpcId"], Attribute="enableDnsSupport"
        )["EnableDnsSupport"]["Value"]
        enable_dns_hostnames = ec2_client.describe_vpc_attribute(
            VpcId=vpc_d["Vpcs"][0]["VpcId"], Attribute="enableDnsHostnames"
        )["EnableDnsHostnames"]["Value"]

        if not (enable_dns_hostnames and enable_dns_support):
            fail(AWS_DNS_SUPPORT_NOT_ENABLED_FOR_VPC, subjects=[vpc_id])
    except KeyError as e:
        fail(AWS_REQUIRED_DATA_MISSING, e.args[0])
    except ec2_client.exceptions.ClientError as ce:
        fail(AWS_INVALID_DATA, ce.args[0])
