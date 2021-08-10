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
# Source File Name:  test_validate_aws_security_groups.py
###
"""Test of AWS Security Groups validation."""
from typing import Any, Dict, List

import boto3
from boto3_type_annotations.ec2 import Client as EC2Client
from botocore.stub import Stubber
from moto import mock_iam

from cdpctl.validation.infra.conftest import (  # noqa: F401 pylint: disable=unused-import
    cdp_cidrs,
)
from cdpctl.validation.infra.validate_aws_security_groups import (
    _aws_default_security_groups_contains_cdp_cidr_validation,
    _aws_gateway_security_groups_contains_cdp_cidr_validation,
    _aws_default_security_groups_contains_vpc_cidr_validation,
    _aws_gateway_security_groups_contains_vpc_cidr_validation,
)
from tests.validation import expect_validation_failure, expect_validation_success

default_security_group = "test_default_111"
gateway_security_group = "test_gateway_111"
vpc_id = "test_vpc_111"
vpc_cidr = "30.1.0.0/16"

config: Dict[str, Any] = {
    "env": {"tunnel": False},
    "infra": {
        "aws": {
            "region": "us-west-2",
            "vpc": {
                "existing": {
                    "security_groups": {
                        "default_id": f"{default_security_group}",
                        "knox_id": f"{gateway_security_group}",
                    },
                    "vpc_id": f"{vpc_id}",
                }
            },
        }
    },
}


def add_describe_vpc_response(stubber: Stubber):
    stubber.add_response(
        "describe_vpcs",
        {
            "Vpcs": [
                {
                    "CidrBlock": vpc_cidr,
                    "DhcpOptionsId": "dopt-19edf471",
                    "State": "available",
                    "VpcId": "vpc-0e9801d129EXAMPLE",
                    "OwnerId": "111122223333",
                    "InstanceTenancy": "default",
                    "CidrBlockAssociationSet": [
                        {
                            "AssociationId": "vpc-cidr-assoc-062c64cfafEXAMPLE",
                            "CidrBlock": "30.1.0.0/16",
                            "CidrBlockState": {"State": "associated"},
                        }
                    ],
                    "Tags": [{"Key": "Name", "Value": "Not Shared"}],
                }
            ]
        },
        expected_params={"VpcIds": [vpc_id]},
    )


@mock_iam
def test_aws_default_security_groups_contains_cdp_cidr_validation_succeeds(
    cdp_cidrs: List[str],  # noqa : F811 pylint: disable=redefined-outer-name
):
    """Verify validation succeeds for cdp cidr within default security group."""
    ec2_client: EC2Client = boto3.client("ec2", "us-west-2")
    stubber = Stubber(ec2_client)

    stubber.add_response(
        "describe_security_groups",
        {
            "SecurityGroups": [
                {
                    "Description": "test",
                    "GroupName": "test",
                    "IpPermissions": [
                        {
                            "FromPort": 9443,
                            "ToPort": 9443,
                            "IpRanges": [
                                {"CidrIp": "52.36.110.208/32"},
                                {"CidrIp": "52.40.165.49/32"},
                                {"CidrIp": "35.166.86.177/32"},
                            ],
                        },
                    ],
                }
            ]
        },
        expected_params={"GroupIds": [default_security_group]},
    )

    with stubber:
        func = expect_validation_success(
            _aws_default_security_groups_contains_cdp_cidr_validation
        )
        func(config, ec2_client, cdp_cidrs)


@mock_iam
def test_aws_default_security_groups_contains_cdp_cidr_validation_fails(
    cdp_cidrs: List[str],  # noqa : F811 pylint: disable=redefined-outer-name
):
    """Verify validation fails for cdp cidr within default security group."""
    ec2_client: EC2Client = boto3.client("ec2", "us-west-2")
    stubber = Stubber(ec2_client)

    stubber.add_response(
        "describe_security_groups",
        {
            "SecurityGroups": [
                {
                    "Description": "test",
                    "GroupName": "test",
                    "IpPermissions": [
                        {
                            "FromPort": 11443,
                            "ToPort": 11443,
                            "IpRanges": [
                                {"CidrIp": "52.36.110.208/32"},
                                {"CidrIp": "52.40.165.49/32"},
                                {"CidrIp": "35.166.86.177/32"},
                            ],
                        }
                    ],
                }
            ]
        },
        expected_params={"GroupIds": [default_security_group]},
    )

    with stubber:
        func = expect_validation_failure(
            _aws_default_security_groups_contains_cdp_cidr_validation
        )
        func(config, ec2_client, cdp_cidrs)


