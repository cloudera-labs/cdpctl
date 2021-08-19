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
# Source File Name:  test_validate_aws_subnets.py
###

"""Test of AWS Subnets validation."""
from typing import Any, Dict, List

import pytest
from boto3_type_annotations.iam import Client as EC2Client
from botocore.stub import Stubber

from cdpctl.validation.aws_utils import get_client
from cdpctl.validation.infra.validate_aws_subnets import (
    aws_private_subnets_availablity_zone_validation,
    aws_private_subnets_range_validation,
    aws_private_subnets_route_validation,
    aws_private_subnets_suffix_validation,
    aws_private_subnets_tags_validation,
    aws_private_subnets_validation,
    aws_public_subnets_availablity_zone_validation,
    aws_public_subnets_range_validation,
    aws_public_subnets_route_validation,
    aws_public_subnets_suffix_validation,
    aws_public_subnets_tags_validation,
    aws_public_subnets_validation,
    aws_vpc_subnets_validation,
)
from tests.validation import expect_validation_failure, expect_validation_success

sample_public_subnets_response = {
    "Subnets": [
        {
            "AvailabilityZone": "us-west-2b",
            "CidrBlock": "10.0.237.0/24",
            "SubnetId": "subnet-pubtest1-cdp",
            "VpcId": "vpc-testcdp12345",
            "Tags": [
                {"Key": "kubernetes.io/role/elb", "Value": "1"},
                {"Key": "Name", "Value": "test-cdp.us-west-2a"},
            ],
        },
        {
            "AvailabilityZone": "us-west-2c",
            "CidrBlock": "10.1.238.0/14",
            "SubnetId": "subnet-pubtest2-cdp",
            "VpcId": "vpc-testcdp12345",
            "Tags": [
                {"Key": "kubernetes.io/role/elb", "Value": "1"},
                {"Key": "Name", "Value": "test-cdp.us-west-2a"},
            ],
        },
        {
            "AvailabilityZone": "us-west-2a",
            "CidrBlock": "10.2.236.0/22",
            "SubnetId": "subnet-pubtest3-cdp",
            "VpcId": "vpc-testcdp12345",
            "Tags": [
                {"Key": "kubernetes.io/role/elb", "Value": "1"},
                {"Key": "Name", "Value": "test-cdp.us-west-2a"},
            ],
        },
    ],
}

sample_private_subnets_response = {
    "Subnets": [
        {
            "AvailabilityZone": "us-west-2b",
            "CidrBlock": "20.0.237.0/14",
            "SubnetId": "subnet-prvtest1-cdp",
            "VpcId": "vpc-testcdp12345",
            "Tags": [
                {"Key": "kubernetes.io/role/internal-elb", "Value": "1"},
                {"Key": "Name", "Value": "test-cdp.us-west-2a"},
            ],
        },
        {
            "AvailabilityZone": "us-west-2c",
            "CidrBlock": "20.1.238.0/19",
            "SubnetId": "subnet-prvtest2-cdp",
            "VpcId": "vpc-testcdp12345",
            "Tags": [
                {"Key": "kubernetes.io/role/internal-elb", "Value": "1"},
                {"Key": "Name", "Value": "test-cdp.us-west-2a"},
            ],
        },
        {
            "AvailabilityZone": "us-west-2a",
            "CidrBlock": "20.2.236.0/18",
            "SubnetId": "subnet-prvtest3-cdp",
            "VpcId": "vpc-testcdp12345",
            "Tags": [
                {"Key": "kubernetes.io/role/internal-elb", "Value": "1"},
                {"Key": "Name", "Value": "test-cdp.us-west-2a"},
            ],
        },
    ],
}

public_subnet_ids = [
    "subnet-pubtest1-cdp",
    "subnet-pubtest2-cdp",
    "subnet-pubtest3-cdp",
]

private_subnet_ids = [
    "subnet-prvtest1-cdp",
    "subnet-prvtest2-cdp",
    "subnet-prvtest3-cdp",
]


