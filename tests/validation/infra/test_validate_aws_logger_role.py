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
# Source File Name:  test_validate_aws_logger_role.py
###
"""Test of validate_logger_role."""
from typing import Any, Dict, List

import boto3
from boto3_type_annotations.iam import Client as IAMClient
from botocore.stub import Stubber
from moto import mock_iam

from cdpctl.validation.aws_utils import convert_s3a_to_arn, parse_arn
from cdpctl.validation.infra.validate_aws_logger_role import (
    _aws_logger_instance_profile_exists_with_role_validation,
    _aws_logger_role_has_ec2_trust_policy_validation,
    _aws_logger_role_has_necessary_s3_actions_validation,
    _aws_logger_role_has_necessary_s3_bucket_actions_validation,
)
from tests.validation import expect_validation_failure, expect_validation_success
from tests.validation.test_aws_utils import (
    add_get_profile_response,
    add_simulate_policy_response,
)

log_location: str = "s3a://test-bucket/test-folder/logs"
log_location_arn = convert_s3a_to_arn(log_location)
log_bucket_name = parse_arn(log_location_arn)["resource_type"]
log_bucket_arn = convert_s3a_to_arn(f"s3a://{log_bucket_name}")
logger_role: str = "arn:aws:iam::214178861886:role/test-role"
logger_instance_profile: str = "arn:aws:iam::214178861886:instance-profile/test-role"

config: Dict[str, Any] = {
    "env": {
        "aws": {"instance_profile": {"name": {"log": f"{logger_instance_profile}"}}}
    },
    "infra": {"aws": {"vpc": {"existing": {"storage": {"logs": f"{log_location}"}}}}},
}


@mock_iam
def test_logger_instance_profile_with_role() -> None:
    """Verify validation succeeds with an instance profile with a role."""
    iam_client: IAMClient = boto3.client("iam")
    stubber = Stubber(iam_client)
    add_get_profile_response(
        stubber=stubber,
        role_arn=logger_instance_profile,
        includeRole=True,
        includeTrustPolicy=True,
    )

    with stubber:
        func = expect_validation_success(
            _aws_logger_instance_profile_exists_with_role_validation
        )
        func(config, iam_client)


@mock_iam
def test_logger_instance_profile_with_no_role() -> None:
    """Verify validation fails without a role within the logger instance profile."""
    iam_client: IAMClient = boto3.client("iam")
    stubber = Stubber(iam_client)
    add_get_profile_response(
        stubber=stubber,
        role_arn=logger_instance_profile,
        includeRole=False,
        includeTrustPolicy=True,
    )

    with stubber:
        func = expect_validation_failure(
            _aws_logger_instance_profile_exists_with_role_validation
        )
        func(config, iam_client)


@mock_iam
def test_logger_role_with_no_trust_policy() -> None:
    """Verify validation fails without a trust policy in the logger role."""
    iam_client: IAMClient = boto3.client("iam")
    stubber = Stubber(iam_client)
    add_get_profile_response(
        stubber=stubber,
        role_arn=logger_instance_profile,
        includeRole=True,
        includeTrustPolicy=False,
    )

    with stubber:
        func = expect_validation_failure(
            _aws_logger_role_has_ec2_trust_policy_validation
        )
        func(config, iam_client)


@mock_iam
def test_logger_role_with_trust_policy() -> None:
    """Verify validation passes with a trust policy in the logger role."""
    iam_client: IAMClient = boto3.client("iam")
    stubber = Stubber(iam_client)
    add_get_profile_response(
        stubber=stubber,
        role_arn=logger_instance_profile,
        includeRole=True,
        includeTrustPolicy=True,
    )

    with stubber:
        func = expect_validation_success(
            _aws_logger_role_has_ec2_trust_policy_validation
        )
        func(config, iam_client)


@mock_iam
def test_logger_role_with_valid_s3_policies(
    logs_needed_actions: List[str],  # noqa: F811
) -> None:
    """Verify s3 policies validation passes with passing policy simulations."""
    iam_client: IAMClient = boto3.client("iam")
    stubber = Stubber(iam_client)
    add_get_profile_response(
        stubber=stubber,
        role_arn=logger_instance_profile,
        includeRole=True,
        includeTrustPolicy=True,
    )

    add_simulate_policy_response(
        stubber=stubber,
        role_arn=logger_instance_profile,
        resource_arns=[log_location_arn, f"{log_location_arn}/*"],
        actions=logs_needed_actions,
        failSimulatePolicy=False,
    )

    with stubber:
        func = expect_validation_success(
            _aws_logger_role_has_necessary_s3_actions_validation
        )
        func(config, iam_client, logs_needed_actions)


@mock_iam
def test_logger_role_with_invalid_s3_policies(
    logs_needed_actions: List[str],  # noqa: F811
) -> None:
    """Verify s3 policies validation passes with passing policy simulations."""
    iam_client: IAMClient = boto3.client("iam")
    stubber = Stubber(iam_client)
    add_get_profile_response(
        stubber=stubber,
        role_arn=logger_instance_profile,
        includeRole=True,
        includeTrustPolicy=True,
    )

    add_simulate_policy_response(
        stubber=stubber,
        role_arn=logger_instance_profile,
        resource_arns=[log_location_arn, f"{log_location_arn}/*"],
        actions=logs_needed_actions,
        failSimulatePolicy=True,
    )

    with stubber:
        func = expect_validation_failure(
            _aws_logger_role_has_necessary_s3_actions_validation
        )
        func(config, iam_client, logs_needed_actions)


@mock_iam
def test_logger_role_with_valid_s3_bucket_policies(
    log_bucket_needed_actions: List[str],  # noqa: F811
) -> None:
    """Verify s3 policies validation passes with passing policy simulations."""
    iam_client: IAMClient = boto3.client("iam")
    stubber = Stubber(iam_client)
    add_get_profile_response(
        stubber=stubber,
        role_arn=logger_instance_profile,
        includeRole=True,
        includeTrustPolicy=True,
    )

    add_simulate_policy_response(
        stubber=stubber,
        role_arn=logger_instance_profile,
        resource_arns=[log_bucket_arn, f"{log_bucket_arn}/*"],
        actions=log_bucket_needed_actions,
        failSimulatePolicy=False,
    )

    with stubber:
        func = expect_validation_success(
            _aws_logger_role_has_necessary_s3_bucket_actions_validation
        )
        func(config, iam_client, log_bucket_needed_actions)


@mock_iam
def test_logger_role_with_invalid_s3_bucket_policies(
    log_bucket_needed_actions: List[str],  # noqa: F811
) -> None:
    """Verify s3 policies validation passes with passing policy simulations."""
    iam_client: IAMClient = boto3.client("iam")
    stubber = Stubber(iam_client)
    add_get_profile_response(
        stubber=stubber,
        role_arn=logger_instance_profile,
        includeRole=True,
        includeTrustPolicy=True,
    )

    add_simulate_policy_response(
        stubber=stubber,
        role_arn=logger_instance_profile,
        resource_arns=[log_bucket_arn, f"{log_bucket_arn}/*"],
        actions=log_bucket_needed_actions,
        failSimulatePolicy=True,
    )

    with stubber:
        func = expect_validation_failure(
            _aws_logger_role_has_necessary_s3_bucket_actions_validation
        )
        func(config, iam_client, log_bucket_needed_actions)
