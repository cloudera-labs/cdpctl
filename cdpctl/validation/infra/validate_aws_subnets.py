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

from cdpctl.validation import get_config_value
from cdpctl.validation.aws_utils import get_client

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
        key_missing_message="No public subnets defined for config option: {0}",
        data_expected_error_message="No public subnets were provided for config option: {0}",  # noqa: E501
    )
    if not len(public_subnets) > 2:
        pytest.fail("Not enough subnets provided, at least 3 subnets required.", False)

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
            pytest.fail(
                f"Subnets ({missing_subnets}) do not exist.",
                False,
            )
        subnets_data["public_subnets"] = subnets["Subnets"]
        subnets_data["public_subnets_ids"] = public_subnets
    except KeyError as e:
        pytest.fail(f"Validation error - missing required data : {e.args[0]}", False)


@pytest.mark.aws
@pytest.mark.infra
@pytest.mark.dependency(depends=["aws_public_subnets_validation"])
@pytest.mark.skip(reason="Suffixes are not part of config at this time.")
def aws_public_subnets_suffix_validation(config: Dict[str, Any]) -> None:
    """Public subnets have the defined suffix."""  # noqa: D401,E501
    public_subnets_suffix: List[str] = get_config_value(
        config,
        "infra:aws:vpc:existing:public_subnets_suffix",
        key_missing_message="No public subnets suffix defined for config option: {0}",
        data_expected_error_message="No public subnets suffix was provided for config option: {0}",  # noqa: E501
    )
    try:
        subnets_wo_valid_suffix = []
        for subnet_id in subnets_data["public_subnets_ids"]:
            if not subnet_id.endswith(public_subnets_suffix):
                subnets_wo_valid_suffix.append(subnet_id)

        if len(subnets_wo_valid_suffix) > 0:
            pytest.fail(
                f"Subnets ({subnets_wo_valid_suffix}) without valid suffix ({public_subnets_suffix}).",  # noqa: E501
                False,
            )
    except KeyError as e:
        pytest.fail(f"Validation error - missing required data : {e.args[0]}", False)


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
            pytest.fail(
                """Not enough availability zones, subnets should be in
            atleast 2 availability zones.""",
                False,
            )
    except KeyError as e:
        pytest.fail(f"Validation error - missing required data : {e.args[0]}", False)


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
            key_missing_message="No VPC id defined for config option: {0}",
            data_expected_error_message="No VPC id was provided for config option: {0}",
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
            pytest.fail(
                f"""Provided subnets {subnets_data["public_subnets_ids"]} and
                or VPC {vpc_id} do not have internet gateway(s).""",
                False,
            )

        if not set(igw_ids) & set(gateway_ids):
            pytest.fail(
                f"""Provided subnets {subnets_data["public_subnets_ids"]} do not
                have internet gateway(s).""",
                False,
            )

    except KeyError as e:
        pytest.fail(f"Validation error - missing required data : {e.args[0]}", False)


@pytest.mark.aws
@pytest.mark.infra
@pytest.mark.dependency(depends=["aws_public_subnets_validation"])
def aws_public_subnets_range_validation() -> None:
    """Public subnets have adequate IP range."""  # noqa: D401,E501
    try:
        subnets_wo_valid_range = []
        for subnet in subnets_data["public_subnets"]:
            cidrblock_range = subnet["CidrBlock"].split("/")[1]
            if int(cidrblock_range) < 24:
                subnets_wo_valid_range.append(subnet["SubnetId"])

        if len(subnets_wo_valid_range) > 0:
            pytest.fail(
                f"Public subnets ({subnets_wo_valid_range}) without valid required range.",  # noqa: E501
                False,
            )
    except KeyError as e:
        pytest.fail(f"Validation error - missing required data : {e.args[0]}", False)


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
            pytest.fail(
                f"""Public subnet(s) {subnet_missing_tags} missing tag
                'kubernetes.io/role/elb'.""",
                False,
            )
    except KeyError as e:
        pytest.fail(f"Validation error - missing required data : {e.args[0]}", False)


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
        key_missing_message="No private subnets defined for config option: {0}",
        data_expected_error_message="No private subnets were provided for config "
        "option: {0}",
    )
    if not len(private_subnets) > 2:
        pytest.fail("Not enough subnets provided, at least 3 subnets required.", False)

    # query subnets
    subnets = ec2_client.describe_subnets(SubnetIds=private_subnets)
    try:
        missing_subnets = []
        for pvt_id in private_subnets:
            missing_subnets.append(pvt_id)
            for subnet in subnets["Subnets"]:
                if subnet["SubnetId"] == pvt_id:
                    missing_subnets.remove(pvt_id)
        if len(missing_subnets) > 0:
            pytest.fail(
                f"Subnets ({missing_subnets}) do not exist.",
                False,
            )
        subnets_data["private_subnets"] = subnets["Subnets"]
        subnets_data["private_subnets_ids"] = private_subnets
    except KeyError as e:
        pytest.fail(f"Validation error - missing required data : {e.args[0]}", False)