def get_config(  # pylint: disable=dangerous-default-value
    public_subnet_ids_val: List[str] = [],
    private_subnet_ids_val: List[str] = [],
    public_suffix_val: str = "",
    private_suffix_val: str = "",
    vpc_id_val: str = "",
) -> Dict[str, Any]:
    """Return a config in proper format."""
    return {
        "infra": {
            "aws": {
                "vpc": {
                    "existing": {
                        "vpc_id": vpc_id_val,
                        "public_subnet_ids": public_subnet_ids_val,
                        "private_subnet_ids": private_subnet_ids_val,
                        "public_subnets_suffix": public_suffix_val,
                        "private_subnets_suffix": private_suffix_val,
                    }
                }
            }
        },
    }


@pytest.fixture(autouse=True, name="ec2_client")
def iam_client_fixture() -> EC2Client:
    config: Dict[str, Any] = {"infra": {"aws": {"region": "us-west-2", "profile": ""}}}
    return get_client("ec2", config)


def test_aws_public_subnets_validation_success(
    ec2_client: EC2Client,
) -> None:
    """Unit test public subnets success."""
    config = get_config(public_subnet_ids_val=public_subnet_ids)
    stubber = Stubber(ec2_client)
    stubber.add_response(
        "describe_subnets",
        sample_public_subnets_response,
        expected_params={"SubnetIds": public_subnet_ids},
    )
    with stubber:
        func = expect_validation_success(aws_public_subnets_validation)
        func(config, ec2_client)


def test_aws_public_subnets_validation_failure(
    ec2_client: EC2Client,
) -> None:
    """Unit test public subnets failure."""
    config = get_config(public_subnet_ids_val=public_subnet_ids)
    stubber = Stubber(ec2_client)
    stubber.add_response(
        "describe_subnets",
        {"Subnets": []},
        expected_params={"SubnetIds": public_subnet_ids},
    )
    with stubber:
        func = expect_validation_failure(aws_public_subnets_validation)
        func(config, ec2_client)


def test_aws_public_subnets_suffix_validation_success(
    ec2_client: EC2Client,
) -> None:
    """Unit test public subnets suffix success."""
    config = get_config(
        public_subnet_ids_val=public_subnet_ids, public_suffix_val="cdp"
    )
    stubber = Stubber(ec2_client)
    stubber.add_response(
        "describe_subnets",
        sample_public_subnets_response,
        expected_params={"SubnetIds": public_subnet_ids},
    )
    with stubber:
        func = expect_validation_success(aws_public_subnets_validation)
        func(config, ec2_client)
    with stubber:
        func = expect_validation_success(aws_public_subnets_suffix_validation)
        func(config)


def test_aws_public_subnets_suffix_validation_failure(
    ec2_client: EC2Client,
) -> None:
    """Unit test public subnets suffix failure."""
    config = get_config(
        public_subnet_ids_val=public_subnet_ids, public_suffix_val="fail"
    )
    stubber = Stubber(ec2_client)
    stubber.add_response(
        "describe_subnets",
        sample_public_subnets_response,
        expected_params={"SubnetIds": public_subnet_ids},
    )
    with stubber:
        func = expect_validation_failure(aws_public_subnets_suffix_validation)
        func(config)


def test_aws_public_subnets_availablity_zone_validation_success(
    ec2_client: EC2Client,
) -> None:
    """Unit test public subnets availablity zone success."""
    config = get_config(
        public_subnet_ids_val=public_subnet_ids, public_suffix_val="cdp"
    )
    stubber = Stubber(ec2_client)
    stubber.add_response(
        "describe_subnets",
        sample_public_subnets_response,
        expected_params={"SubnetIds": public_subnet_ids},
    )
    with stubber:
        func = expect_validation_success(aws_public_subnets_validation)
        func(config, ec2_client)
    with stubber:
        func = expect_validation_success(aws_public_subnets_availablity_zone_validation)
        func()


def test_aws_public_subnets_availablity_zone_validation_failure(
    ec2_client: EC2Client,
) -> None:
    """Unit test public subnets availablity zone failure."""
    config = get_config(
        public_subnet_ids_val=public_subnet_ids, public_suffix_val="fail"
    )
    stubber = Stubber(ec2_client)
    stubber.add_response(
        "describe_subnets",
        {
            "Subnets": [
                {
                    "AvailabilityZone": "us-west-2a",
                    "SubnetId": "subnet-pubtest1-cdp",
                },
                {
                    "AvailabilityZone": "us-west-2a",
                    "SubnetId": "subnet-pubtest2-cdp",
                },
                {
                    "AvailabilityZone": "us-west-2a",
                    "SubnetId": "subnet-pubtest3-cdp",
                },
            ],
        },
        expected_params={"SubnetIds": public_subnet_ids},
    )
    with stubber:
        func = expect_validation_success(aws_public_subnets_validation)
        func(config, ec2_client)
    with stubber:
        func = expect_validation_failure(aws_public_subnets_availablity_zone_validation)
        func()


