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
# Source File Name:  test_validate_aws_cross_account_role.py
###
"""Test of AWS Cross Account role validation."""
from typing import Any, Dict, List

import pytest
from boto3_type_annotations.iam import Client as IAMClient
from botocore.stub import Stubber

from cdpctl.validation.aws_utils import get_client
from cdpctl.validation.infra.validate_aws_cross_account_role import (
    aws_cross_account_identity_management_needed_actions_validation,
    aws_cross_account_role_account_id_validation,
    aws_cross_account_role_autoscaling_resources_needed_actions_validation,
    aws_cross_account_role_cdp_environment_resources_needed_actions_validation,
    aws_cross_account_role_cloud_formation_needed_actions_validation,
    aws_cross_account_role_ec2_needed_actions_validation,
    aws_cross_account_role_exists_validation,
    aws_cross_account_role_external_id_validation,
    aws_cross_account_role_pass_role_needed_actions_validation,
    cross_account_role_data,
)
from tests.validation import expect_validation_failure, expect_validation_success
from tests.validation.test_aws_utils import (
    add_get_role_response,
    add_simulate_policy_response,
)


@pytest.fixture(autouse=True, name="iam_client")
def iam_client_fixture() -> IAMClient:
    config: Dict[str, Any] = {"infra": {"aws": {"region": "us-west-2", "profile": ""}}}
    return get_client("iam", config)


def test_aws_cross_account_role_exists_validation_success(
    iam_client: IAMClient,
) -> None:
    """Unit test cross account role validation success."""
    config: Dict[str, Any] = {
        "env": {
            "aws": {
                "role": {
                    "name": {"cross_account": "arn:aws:iam::1234:role/cross_acct_role"}
                }
            }
        }
    }
    stubber = Stubber(iam_client)
    add_get_role_response(
        stubber=stubber,
        role_arn="arn:aws:iam::1234:role/cross_acct_role",
        includeTrustPolicy=True,
    )
    with stubber:
        func = expect_validation_success(aws_cross_account_role_exists_validation)
        func(config, iam_client)


def test_aws_cross_account_role_exists_validation_failure(
    iam_client: IAMClient,
) -> None:
    """Unit test cross account role validation failure scenario."""
    config: Dict[str, Any] = {
        "env": {
            "aws": {
                "role": {
                    "name": {"cross_account": "arn:aws:iam::1F:role/cross_acct_role"}
                }
            }
        }
    }
    stubber = Stubber(iam_client)
    stubber.add_client_error(
        "get_role",
        service_error_code="NoSuchEntityException",
        service_message="Role Not Found",
        http_status_code=404,
    )
    with stubber:
        func = expect_validation_failure(aws_cross_account_role_exists_validation)
        func(config, iam_client)


@pytest.mark.skip(reason="Type issue between aws get_role vs boto3 Iam client get_role")
def test_aws_cross_account_role_account_id_and_external_id_validation_success(
    iam_client: IAMClient,
) -> None:
    """Unit test cross account role account id & external id validation success."""
    config: Dict[str, Any] = {
        "env": {
            "aws": {
                "role": {
                    "name": {"cross_account": "arn:aws:iam::1234:role/cross_acct_role"}
                }
            },
            "cdp": {
                "cross_account": {
                    "account_id": 706388717391,
                    "external_id": "a7e9d31f-b0b9-4c4a-abf9-d8dd8b3456c8",
                }
            },
        }
    }
    stubber = Stubber(iam_client)
    stubber.add_response(
        "get_role",
        {
            "Role": {
                "Path": "/",
                "RoleName": "cross_acct_role",
                "RoleId": "AROAUPTUOROPIQUKF63E5",
                "Arn": "arn:aws:iam::308408126366:role/cross_acct_role",
                "CreateDate": "2016-01-01T00:00:00.000Z",
                "AssumeRolePolicyDocument": """{
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Principal": {
                                "Service": ["ec2.amazonaws.com", "s3.amazonaws.com"]
                            },
                            "Action": "sts:AssumeRole",
                        },
                        {
                            "Effect": "Allow",
                            "Principal": {
                                "AWS": [
                                    "arn:aws:iam::463114675373:user/cross-account-trust-user",
                                    'arn:aws:iam::706388717391:user/cross-account-trust-user',
                                    'arn:aws:iam::649540440146:root',
                                    'arn:aws:iam::387553343826:root'
                                ]
                            },
                            "Action": "sts:AssumeRole",
                            "Condition": {
                                "StringEquals": {
                                    "sts:ExternalId": [
                                        "a7e9d31f-b0b9-4c4a-abf9-d8dd8b3456c8",
                                    ]
                                }
                            },
                        },
                    ],
                }""",
                "MaxSessionDuration": 3600,
                "RoleLastUsed": {
                    "LastUsedDate": "2016-01-01T00:00:00.000Z",
                    "Region": "us-west-2",
                },
            },
            "ResponseMetadata": {
                "RequestId": "4c886bbb-615c-427b-8ef9-b9a174c5cb66",
                "HTTPStatusCode": 200,
                "HTTPHeaders": {
                    "x-amzn-requestid": "4c886bbb-615c-427b-8ef9-b9a174c5cb66",
                    "content-type": "text/xml",
                    "content-length": "2370",
                    "vary": "accept-encoding",
                    "date": "Mon, 26 Jul 2021 03:24:51 GMT",
                },
                "RetryAttempts": 0,
            },
        },
        expected_params={"RoleName": "arn:aws:iam::1234:role/cross_acct_role"},
    )
    with stubber:
        func = expect_validation_success(aws_cross_account_role_exists_validation)
        func(config, iam_client)
    with stubber:
        func = expect_validation_success(aws_cross_account_role_account_id_validation)
        func(config, iam_client)
    with stubber:
        func = expect_validation_success(aws_cross_account_role_external_id_validation)
        func(config, iam_client)


