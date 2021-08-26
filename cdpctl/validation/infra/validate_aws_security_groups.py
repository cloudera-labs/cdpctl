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
# Source File Name:  validate_aws_security_groups.py
###
"""Validation of AWS security groups."""
from typing import Any, Dict, List

import pytest
from boto3_type_annotations.ec2 import Client as EC2Client

from cdpctl.validation import fail, get_config_value, validator
from cdpctl.validation.aws_utils import get_client
from cdpctl.validation.infra.issues import (
    AWS_DEFAULT_SG_NEEDS_ALLOW_ACCESS_INTERNAL_TO_VPC,
    AWS_GATEWAY_SG_NEEDS_ALLOW_ACCESS_INTERNAL_TO_VPC,
    AWS_NON_CCM_DEFAULT_SG_NEEDS_TO_ALLOW_CDP_CIDRS,
    AWS_NON_CCM_GATEWAY_SG_MISSING_CIDRS,
    AWS_VPC_NOT_FOUND_IN_ACCOUNT,
)


@pytest.fixture(autouse=True, name="ec2_client")
def iam_client_fixture(config: Dict[str, Any]) -> EC2Client:
    """Return an AWS EC2 Client."""
    return get_client("ec2", config)


@pytest.mark.aws
@pytest.mark.infra
@pytest.mark.config_value(path="env:tunnel", value=False)
def aws_default_security_groups_contains_cdp_cidr_validation(
    config: Dict[str, Any],
    cdp_cidrs: List[str],
    ec2_client: EC2Client,
) -> None:
    """Default security groups contain CDP CIDRs if CCM is not enabled."""  # noqa: D401,E501
    _aws_default_security_groups_contains_cdp_cidr_validation(
        config, ec2_client, cdp_cidrs
    )


@validator
def _aws_default_security_groups_contains_cdp_cidr_validation(
    config: Dict[str, Any], ec2_client: EC2Client, cdp_cidrs: List[str]
) -> None:
    """Default security groups contain CDP CIDRs if CCM is not enabled."""  # noqa: D401,E501

    default_security_groups_id: str = get_config_value(
        config,
        "infra:aws:vpc:existing:security_groups:default_id",
    )

    security_groups = ec2_client.describe_security_groups(
        GroupIds=[default_security_groups_id]
    )

    missing_cdp_cidr_9443 = []

    for cdp_cidr in cdp_cidrs:  # pylint: disable=too-many-nested-blocks
        found_cidr_9443 = False

        for group in security_groups["SecurityGroups"]:
            ip_permissions = group["IpPermissions"]
            for ip_permission in ip_permissions:
                if "FromPort" not in ip_permission or "ToPort" not in ip_permission:
                    continue
                from_port = ip_permission["FromPort"]
                to_port = ip_permission["ToPort"]

                if from_port <= 9443 <= to_port:
                    for cidr in ip_permission["IpRanges"]:
                        if cidr["CidrIp"] == cdp_cidr:
                            found_cidr_9443 = True

        if not found_cidr_9443:
            missing_cdp_cidr_9443.append(cdp_cidr)

    if len(missing_cdp_cidr_9443) > 0:
        fail(
            AWS_NON_CCM_DEFAULT_SG_NEEDS_TO_ALLOW_CDP_CIDRS,
            resources=missing_cdp_cidr_9443,
        )


@pytest.mark.aws
@pytest.mark.infra
@pytest.mark.config_value(path="env:tunnel", value=False)
def aws_gateway_security_groups_contains_cdp_cidr_validation(
    config: Dict[str, Any],
    cdp_cidrs: List[str],
    ec2_client: EC2Client,
) -> None:
    """Gateway security groups contain CDP CIDRs if CCM is not enabled."""  # noqa: D401,E501
    _aws_gateway_security_groups_contains_cdp_cidr_validation(
        config, ec2_client, cdp_cidrs
    )