def test_aws_public_subnets_route_validation_success(ec2_client: EC2Client) -> None:
    """Unit test public subnets route success."""
    config = get_config(
        public_subnet_ids_val=public_subnet_ids,
        public_suffix_val="cdp",
        vpc_id_val="vpc-testcdp12345",
    )
    stubber = Stubber(ec2_client)
    stubber.add_response(
        "describe_subnets",
        sample_public_subnets_response,
        expected_params={"SubnetIds": public_subnet_ids},
    )
    stubber.add_response(
        "describe_route_tables",
        {
            "RouteTables": [
                {
                    "Associations": [],
                    "OwnerId": "5634563456745",
                    "PropagatingVgws": [],
                    "RouteTableId": "rtb-0c451408c5eed6a63",
                    "Routes": [
                        {
                            "DestinationIpv6CidrBlock": "::/0",
                            "GatewayId": "igw-0c345435ee08c38ecd",
                            "Origin": "CreateRoute",
                            "State": "active",
                        },
                        {
                            "DestinationPrefixListId": "pl-00a54069",
                            "GatewayId": "vpce-04674658f3f99a",
                            "Origin": "CreateRoute",
                            "State": "active",
                        },
                        {
                            "DestinationPrefixListId": "pl-68a54001",
                            "GatewayId": "vpce-0dfgdg4353431d",
                            "Origin": "CreateRoute",
                            "State": "active",
                        },
                    ],
                    "Tags": [],
                    "VpcId": "vpc-testcdp12345",
                }
            ]
        },
        expected_params={
            "Filters": [
                {
                    "Name": "association.subnet-id",
                    "Values": public_subnet_ids,
                },
                {
                    "Name": "route.state",
                    "Values": ["active"],
                },
            ]
        },
    )

    stubber.add_response(
        "describe_internet_gateways",
        {
            "InternetGateways": [
                {
                    "Attachments": [
                        {"State": "available", "VpcId": "vpc-testcdp12345"}
                    ],
                    "InternetGatewayId": "igw-0c345435ee08c38ecd",
                    "OwnerId": "924123132397",
                    "Tags": [],
                }
            ],
        },
        expected_params={
            "Filters": [
                {
                    "Name": "attachment.vpc-id",
                    "Values": ["vpc-testcdp12345"],
                },
                {
                    "Name": "attachment.state",
                    "Values": ["available"],
                },
            ]
        },
    )
    with stubber:
        func = expect_validation_success(aws_public_subnets_validation)
        func(config, ec2_client)
    with stubber:
        func = expect_validation_success(aws_public_subnets_route_validation)
        func(config, ec2_client)