@pytest.mark.skip(reason="Type issue between aws get_role vs boto3 Iam client get_role")
def test_aws_cross_account_role_account_id_and_external_id_validation_failure(
    iam_client: IAMClient,
) -> None:
    """Unit test cross account role account id & external id validation failure scenario."""
    config: Dict[str, Any] = {
        "env": {
            "aws": {
                "role": {
                    "name": {"cross_account": "arn:aws:iam::1234:role/cross_acct_role"}
                }
            },
            "cdp": {
                "cross_account": {
                    "account_id": 308408126366,
                    "external_id": "a7e9d31f-b0b9-4c4a-abf9-d8dd8b3456c8",
                }
            },
        }
    }
    stubber = Stubber(iam_client)
    stubber.add_response(
        "get_role",
        {
            "Role": {
                "Path": "/",
                "RoleName": "cross_acct_role",
                "RoleId": "AROAUPTUOROPIQUKF63E5",
                "Arn": "arn:aws:iam::3084FAILURE:role/cross_acct_role",
                "CreateDate": "2016-01-01T00:00:00.000Z",
                "AssumeRolePolicyDocument": """{
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Principal": {
                                "Service": ["ec2.amazonaws.com", "s3.amazonaws.com"]
                            },
                            "Action": "sts:AssumeRole",
                        },
                        {
                            "Effect": "Allow",
                            "Principal": {
                                "AWS": [
                                    "arn:aws:iam::463114675373:user/cross-account-trust-user",
                                ]
                            },
                            "Action": "sts:AssumeRole",
                            "Condition": {
                                "StringEquals": {
                                    "sts:ExternalId": [
                                        "a7e9d31f-b0b9-4c4a-abf9-d8dd8b3456c8",
                                    ]
                                }
                            },
                        },
                    ],
                }""",
                "MaxSessionDuration": 3600,
                "RoleLastUsed": {
                    "LastUsedDate": "2016-01-01T00:00:00.000Z",
                    "Region": "us-west-2",
                },
            },
            "ResponseMetadata": {
                "RequestId": "4c886bbb-615c-427b-8ef9-b9a174c5cb66",
                "HTTPStatusCode": 200,
                "HTTPHeaders": {
                    "x-amzn-requestid": "4c886bbb-615c-427b-8ef9-b9a174c5cb66",
                    "content-type": "text/xml",
                    "content-length": "2370",
                    "vary": "accept-encoding",
                    "date": "Mon, 26 Jul 2021 03:24:51 GMT",
                },
                "RetryAttempts": 0,
            },
        },
        expected_params={"RoleName": "arn:aws:iam::1234:role/cross_acct_role"},
    )
    with stubber:
        func = expect_validation_success(aws_cross_account_role_exists_validation)
        func(config, iam_client)
    with stubber:
        func = expect_validation_failure(aws_cross_account_role_account_id_validation)
        func(config, iam_client)
    with stubber:
        func = expect_validation_success(aws_cross_account_role_external_id_validation)
        func(config, iam_client)