@mock_iam
def test_aws_gateway_security_groups_contains_cdp_cidr_validation_succeeds(
    cdp_cidrs: List[str],  # noqa : F811 pylint: disable=redefined-outer-name
):
    """Verify validation succeeds for cdp cidr within gateway security group."""
    ec2_client: EC2Client = boto3.client("ec2", "us-west-2")
    stubber = Stubber(ec2_client)

    stubber.add_response(
        "describe_security_groups",
        {
            "SecurityGroups": [
                {
                    "Description": "test",
                    "GroupName": "test",
                    "IpPermissions": [
                        {
                            "FromPort": 443,
                            "ToPort": 443,
                            "IpRanges": [
                                {"CidrIp": "52.36.110.208/32"},
                                {"CidrIp": "52.40.165.49/32"},
                                {"CidrIp": "35.166.86.177/32"},
                            ],
                        },
                        {
                            "FromPort": 9443,
                            "ToPort": 9443,
                            "IpRanges": [
                                {"CidrIp": "52.36.110.208/32"},
                                {"CidrIp": "52.40.165.49/32"},
                                {"CidrIp": "35.166.86.177/32"},
                            ],
                        },
                    ],
                }
            ]
        },
        expected_params={"GroupIds": [gateway_security_group]},
    )

    with stubber:
        func = expect_validation_success(
            _aws_gateway_security_groups_contains_cdp_cidr_validation
        )
        func(config, ec2_client, cdp_cidrs)


@mock_iam
def test_aws_gateway_security_groups_contains_cdp_cidr_validation_fails(
    cdp_cidrs: List[str],  # noqa : F811 pylint: disable=redefined-outer-name
):
    """Verify validation fails for cdp cidr within gateway security group."""
    ec2_client: EC2Client = boto3.client("ec2", "us-west-2")
    stubber = Stubber(ec2_client)

    stubber.add_response(
        "describe_security_groups",
        {
            "SecurityGroups": [
                {
                    "Description": "test",
                    "GroupName": "test",
                    "IpPermissions": [
                        {
                            "FromPort": 11443,
                            "ToPort": 11443,
                            "IpRanges": [
                                {"CidrIp": "52.36.110.208/32"},
                                {"CidrIp": "52.40.165.49/32"},
                                {"CidrIp": "35.166.86.177/32"},
                            ],
                        },
                        {
                            "FromPort": 22443,
                            "ToPort": 22943,
                            "IpRanges": [
                                {"CidrIp": "52.36.110.208/32"},
                                {"CidrIp": "52.40.165.49/32"},
                                {"CidrIp": "35.166.86.177/32"},
                            ],
                        },
                    ],
                }
            ]
        },
        expected_params={"GroupIds": [gateway_security_group]},
    )

    with stubber:
        func = expect_validation_failure(
            _aws_gateway_security_groups_contains_cdp_cidr_validation
        )
        func(config, ec2_client, cdp_cidrs)


@mock_iam
def test_aws_gateway_security_groups_contains_vpc_cidr_validation_succeeds_with_ports():
    """Verify validation succeeds for VPC cidr within gateway security group with ports."""
    ec2_client: EC2Client = boto3.client("ec2", "us-west-2")
    stubber = Stubber(ec2_client)

    add_describe_vpc_response(stubber)

    stubber.add_response(
        "describe_security_groups",
        {
            "SecurityGroups": [
                {
                    "Description": "test",
                    "GroupName": "test",
                    "IpPermissions": [
                        {
                            "FromPort": 0,
                            "ToPort": 65535,
                            "IpRanges": [{"CidrIp": vpc_cidr}],
                        }
                    ],
                }
            ]
        },
        expected_params={"GroupIds": [gateway_security_group]},
    )

    with stubber:
        func = expect_validation_success(
            _aws_gateway_security_groups_contains_vpc_cidr_validation
        )
        func(config, ec2_client)