def test_aws_public_subnets_route_validation_failure(ec2_client: EC2Client) -> None:
    """Unit test public subnets route failure."""
    config = get_config(
        public_subnet_ids_val=public_subnet_ids,
        public_suffix_val="cdp",
        vpc_id_val="vpc-testcdp12345",
    )
    stubber = Stubber(ec2_client)
    stubber.add_response(
        "describe_subnets",
        {
            "Subnets": [
                {
                    "AvailabilityZone": "us-west-2a",
                    "SubnetId": "subnet-pubtest1-cdp",
                },
                {
                    "AvailabilityZone": "us-west-2a",
                    "SubnetId": "subnet-pubtest2-cdp",
                },
                {
                    "AvailabilityZone": "us-west-2a",
                    "SubnetId": "subnet-pubtest3-cdp",
                },
            ],
        },
        expected_params={"SubnetIds": public_subnet_ids},
    )
    stubber.add_response(
        "describe_route_tables",
        {
            "RouteTables": [
                {
                    "Associations": [],
                    "OwnerId": "5634563456745",
                    "PropagatingVgws": [],
                    "RouteTableId": "rtb-0c451408c5eed6a63",
                    "Routes": [
                        {
                            "DestinationPrefixListId": "pl-68a54001",
                            "GatewayId": "vpce-0dfgdg4353431d",
                            "Origin": "CreateRoute",
                            "State": "active",
                        },
                    ],
                    "Tags": [],
                    "VpcId": "vpc-testcdp12345",
                }
            ]
        },
        expected_params={
            "Filters": [
                {
                    "Name": "association.subnet-id",
                    "Values": public_subnet_ids,
                },
                {
                    "Name": "route.state",
                    "Values": ["active"],
                },
            ]
        },
    )
    stubber.add_response(
        "describe_internet_gateways",
        {
            "InternetGateways": [],
        },
        expected_params={
            "Filters": [
                {
                    "Name": "attachment.vpc-id",
                    "Values": ["vpc-testcdp12345"],
                },
                {
                    "Name": "attachment.state",
                    "Values": ["available"],
                },
            ]
        },
    )
    with stubber:
        func = expect_validation_success(aws_public_subnets_validation)
        func(config, ec2_client)
    with stubber:
        func = expect_validation_failure(aws_public_subnets_route_validation)
        func(config, ec2_client)


def test_aws_public_subnets_range_validation_success(ec2_client: EC2Client) -> None:
    """Unit test public subnets range success."""
    config = get_config(
        public_subnet_ids_val=public_subnet_ids, public_suffix_val="cdp"
    )
    stubber = Stubber(ec2_client)
    stubber.add_response(
        "describe_subnets",
        sample_public_subnets_response,
        expected_params={"SubnetIds": public_subnet_ids},
    )
    with stubber:
        func = expect_validation_success(aws_public_subnets_validation)
        func(config, ec2_client)
    with stubber:
        func = expect_validation_success(aws_public_subnets_range_validation)
        func()


def test_aws_public_subnets_range_validation_failure(ec2_client: EC2Client) -> None:
    """Unit test public subnets range failure."""
    config = get_config(public_subnet_ids, "fail")
    stubber = Stubber(ec2_client)
    stubber.add_response(
        "describe_subnets",
        {
            "Subnets": [
                {
                    "CidrBlock": "10.0.237.0/25",
                    "SubnetId": "subnet-pubtest1-cdp",
                },
                {"CidrBlock": "10.1.238.0/24", "SubnetId": "subnet-pubtest2-cdp"},
                {
                    "CidrBlock": "10.2.236.0/14",
                    "SubnetId": "subnet-pubtest3-cdp",
                },
            ],
        },
        expected_params={"SubnetIds": public_subnet_ids},
    )
    with stubber:
        func = expect_validation_success(aws_public_subnets_validation)
        func(config, ec2_client)
    with stubber:
        func = expect_validation_failure(aws_public_subnets_range_validation)
        func()


def test_aws_public_subnets_tags_validation_success(ec2_client: EC2Client) -> None:
    """Unit test public subnets tags success."""
    config = get_config(
        public_subnet_ids_val=public_subnet_ids, public_suffix_val="cdp"
    )
    stubber = Stubber(ec2_client)
    stubber.add_response(
        "describe_subnets",
        sample_public_subnets_response,
        expected_params={"SubnetIds": public_subnet_ids},
    )
    with stubber:
        func = expect_validation_success(aws_public_subnets_validation)
        func(config, ec2_client)
    with stubber:
        func = expect_validation_success(aws_public_subnets_tags_validation)
        func()


def test_aws_public_subnets_tags_validation_failure(ec2_client: EC2Client) -> None:
    """Unit test public subnets tags failure."""
    config = get_config(public_subnet_ids, "fail")
    stubber = Stubber(ec2_client)
    stubber.add_response(
        "describe_subnets",
        {
            "Subnets": [
                {
                    "Tags": [
                        {"Key": "kubernetes.io/role/elb", "Value": "1"},
                        {"Key": "Name", "Value": "test-cdp.us-west-2a"},
                    ],
                    "SubnetId": "subnet-pubtest1-cdp",
                },
                {
                    "Tags": [
                        {"Key": "kubernetes.io/role/elb", "Value": "1"},
                        {"Key": "Name", "Value": "test-cdp.us-west-2a"},
                    ],
                    "SubnetId": "subnet-pubtest2-cdp",
                },
                {
                    "Tags": [
                        {"Key": "Name", "Value": "test-cdp.us-west-2a"},
                    ],
                    "SubnetId": "subnet-pubtest3-cdp",
                },
            ],
        },
        expected_params={"SubnetIds": public_subnet_ids},
    )
    with stubber:
        func = expect_validation_success(aws_public_subnets_validation)
        func(config, ec2_client)
    with stubber:
        func = expect_validation_failure(aws_public_subnets_tags_validation)
        func()