def test_aws_cross_account_role_ec2_needed_actions_validation_success(
    ec2_needed_actions: List[str],
    iam_client: IAMClient,
) -> None:
    """Unit test cross account role ec2 needed actions validation success."""
    cross_account_role_data["role_arn"] = "arn:aws:iam::1234:role/cross_acct_role"

    stubber = Stubber(iam_client)

    add_simulate_policy_response(
        stubber=stubber,
        role_arn=cross_account_role_data["role_arn"],
        resource_arns=["*"],
        actions=ec2_needed_actions,
        failSimulatePolicy=False,
    )
    with stubber:
        func = expect_validation_success(
            aws_cross_account_role_ec2_needed_actions_validation
        )
        func(ec2_needed_actions, iam_client)


def test_aws_cross_account_role_ec2_needed_actions_validation_failure(
    ec2_needed_actions: List[str],
    iam_client: IAMClient,
) -> None:
    """Unit test cross account role ec2 needed actions validation failure."""
    cross_account_role_data["role_arn"] = "arn:aws:iam::1234:role/cross_acct_role"

    stubber = Stubber(iam_client)

    add_simulate_policy_response(
        stubber=stubber,
        role_arn=cross_account_role_data["role_arn"],
        resource_arns=["*"],
        actions=ec2_needed_actions,
        failSimulatePolicy=True,
    )
    with stubber:
        func = expect_validation_failure(
            aws_cross_account_role_ec2_needed_actions_validation
        )
        func(ec2_needed_actions, iam_client)


def test_aws_cross_account_role_autoscaling_resources_needed_actions_validation_success(
    autoscaling_resources_needed_actions: List[str],
    iam_client: IAMClient,
) -> None:
    """Unit test cross account role autoscaling resources needed actions validation success."""
    cross_account_role_data["role_arn"] = "arn:aws:iam::1234:role/cross_acct_role"

    stubber = Stubber(iam_client)

    add_simulate_policy_response(
        stubber=stubber,
        role_arn=cross_account_role_data["role_arn"],
        resource_arns=["*"],
        actions=autoscaling_resources_needed_actions,
        failSimulatePolicy=False,
    )
    with stubber:
        func = expect_validation_success(
            aws_cross_account_role_autoscaling_resources_needed_actions_validation
        )
        func(autoscaling_resources_needed_actions, iam_client)


def test_aws_cross_account_role_autoscaling_resources_needed_actions_validation_failure(
    autoscaling_resources_needed_actions: List[str],
    iam_client: IAMClient,
) -> None:
    """Unit test cross account role autoscaling resources needed actions validation failure."""
    cross_account_role_data["role_arn"] = "arn:aws:iam::1234:role/cross_acct_role"

    stubber = Stubber(iam_client)

    add_simulate_policy_response(
        stubber=stubber,
        role_arn=cross_account_role_data["role_arn"],
        resource_arns=["*"],
        actions=autoscaling_resources_needed_actions,
        failSimulatePolicy=True,
    )
    with stubber:
        func = expect_validation_failure(
            aws_cross_account_role_autoscaling_resources_needed_actions_validation
        )
        func(autoscaling_resources_needed_actions, iam_client)


def test_aws_cross_account_role_cloud_formation_needed_actions_validation_success(
    cloud_formation_needed_actions: List[str],
    iam_client: IAMClient,
) -> None:
    """Unit test cross account role cloud formation needed actions validation success."""
    cross_account_role_data["role_arn"] = "arn:aws:iam::1234:role/cross_acct_role"

    stubber = Stubber(iam_client)

    add_simulate_policy_response(
        stubber=stubber,
        role_arn=cross_account_role_data["role_arn"],
        resource_arns=["*"],
        actions=cloud_formation_needed_actions,
        failSimulatePolicy=False,
    )
    with stubber:
        func = expect_validation_success(
            aws_cross_account_role_cloud_formation_needed_actions_validation
        )
        func(cloud_formation_needed_actions, iam_client)


def test_aws_cross_account_role_cloud_formation_needed_actions_validation_failure(
    cloud_formation_needed_actions: List[str],
    iam_client: IAMClient,
) -> None:
    """Unit test cross account role cloud formation needed actions validation failure."""
    cross_account_role_data["role_arn"] = "arn:aws:iam::1234:role/cross_acct_role"

    stubber = Stubber(iam_client)

    add_simulate_policy_response(
        stubber=stubber,
        role_arn=cross_account_role_data["role_arn"],
        resource_arns=["*"],
        actions=cloud_formation_needed_actions,
        failSimulatePolicy=True,
    )
    with stubber:
        func = expect_validation_failure(
            aws_cross_account_role_cloud_formation_needed_actions_validation
        )
        func(cloud_formation_needed_actions, iam_client)