@pytest.mark.aws
@pytest.mark.infra
@pytest.mark.dependency(depends=["aws_private_subnets_validation"])
@pytest.mark.skip(reason="Suffixes are not part of config at this time.")
def aws_private_subnets_suffix_validation(config: Dict[str, Any]) -> None:
    """Private subnets have the defined suffix."""  # noqa: D401,E501
    private_subnets_suffix: List[str] = get_config_value(
        config,
        "infra:aws:vpc:existing:private_subnets_suffix",
        key_missing_message="No private subnets suffix defined for config option: {0}",
        data_expected_error_message="No private subnets suffix was provided for config option: {0}",  # noqa: E501
    )
    try:
        subnets_wo_valid_suffix = []
        for subnet_id in subnets_data["private_subnets_ids"]:
            if not subnet_id.endswith(private_subnets_suffix):
                subnets_wo_valid_suffix.append(subnet_id)

        if len(subnets_wo_valid_suffix) > 0:
            pytest.fail(
                f"Subnets ({subnets_wo_valid_suffix}) without valid suffix ({private_subnets_suffix}).",  # noqa: E501
                False,
            )
    except KeyError as e:
        pytest.fail(f"Validation error - missing required data : {e.args[0]}", False)


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
            pytest.fail(
                """Not enough availability zones, subnets should be in
            at least 2 availability zones.""",
                False,
            )
    except KeyError as e:
        pytest.fail(f"Validation error - missing required data : {e.args[0]}", False)


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
            key_missing_message="No vpc id defined for config option: {0}",
            data_expected_error_message="No vpc id was provided for config option: {0}",
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
                    if "GatewayId" in route:
                        gateway_ids.append(route["GatewayId"])
        else:
            pytest.fail(
                f"""Provided Subnets {subnets_data["private_subnets_ids"]} and
                or VPC {vpc_id} do not have NAT gateway(s).""",
                False,
            )
        if not set(igw_ids) & set(gateway_ids):
            pytest.fail(
                f"""Provided subnets {subnets_data["private_subnets_ids"]} do not
                have NAT gateway(s).""",
                False,
            )

    except KeyError as e:
        pytest.fail(f"Validation error - missing required data : {e.args[0]}", False)


@pytest.mark.aws
@pytest.mark.infra
@pytest.mark.dependency(depends=["aws_private_subnets_validation"])
def aws_private_subnets_range_validation() -> None:
    """Private subnets have adequate IP range."""  # noqa: D401,E501
    try:
        subnets_wo_valid_range = []
        for subnet in subnets_data["private_subnets"]:
            cidrblock_range = subnet["CidrBlock"].split("/")[1]
            if int(cidrblock_range) < 19:
                subnets_wo_valid_range.append(subnet["SubnetId"])

        if len(subnets_wo_valid_range) > 0:
            pytest.fail(
                f"Private subnets ({subnets_wo_valid_range}) without valid required range.",  # noqa: E501
                False,
            )
    except KeyError as e:
        pytest.fail(f"Validation error - missing required data : {e.args[0]}", False)


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
            pytest.fail(
                f"""Private subnet(s) {subnet_missing_tags} missing tag
                'kubernetes.io/role/internal-elb'.""",
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
        key_missing_message="No vpc id defined for config option: {0}",
        data_expected_error_message="No vpc id was provided for config option: {0}",
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
            pytest.fail(
                f"""Subnets {missing_subnets} are not associated to provided vpc.""",
                False,
            )

        # DNS names and DNS resolution enabled
        enable_dns_support = ec2_client.describe_vpc_attribute(
            VpcId=vpc_d["Vpcs"][0]["VpcId"], Attribute="enableDnsSupport"
        )["EnableDnsSupport"]["Value"]
        enable_dns_hostnames = ec2_client.describe_vpc_attribute(
            VpcId=vpc_d["Vpcs"][0]["VpcId"], Attribute="enableDnsHostnames"
        )["EnableDnsHostnames"]["Value"]

        if not (enable_dns_hostnames and enable_dns_support):
            pytest.fail("DNS support not enabled for provided vpc.", False)
    except KeyError as e:
        pytest.fail(f"Validation error - missing required data : {e.args[0]}", False)