def test_aws_private_subnets_validation_success(ec2_client: EC2Client) -> None:
    """Unit test private subnets success."""
    config = get_config(private_subnet_ids_val=private_subnet_ids)
    stubber = Stubber(ec2_client)
    stubber.add_response(
        "describe_subnets",
        sample_private_subnets_response,
        expected_params={"SubnetIds": private_subnet_ids},
    )
    with stubber:
        func = expect_validation_success(aws_private_subnets_validation)
        func(config, ec2_client)


def test_aws_private_subnets_validation_failure(ec2_client: EC2Client) -> None:
    """Unit test private subnets failure."""
    config = get_config(private_subnet_ids_val=private_subnet_ids)
    stubber = Stubber(ec2_client)
    stubber.add_response(
        "describe_subnets",
        {"Subnets": []},
        expected_params={"SubnetIds": private_subnet_ids},
    )
    with stubber:
        func = expect_validation_failure(aws_private_subnets_validation)
        func(config, ec2_client)


def test_aws_private_subnets_suffix_validation_success(ec2_client: EC2Client) -> None:
    """Unit test private subnets suffix success."""
    config = get_config(
        private_subnet_ids_val=private_subnet_ids, private_suffix_val="cdp"
    )
    stubber = Stubber(ec2_client)
    stubber.add_response(
        "describe_subnets",
        sample_private_subnets_response,
        expected_params={"SubnetIds": private_subnet_ids},
    )
    with stubber:
        func = expect_validation_success(aws_private_subnets_validation)
        func(config, ec2_client)
    with stubber:
        func = expect_validation_success(aws_private_subnets_suffix_validation)
        func(config)


def test_aws_private_subnets_suffix_validation_failure(ec2_client: EC2Client) -> None:
    """Unit test private subnets suffix failure."""
    config = get_config(
        private_subnet_ids_val=private_subnet_ids, private_suffix_val="fail"
    )
    stubber = Stubber(ec2_client)
    stubber.add_response(
        "describe_subnets",
        sample_private_subnets_response,
        expected_params={"SubnetIds": private_subnet_ids},
    )
    with stubber:
        func = expect_validation_success(aws_private_subnets_validation)
        func(config, ec2_client)
    with stubber:
        func = expect_validation_failure(aws_private_subnets_suffix_validation)
        func(config)


def test_aws_private_subnets_availablity_zone_validation_success(
    ec2_client: EC2Client,
) -> None:
    """Unit test private subnets availablity zone success."""
    config = get_config(
        private_subnet_ids_val=private_subnet_ids, private_suffix_val="cdp"
    )
    stubber = Stubber(ec2_client)
    stubber.add_response(
        "describe_subnets",
        sample_private_subnets_response,
        expected_params={"SubnetIds": private_subnet_ids},
    )
    with stubber:
        func = expect_validation_success(aws_private_subnets_validation)
        func(config, ec2_client)
    with stubber:
        func = expect_validation_success(
            aws_private_subnets_availablity_zone_validation
        )
        func()


def test_aws_private_subnets_availablity_zone_validation_failure(
    ec2_client: EC2Client,
) -> None:
    """Unit test private subnets availablity zone failure."""
    config = get_config(
        private_subnet_ids_val=private_subnet_ids, private_suffix_val="fail"
    )
    stubber = Stubber(ec2_client)
    stubber.add_response(
        "describe_subnets",
        {
            "Subnets": [
                {
                    "AvailabilityZone": "us-west-2a",
                    "SubnetId": "subnet-prvtest1-cdp",
                },
                {
                    "AvailabilityZone": "us-west-2a",
                    "SubnetId": "subnet-prvtest2-cdp",
                },
                {
                    "AvailabilityZone": "us-west-2a",
                    "SubnetId": "subnet-prvtest3-cdp",
                },
            ],
        },
        expected_params={"SubnetIds": private_subnet_ids},
    )
    with stubber:
        func = expect_validation_success(aws_private_subnets_validation)
        func(config, ec2_client)
    with stubber:
        func = expect_validation_failure(
            aws_private_subnets_availablity_zone_validation
        )
        func()


