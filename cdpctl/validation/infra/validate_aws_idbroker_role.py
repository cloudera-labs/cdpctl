#!/usr/bin/env python3
# -*- coding:utf-8 -*-
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
# Source File Name:  validate_aws_idbroker_role.py
###
"""Validation of AWS Idbroker Role."""
import json
from typing import Any, Dict, List

import pytest
from boto3_type_annotations.iam import Client as IAMClient

from cdpctl.validation import get_config_value, validator
from cdpctl.validation.aws_utils import (
    convert_s3a_to_arn,
    parse_arn,
    simulate_policy,
    get_instance_profile,
    get_client,
    get_role,
)


@pytest.fixture(autouse=True, name="iam_client")
def iam_client_fixture(config: Dict[str, Any]) -> IAMClient:
    """Return an AWS IAM Client."""
    return get_client("iam", config)


def get_idbroker_instance_profile(
    config: Dict[str, Any], iam_client: IAMClient
) -> Dict:  # pragma: no cover
    """Get the idbroker instance profile from the config."""
    idbroker_instance_profile: str = get_config_value(
        config,
        "env:aws:instance_profile:name:idbroker",
        key_missing_message=(
            "No idbroker instance profile defined for config option: {}"
        ),
        data_expected_error_message=(
            "No idbroker instance profile provided for config option: {}"
        ),
    )

    return get_instance_profile(iam_client, idbroker_instance_profile)


@pytest.mark.aws
@pytest.mark.infra
def aws_idbroker_instance_profile_exists_with_role_validation(
    config: Dict[str, Any], iam_client: IAMClient
) -> None:  # pragma: no cover
    """IdBroker instance profile exists with a role."""  # noqa: D401,E501
    _aws_idbroker_instance_profile_exists_with_role_validation(config, iam_client)


@validator
def _aws_idbroker_instance_profile_exists_with_role_validation(
    config: Dict[str, Any], iam_client: IAMClient
) -> None:  # pragma: no cover
    """IdBroker instance profile exists with a role."""  # noqa: D401,E501
    profile = get_idbroker_instance_profile(config=config, iam_client=iam_client)

    if not profile["InstanceProfile"]["Roles"]:
        pytest.fail(
            """IdBroker instance profile {} set in config env:aws:instance_profile:name:idbroker
             should contain a idbroker role.""".format(
                profile["InstanceProfile"]["Arn"]
            ),
            False,
        )


@pytest.mark.aws
@pytest.mark.infra
@pytest.mark.dependency(
    depends=[
        "aws_idbroker_instance_profile_exists_with_role_validation",
    ]
)
def aws_idbroker_role_has_ec2_trust_policy_validation(
    config: Dict[str, Any], iam_client: IAMClient
) -> None:  # pragma: no cover
    """IdBroker role has the EC2 trust policy."""  # noqa: D401,E501
    _aws_idbroker_role_has_ec2_trust_policy_validation(config, iam_client)


@validator
def _aws_idbroker_role_has_ec2_trust_policy_validation(
    config: Dict[str, Any], iam_client: IAMClient
) -> None:  # pragma: no cover
    """Validating that IdBroker role has the ec2 trust policy."""  # noqa: D401,E501
    profile = get_idbroker_instance_profile(config=config, iam_client=iam_client)

    role = profile["InstanceProfile"]["Roles"][0]
    role_assume_policy = role["AssumeRolePolicyDocument"]

    if isinstance(role_assume_policy, str):
        assume_policy_statement = json.loads(role_assume_policy)["Statement"]
    else:
        assume_policy_statement = role_assume_policy["Statement"]

    found_ec2_trust = False
    for trust_policy in assume_policy_statement:
        try:
            if (
                trust_policy["Effect"] == "Allow"
                and "ec2.amazonaws.com" in trust_policy["Principal"]["Service"]
                and trust_policy["Action"] == "sts:AssumeRole"
            ):
                found_ec2_trust = True
                break
        except KeyError:
            continue

    if not found_ec2_trust:
        pytest.fail(
            """The idbroker role {} should contain a trust policy for ec2""".format(
                role
            ),
            False,
        )


@pytest.mark.aws
@pytest.mark.infra
@pytest.mark.dependency(
    depends=[
        "aws_idbroker_instance_profile_exists_with_role_validation",
    ]
)
def aws_idbroker_role_has_assumerole_policy_validation(
    config: Dict[str, Any], iam_client: IAMClient
) -> None:  # pragma: no cover
    """IdBroker role can assume the Ranger Audit and Datalake Admin Roles."""  # noqa: D401,E501
    _aws_idbroker_role_has_assumerole_policy_validation(config, iam_client)