def test_aws_cross_account_role_cdp_environment_resources_needed_actions_validation_success(
    cdp_environment_resources_needed_actions: List[str],
    iam_client: IAMClient,
) -> None:
    """Unit test cross account role cdp environment resources needed actions validation success."""
    cross_account_role_data["role_arn"] = "arn:aws:iam::1234:role/cross_acct_role"

    stubber = Stubber(iam_client)

    add_simulate_policy_response(
        stubber=stubber,
        role_arn=cross_account_role_data["role_arn"],
        resource_arns=["*"],
        actions=cdp_environment_resources_needed_actions,
        failSimulatePolicy=False,
    )
    with stubber:
        func = expect_validation_success(
            aws_cross_account_role_cdp_environment_resources_needed_actions_validation
        )
        func(cdp_environment_resources_needed_actions, iam_client)


def test_aws_cross_account_role_cdp_environment_resources_needed_actions_validation_failure(
    cdp_environment_resources_needed_actions: List[str],
    iam_client: IAMClient,
) -> None:
    """Unit test cross account role cdp environment resources needed actions validation failure."""
    cross_account_role_data["role_arn"] = "arn:aws:iam::1234:role/cross_acct_role"

    stubber = Stubber(iam_client)

    add_simulate_policy_response(
        stubber=stubber,
        role_arn=cross_account_role_data["role_arn"],
        resource_arns=["*"],
        actions=cdp_environment_resources_needed_actions,
        failSimulatePolicy=True,
    )
    with stubber:
        func = expect_validation_failure(
            aws_cross_account_role_cdp_environment_resources_needed_actions_validation
        )
        func(cdp_environment_resources_needed_actions, iam_client)


def test_aws_cross_account_role_pass_role_needed_actions_validation_success(
    pass_role_needed_actions: List[str],
    iam_client: IAMClient,
) -> None:
    """Unit test cross account role pass role needed actions validation success."""
    cross_account_role_data["role_arn"] = "arn:aws:iam::1234:role/cross_acct_role"

    stubber = Stubber(iam_client)

    add_simulate_policy_response(
        stubber=stubber,
        role_arn=cross_account_role_data["role_arn"],
        resource_arns=["*"],
        actions=pass_role_needed_actions,
        failSimulatePolicy=False,
    )
    with stubber:
        func = expect_validation_success(
            aws_cross_account_role_pass_role_needed_actions_validation
        )
        func(pass_role_needed_actions, iam_client)


def test_aws_cross_account_role_pass_role_needed_actions_validation_failure(
    pass_role_needed_actions: List[str],
    iam_client: IAMClient,
) -> None:
    """Unit test cross account role pass role needed actions validation failure."""
    cross_account_role_data["role_arn"] = "arn:aws:iam::1234:role/cross_acct_role"

    stubber = Stubber(iam_client)

    add_simulate_policy_response(
        stubber=stubber,
        role_arn=cross_account_role_data["role_arn"],
        resource_arns=["*"],
        actions=pass_role_needed_actions,
        failSimulatePolicy=True,
    )
    with stubber:
        func = expect_validation_failure(
            aws_cross_account_role_pass_role_needed_actions_validation
        )
        func(pass_role_needed_actions, iam_client)


def test_aws_cross_account_role_identity_management_needed_actions_validation_success(
    identity_management_needed_actions: List[str],
    iam_client: IAMClient,
) -> None:
    """Unit test cross account role identity management needed actions validation success."""
    cross_account_role_data["role_arn"] = "arn:aws:iam::1234:role/cross_acct_role"

    stubber = Stubber(iam_client)

    add_simulate_policy_response(
        stubber=stubber,
        role_arn=cross_account_role_data["role_arn"],
        resource_arns=["arn:aws:iam::*:role/aws-service-role/*"],
        actions=identity_management_needed_actions,
        failSimulatePolicy=False,
    )
    with stubber:
        func = expect_validation_success(
            aws_cross_account_identity_management_needed_actions_validation
        )
        func(identity_management_needed_actions, iam_client)


def test_aws_cross_account_role_identity_management_needed_actions_validation_failure(
    identity_management_needed_actions: List[str],
    iam_client: IAMClient,
) -> None:
    """Unit test cross account role identity management needed actions validation failure."""
    cross_account_role_data["role_arn"] = "arn:aws:iam::1234:role/cross_acct_role"

    stubber = Stubber(iam_client)

    add_simulate_policy_response(
        stubber=stubber,
        role_arn=cross_account_role_data["role_arn"],
        resource_arns=["arn:aws:iam::*:role/aws-service-role/*"],
        actions=identity_management_needed_actions,
        failSimulatePolicy=True,
    )
    with stubber:
        func = expect_validation_failure(
            aws_cross_account_identity_management_needed_actions_validation
        )
        func(identity_management_needed_actions, iam_client)