def test_aws_private_subnets_route_validation_success(ec2_client: EC2Client) -> None:
    """Unit test private subnets route success."""
    config = get_config(
        private_subnet_ids_val=private_subnet_ids,
        private_suffix_val="cdp",
        vpc_id_val="vpc-testcdp12345",
    )
    stubber = Stubber(ec2_client)
    stubber.add_response(
        "describe_subnets",
        sample_private_subnets_response,
        expected_params={"SubnetIds": private_subnet_ids},
    )
    stubber.add_response(
        "describe_route_tables",
        {
            "RouteTables": [
                {
                    "Associations": [],
                    "OwnerId": "5634563456745",
                    "PropagatingVgws": [],
                    "RouteTableId": "rtb-0c451408c5eed6a63",
                    "Routes": [
                        {
                            "DestinationIpv6CidrBlock": "::/0",
                            "NatGatewayId": "nat-test1234566789",
                            "Origin": "CreateRoute",
                            "State": "active",
                        },
                        {
                            "DestinationPrefixListId": "pl-00a54069",
                            "GatewayId": "vpce-test1234567",
                            "Origin": "CreateRoute",
                            "State": "active",
                        },
                        {
                            "DestinationPrefixListId": "pl-68a54001",
                            "GatewayId": "vpce-testvpce12234",
                            "Origin": "CreateRoute",
                            "State": "active",
                        },
                    ],
                    "Tags": [],
                    "VpcId": "vpc-testcdp12345",
                }
            ]
        },
        expected_params={
            "Filters": [
                {
                    "Name": "association.subnet-id",
                    "Values": private_subnet_ids,
                },
                {
                    "Name": "route.state",
                    "Values": ["active"],
                },
            ]
        },
    )
    stubber.add_response(
        "describe_nat_gateways",
        {
            "NatGateways": [
                {
                    "NatGatewayId": "nat-test1234566789",
                }
            ],
        },
        expected_params={
            "Filters": [
                {
                    "Name": "vpc-id",
                    "Values": ["vpc-testcdp12345"],
                },
                {
                    "Name": "state",
                    "Values": ["available"],
                },
            ]
        },
    )
    with stubber:
        func = expect_validation_success(aws_private_subnets_validation)
        func(config, ec2_client)
    with stubber:
        func = expect_validation_success(aws_private_subnets_route_validation)
        func(config, ec2_client)


def test_aws_private_subnets_route_validation_failure(ec2_client: EC2Client) -> None:
    """Unit test private subnets route failure."""
    config = get_config(
        private_subnet_ids_val=private_subnet_ids,
        private_suffix_val="cdp",
        vpc_id_val="vpc-testcdp12345",
    )
    stubber = Stubber(ec2_client)
    stubber.add_response(
        "describe_subnets",
        {
            "Subnets": [
                {
                    "AvailabilityZone": "us-west-2a",
                    "SubnetId": "subnet-prvtest1-cdp",
                },
                {
                    "AvailabilityZone": "us-west-2a",
                    "SubnetId": "subnet-prvtest2-cdp",
                },
                {
                    "AvailabilityZone": "us-west-2a",
                    "SubnetId": "subnet-prvtest3-cdp",
                },
            ],
        },
        expected_params={"SubnetIds": private_subnet_ids},
    )
    stubber.add_response(
        "describe_route_tables",
        {
            "RouteTables": [
                {
                    "Associations": [],
                    "OwnerId": "5634563456745",
                    "PropagatingVgws": [],
                    "RouteTableId": "rtb-0c451408c5eed6a63",
                    "Routes": [
                        {
                            "DestinationPrefixListId": "pl-68a54001",
                            "GatewayId": "vpce-test12123423",
                            "Origin": "CreateRoute",
                            "State": "active",
                        },
                    ],
                    "Tags": [],
                    "VpcId": "vpc-testcdp12345",
                }
            ]
        },
        expected_params={
            "Filters": [
                {
                    "Name": "association.subnet-id",
                    "Values": private_subnet_ids,
                },
                {
                    "Name": "route.state",
                    "Values": ["active"],
                },
            ]
        },
    )
    stubber.add_response(
        "describe_nat_gateways",
        {
            "NatGateways": [],
        },
        expected_params={
            "Filters": [
                {
                    "Name": "vpc-id",
                    "Values": ["vpc-testcdp12345"],
                },
                {
                    "Name": "state",
                    "Values": ["available"],
                },
            ]
        },
    )
    with stubber:
        func = expect_validation_success(aws_private_subnets_validation)
        func(config, ec2_client)
    with stubber:
        func = expect_validation_failure(aws_private_subnets_route_validation)
        func(config, ec2_client)