@mock_iam
def test_aws_gateway_security_groups_contains_vpc_cidr_validation_succeeds_without_ports():
    """Verify validation succeeds for VPC cidr within gateway security group without ports."""
    ec2_client: EC2Client = boto3.client("ec2", "us-west-2")
    stubber = Stubber(ec2_client)

    add_describe_vpc_response(stubber)

    stubber.add_response(
        "describe_security_groups",
        {
            "SecurityGroups": [
                {
                    "Description": "test",
                    "GroupName": "test",
                    "IpPermissions": [
                        {
                            "IpProtocol": "-1",
                            "IpRanges": [{"CidrIp": vpc_cidr}],
                        }
                    ],
                }
            ]
        },
        expected_params={"GroupIds": [gateway_security_group]},
    )

    with stubber:
        func = expect_validation_success(
            _aws_gateway_security_groups_contains_vpc_cidr_validation
        )
        func(config, ec2_client)


@mock_iam
def test_aws_gateway_security_groups_contains_vpc_cidr_validation_fails():
    """Verify validation fails for VPC cidr within gateway security group."""
    ec2_client: EC2Client = boto3.client("ec2", "us-west-2")
    stubber = Stubber(ec2_client)

    add_describe_vpc_response(stubber)

    stubber.add_response(
        "describe_security_groups",
        {
            "SecurityGroups": [
                {
                    "Description": "test",
                    "GroupName": "test",
                    "IpPermissions": [
                        {
                            "IpProtocol": "-1",
                            "IpRanges": [{"CidrIp": "fail_cidr"}],
                        }
                    ],
                }
            ]
        },
        expected_params={"GroupIds": [gateway_security_group]},
    )

    with stubber:
        func = expect_validation_failure(
            _aws_gateway_security_groups_contains_vpc_cidr_validation
        )
        func(config, ec2_client)


@mock_iam
def test_aws_default_security_groups_contains_vpc_cidr_validation_succeeds_with_ports():
    """Verify validation succeeds for VPC cidr within default security group using ports."""
    ec2_client: EC2Client = boto3.client("ec2", "us-west-2")
    stubber = Stubber(ec2_client)

    add_describe_vpc_response(stubber)

    stubber.add_response(
        "describe_security_groups",
        {
            "SecurityGroups": [
                {
                    "Description": "test",
                    "GroupName": "test",
                    "IpPermissions": [
                        {
                            "FromPort": 0,
                            "ToPort": 65535,
                            "IpRanges": [{"CidrIp": vpc_cidr}],
                        }
                    ],
                }
            ]
        },
        expected_params={"GroupIds": [default_security_group]},
    )

    with stubber:
        func = expect_validation_success(
            _aws_default_security_groups_contains_vpc_cidr_validation
        )
        func(config, ec2_client)


@mock_iam
def test_aws_default_security_groups_contains_vpc_cidr_validation_succeeds_without_ports():
    """Verify validation succeeds for VPC cidr within default security group without ports."""
    ec2_client: EC2Client = boto3.client("ec2", "us-west-2")
    stubber = Stubber(ec2_client)

    add_describe_vpc_response(stubber)

    stubber.add_response(
        "describe_security_groups",
        {
            "SecurityGroups": [
                {
                    "Description": "test",
                    "GroupName": "test",
                    "IpPermissions": [
                        {
                            "IpProtocol": "-1",
                            "IpRanges": [{"CidrIp": vpc_cidr}],
                        }
                    ],
                }
            ]
        },
        expected_params={"GroupIds": [default_security_group]},
    )

    with stubber:
        func = expect_validation_success(
            _aws_default_security_groups_contains_vpc_cidr_validation
        )
        func(config, ec2_client)


@mock_iam
def test_aws_default_security_groups_contains_vpc_cidr_validation_fails():
    """Verify validation fails for VPC cidr within default security group."""
    ec2_client: EC2Client = boto3.client("ec2", "us-west-2")
    stubber = Stubber(ec2_client)

    add_describe_vpc_response(stubber)

    stubber.add_response(
        "describe_security_groups",
        {
            "SecurityGroups": [
                {
                    "Description": "test",
                    "GroupName": "test",
                    "IpPermissions": [
                        {
                            "IpProtocol": "-1",
                            "IpRanges": [{"CidrIp": "fail_cidr"}],
                        }
                    ],
                }
            ]
        },
        expected_params={"GroupIds": [default_security_group]},
    )

    with stubber:
        func = expect_validation_failure(
            _aws_default_security_groups_contains_vpc_cidr_validation
        )
        func(config, ec2_client)