@validator
def _aws_gateway_security_groups_contains_cdp_cidr_validation(
    config: Dict[str, Any], ec2_client: EC2Client, cdp_cidrs: List[str]
) -> None:
    """Validate that gateway security groups contain CDP CIDRs if CCM not used."""

    gateway_security_groups_id: str = get_config_value(
        config,
        "infra:aws:vpc:existing:security_groups:knox_id",
    )

    security_groups = ec2_client.describe_security_groups(
        GroupIds=[gateway_security_groups_id]
    )

    missing_cdp_cidr_443 = []
    missing_cdp_cidr_9443 = []

    for cdp_cidr in cdp_cidrs:  # pylint: disable=too-many-nested-blocks
        found_cidr_443 = False
        found_cidr_9443 = False

        for group in security_groups["SecurityGroups"]:
            ip_permissions = group["IpPermissions"]
            for ip_permission in ip_permissions:
                if "FromPort" not in ip_permission or "ToPort" not in ip_permission:
                    continue

                from_port = ip_permission["FromPort"]
                to_port = ip_permission["ToPort"]

                for cidr in ip_permission["IpRanges"]:
                    if cidr["CidrIp"] == cdp_cidr:
                        if from_port <= 443 <= to_port:
                            found_cidr_443 = True

                        if from_port <= 9443 <= to_port:
                            found_cidr_9443 = True

        if not found_cidr_443:
            missing_cdp_cidr_443.append(cdp_cidr)

        if not found_cidr_9443:
            missing_cdp_cidr_9443.append(cdp_cidr)

    missing_cidrs = []
    if len(missing_cdp_cidr_443) > 0:
        missing_cidrs = (
            "Access to TCP port 443 needs to be allowed for "
            f"Cloudera CDP CIDR {missing_cdp_cidr_443}"
        )
    if len(missing_cdp_cidr_9443) > 0:
        missing_cidrs = (
            missing_cidrs + "Access to TCP port 9443 needs to be allowed "
            f"for Cloudera CDP CIDR {missing_cdp_cidr_9443}"
        )
    if missing_cidrs:
        fail(
            AWS_NON_CCM_GATEWAY_SG_MISSING_CIDRS,
            subjects=gateway_security_groups_id,
            resources=missing_cidrs,
        )


def security_groups_contains_vpc_cidr(
    config: Dict[str, Any], ec2_client: EC2Client, security_groups_id: str
) -> None:
    """Verify security groups contains the VPC CIDRs."""
    vpc_id: str = get_config_value(
        config,
        "infra:aws:vpc:existing:vpc_id",
    )

    vpcs = ec2_client.describe_vpcs(VpcIds=[vpc_id])

    if len(vpcs["Vpcs"]) == 0:
        fail(AWS_VPC_NOT_FOUND_IN_ACCOUNT, subjects=[vpc_id])

    vpc_cidr = vpcs["Vpcs"][0]["CidrBlock"]

    security_groups = ec2_client.describe_security_groups(GroupIds=[security_groups_id])

    found_vpc_cidr = False

    for group in security_groups["SecurityGroups"]:
        ip_permissions = group["IpPermissions"]

        for ip_permission in ip_permissions:
            if "IpProtocol" in ip_permission and ip_permission["IpProtocol"] == "-1":
                for cidr in ip_permission["IpRanges"]:
                    if cidr["CidrIp"] == vpc_cidr:
                        found_vpc_cidr = True
                continue

            if "FromPort" not in ip_permission or "ToPort" not in ip_permission:
                continue

            from_port = ip_permission["FromPort"]
            to_port = ip_permission["ToPort"]

            if from_port == 0 and to_port >= 65535:
                for cidr in ip_permission["IpRanges"]:
                    if cidr["CidrIp"] == vpc_cidr:
                        found_vpc_cidr = True

    return found_vpc_cidr


@pytest.mark.aws
@pytest.mark.infra
def aws_default_security_groups_contains_vpc_cidr_validation(
    config: Dict[str, Any]
) -> None:
    """Default security groups contain the existing VPC CIDRs."""  # noqa: D401,E501
    ec2_client: EC2Client = get_client("ec2", config)
    _aws_default_security_groups_contains_vpc_cidr_validation(config, ec2_client)


def _aws_default_security_groups_contains_vpc_cidr_validation(
    config: Dict[str, Any], ec2_client: EC2Client
) -> None:
    """Default security groups contain the existing VPC CIDRs."""  # noqa: D401,E501
    default_security_groups_id: str = get_config_value(
        config,
        "infra:aws:vpc:existing:security_groups:default_id",
    )

    if not security_groups_contains_vpc_cidr(
        config, ec2_client, default_security_groups_id
    ):
        fail(
            AWS_DEFAULT_SG_NEEDS_ALLOW_ACCESS_INTERNAL_TO_VPC,
            subjects=default_security_groups_id,
        )


@pytest.mark.aws
@pytest.mark.infra
def aws_gateway_security_groups_contains_vpc_cidr_validation(
    config: Dict[str, Any]
) -> None:
    """Gateway security groups contain the existing VPC CIDRs."""  # noqa: D401,E501
    ec2_client: EC2Client = get_client("ec2", config)
    _aws_gateway_security_groups_contains_vpc_cidr_validation(config, ec2_client)


def _aws_gateway_security_groups_contains_vpc_cidr_validation(
    config: Dict[str, Any], ec2_client: EC2Client
) -> None:
    """Gateway security groups contain the existing VPC CIDRs."""  # noqa: D401,E501
    gateway_security_groups_id: str = get_config_value(
        config,
        "infra:aws:vpc:existing:security_groups:knox_id",
    )

    if not security_groups_contains_vpc_cidr(
        config, ec2_client, gateway_security_groups_id
    ):
        fail(
            AWS_GATEWAY_SG_NEEDS_ALLOW_ACCESS_INTERNAL_TO_VPC,
            subjects=gateway_security_groups_id,
        )