def test_aws_private_subnets_range_validation_success(ec2_client: EC2Client) -> None:
    """Unit test private subnets range success."""
    config = get_config(
        private_subnet_ids_val=private_subnet_ids, private_suffix_val="fail"
    )
    stubber = Stubber(ec2_client)
    stubber.add_response(
        "describe_subnets",
        sample_private_subnets_response,
        expected_params={"SubnetIds": private_subnet_ids},
    )
    with stubber:
        func = expect_validation_success(aws_private_subnets_validation)
        func(config, ec2_client)
    with stubber:
        func = expect_validation_success(aws_private_subnets_range_validation)
        func()


def test_aws_private_subnets_range_validation_failure(ec2_client: EC2Client) -> None:
    """Unit test private subnets range failure."""
    config = get_config(
        private_subnet_ids_val=private_subnet_ids, private_suffix_val="fail"
    )
    stubber = Stubber(ec2_client)
    stubber.add_response(
        "describe_subnets",
        {
            "Subnets": [
                {
                    "CidrBlock": "10.0.237.0/12",
                    "SubnetId": "subnet-prvtest1-cdp",
                },
                {"CidrBlock": "10.1.238.0/24", "SubnetId": "subnet-prvtest2-cdp"},
                {
                    "CidrBlock": "10.2.236.0/24",
                    "SubnetId": "subnet-prvtest3-cdp",
                },
            ],
        },
        expected_params={"SubnetIds": private_subnet_ids},
    )
    with stubber:
        func = expect_validation_success(aws_private_subnets_validation)
        func(config, ec2_client)
    with stubber:
        func = expect_validation_failure(aws_private_subnets_range_validation)
        func()


def test_aws_private_subnets_tags_validation_success(ec2_client: EC2Client) -> None:
    """Unit test private subnets tags success."""
    config = get_config(
        private_subnet_ids_val=private_subnet_ids, private_suffix_val="cdp"
    )
    stubber = Stubber(ec2_client)
    stubber.add_response(
        "describe_subnets",
        sample_private_subnets_response,
        expected_params={"SubnetIds": private_subnet_ids},
    )
    with stubber:
        func = expect_validation_success(aws_private_subnets_validation)
        func(config, ec2_client)
    with stubber:
        func = expect_validation_success(aws_private_subnets_tags_validation)
        func()


def test_aws_private_subnets_tags_validation_failure(ec2_client: EC2Client) -> None:
    """Unit test private subnets tags failure."""
    config = get_config(
        private_subnet_ids_val=private_subnet_ids, private_suffix_val="fail"
    )
    stubber = Stubber(ec2_client)
    stubber.add_response(
        "describe_subnets",
        {
            "Subnets": [
                {
                    "Tags": [
                        {"Key": "kubernetes.io/role/internal-elb", "Value": "1"},
                        {"Key": "Name", "Value": "test-cdp.us-west-2a"},
                    ],
                    "SubnetId": "subnet-prvtest1-cdp",
                },
                {
                    "Tags": [
                        {"Key": "kubernetes.io/role/internal-elb", "Value": "1"},
                        {"Key": "Name", "Value": "test-cdp.us-west-2a"},
                    ],
                    "SubnetId": "subnet-prvtest2-cdp",
                },
                {
                    "Tags": [
                        {"Key": "Name", "Value": "test-cdp.us-west-2a"},
                    ],
                    "SubnetId": "subnet-prvtest3-cdp",
                },
            ],
        },
        expected_params={"SubnetIds": private_subnet_ids},
    )
    with stubber:
        func = expect_validation_success(aws_private_subnets_validation)
        func(config, ec2_client)
    with stubber:
        func = expect_validation_failure(aws_private_subnets_tags_validation)
        func()