@validator
def _aws_idbroker_role_has_assumerole_policy_validation(
    config: Dict[str, Any], iam_client: IAMClient
) -> None:  # pragma: no cover
    """Validating that the idbroker role has the AssumeRole for Ranger Audit and Datalake Admin Roles."""  # noqa: D401,E501
    idbroker_profile = get_idbroker_instance_profile(
        config=config, iam_client=iam_client
    )
    idbroker_role_arn = idbroker_profile["InstanceProfile"]["Roles"][0]["Arn"]

    ranger_audit_role_name: str = get_config_value(
        config,
        "env:aws:role:name:ranger_audit",
        key_missing_message="No role defined for config option: {0}",
        data_expected_error_message="No role was provided for config option: {0}",
    )
    ranger_audit_role = get_role(iam_client, ranger_audit_role_name)
    ranger_audit_role_arn = ranger_audit_role["Role"]["Arn"]

    datalake_admin_role_name: str = get_config_value(
        config,
        "env:aws:role:name:datalake_admin",
        key_missing_message="No role defined for config option: {0}",
        data_expected_error_message="No role was provided for config option: {0}",
    )

    datalake_admin_role = get_role(iam_client, datalake_admin_role_name)
    datalake_admin_role_arn = datalake_admin_role["Role"]["Arn"]

    simulate_policy(
        iam_client,
        idbroker_role_arn,
        [ranger_audit_role_arn, datalake_admin_role_arn],
        ["sts:AssumeRole"],
        f"The role ({idbroker_role_arn}) requires the following "
        f"actions for resource wildcard (*) :\n{{}}",
    )


@pytest.mark.aws
@pytest.mark.infra
@pytest.mark.dependency(
    depends=[
        "aws_idbroker_instance_profile_exists_with_role_validation",
    ]
)
def aws_idbroker_role_has_necessary_s3_actions_validation(
    config: Dict[str, Any], logs_needed_actions: List[str], iam_client: IAMClient
) -> None:
    """IdBroker role has the necessary S3 logs location actions."""  # noqa: D401
    _aws_idbroker_role_has_necessary_s3_actions_validation(
        config, iam_client, logs_needed_actions
    )


@validator
def _aws_idbroker_role_has_necessary_s3_actions_validation(
    config: Dict[str, Any],
    iam_client: IAMClient,
    logs_needed_actions: List[str],
) -> None:
    """Check the idbroker role has the necessary s3 actions."""
    profile = get_idbroker_instance_profile(config=config, iam_client=iam_client)
    role = profile["InstanceProfile"]["Roles"][0]
    role_arn = role["Arn"]

    log_location: str = get_config_value(
        config,
        "infra:aws:vpc:existing:storage:logs",
        key_missing_message="No log storage path defined for config option: {}",
        data_expected_error_message="No log storage path provided for config option: {}",  # noqa: E501
    )
    log_location_arn = convert_s3a_to_arn(log_location)

    simulate_policy(
        iam_client,
        role_arn,
        [log_location_arn, f"{log_location_arn}/*"],
        logs_needed_actions,
        f"""The role ({role_arn}) requires the following actions
         for the log storage path ({log_location}):\n{{}}""",
    )


@pytest.mark.aws
@pytest.mark.infra
@pytest.mark.dependency(
    depends=[
        "aws_idbroker_instance_profile_exists_with_role_validation",
    ]
)
def aws_idbroker_role_has_necessary_s3_bucket_actions_validation(
    config: Dict[str, Any], log_bucket_needed_actions: List[str], iam_client: IAMClient
) -> None:
    """IdBroker role has the necessary S3 bucket actions."""  # noqa: D401
    _aws_idbroker_role_has_necessary_s3_bucket_actions_validation(
        config,
        iam_client,
        log_bucket_needed_actions,
    )


@validator
def _aws_idbroker_role_has_necessary_s3_bucket_actions_validation(
    config: Dict[str, Any],
    iam_client: IAMClient,
    log_bucket_needed_actions: List[str],
) -> None:
    """Check the idbroker role has the necessary s3 bucket actions."""
    profile = get_idbroker_instance_profile(config=config, iam_client=iam_client)
    role = profile["InstanceProfile"]["Roles"][0]
    role_arn = role["Arn"]

    log_location: str = get_config_value(
        config,
        "infra:aws:vpc:existing:storage:logs",
        key_missing_message="No log storage path defined for config option: {}",
        data_expected_error_message="No log storage path provided for config option: {}",  # noqa: E501
    )

    log_location_arn = convert_s3a_to_arn(log_location)
    log_bucket_name = parse_arn(log_location_arn)["resource_type"]
    log_bucket_arn = convert_s3a_to_arn(f"s3a://{log_bucket_name}")

    simulate_policy(
        iam_client,
        role_arn,
        [log_bucket_arn, f"{log_bucket_arn}/*"],
        log_bucket_needed_actions,
        f"""The role ({role_arn}) requires the following actions
         for the log storage bucket ({log_bucket_arn}):\n{{}}""",
    )