def test_aws_vpc_validation_success(ec2_client: EC2Client) -> None:
    """Unit test vpc success."""
    config = {
        "infra": {
            "aws": {
                "vpc": {
                    "existing": {
                        "private_subnets": private_subnet_ids,
                        "private_subnets_suffix": "cdp",
                        "public_subnets": public_subnet_ids,
                        "public_subnets_suffix": "cdp",
                        "vpc_id": "test-vpc-cdp",
                    }
                }
            }
        },
    }
    stubber = Stubber(ec2_client)
    filters = [{"Name": "tag:Name", "Values": ["test-vpc-cdp"]}]
    stubber.add_response(
        "describe_vpcs",
        {
            "Vpcs": [
                {
                    "VpcId": "vpc-testcdp12345",
                    "OwnerId": "308408126366",
                    "Tags": [{"Key": "Name", "Value": "test-vpc-cdp"}],
                }
            ]
        },
        expected_params={"VpcIds": ["test-vpc-cdp"]},
    )
    filters = [{"Name": "vpc-id", "Values": ["vpc-testcdp12345"]}]
    stubber.add_response(
        "describe_subnets",
        {
            "Subnets": sample_public_subnets_response["Subnets"]
            + sample_private_subnets_response["Subnets"]
        },
        expected_params={"Filters": filters},
    )
    stubber.add_response(
        "describe_vpc_attribute",
        {"EnableDnsSupport": {"Value": True}},
        expected_params={"VpcId": "vpc-testcdp12345", "Attribute": "enableDnsSupport"},
    )
    stubber.add_response(
        "describe_vpc_attribute",
        {"EnableDnsHostnames": {"Value": True}},
        expected_params={
            "VpcId": "vpc-testcdp12345",
            "Attribute": "enableDnsHostnames",
        },
    )

    with stubber:
        func = expect_validation_success(aws_vpc_subnets_validation)
        func(config, ec2_client)


def test_aws_vpc_validation_failure(ec2_client: EC2Client) -> None:
    """Unit test subnets not associated to provided vpc  failure."""
    config: Dict[str, Any] = {
        "infra": {
            "vpc": {
                "private_subnet_ids": private_subnet_ids,
                "private_subnets_suffix": "cdp",
                "public_subnets_ids": public_subnet_ids,
                "public_subnets_suffix": "cdp",
                "vpc_id": "test-vpc-cdp",
            }
        },
    }
    stubber = Stubber(ec2_client)
    filters = [{"Name": "tag:Name", "Values": ["test-vpc-cdp"]}]
    stubber.add_response(
        "describe_vpcs",
        {
            "Vpcs": [
                {
                    "VpcId": "vpc-testcdp12345",
                    "OwnerId": "308408126366",
                    "Tags": [{"Key": "Name", "Value": "test-vpc-cdp"}],
                }
            ]
        },
        expected_params={"VpcIds": ["test-vpc-cdp"]},
    )
    filters = [{"Name": "vpc-id", "Values": ["vpc-testcdp12345"]}]
    stubber.add_response(
        "describe_subnets",
        {
            "Subnets": sample_public_subnets_response["Subnets"]
            + sample_private_subnets_response["Subnets"]
        },
        expected_params={"Filters": filters},
    )
    stubber.add_response(
        "describe_vpc_attribute",
        {"EnableDnsSupport": {"Value": False}},
        expected_params={"VpcId": "vpc-testcdp12345", "Attribute": "enableDnsSupport"},
    )
    stubber.add_response(
        "describe_vpc_attribute",
        {"EnableDnsHostnames": {"Value": True}},
        expected_params={
            "VpcId": "vpc-testcdp12345",
            "Attribute": "enableDnsHostnames",
        },
    )

    with stubber:
        func = expect_validation_failure(aws_vpc_subnets_validation)
        func(config, ec2_client)
