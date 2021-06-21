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
# Source File Name:  validate_aws_ranger_audit_role.py
###
"""Validation of AWS IAM Ranger Audit Role."""
from typing import Any, Dict, List

import pytest

from boto3_type_annotations.iam import Client as IAMClient
from cdpctl.validation import get_config_value
from cdpctl.validation.aws_utils import (
    convert_dynamodb_table_to_arn,
    convert_s3a_to_arn,
    get_role,
    parse_arn,
    simulate_policy,
    get_client,
)


ranger_audit_data = {}


@pytest.fixture(autouse=True, name="iam_client")
def iam_client_fixture(config: Dict[str, Any]) -> IAMClient:
    """Returns an IAMClient."""  # noqa: D401
    return get_client("iam", config)


@pytest.mark.aws
@pytest.mark.infra
def aws_ranger_audit_role_exists_validation(
    config: Dict[str, Any], iam_client: IAMClient
) -> None:  # pragma: no cover
    """Ranger audit role exists."""  # noqa: D401
    ranger_audit_role: str = get_config_value(
        config,
        "env:aws:role:name:ranger_audit",
        key_missing_message="No role defined for config option: {0}",
        data_expected_error_message="No role was provided for config option: {0}",
    )

    # ranger audit role arn
    role = get_role(iam_client, ranger_audit_role)
    role_arn = role["Role"]["Arn"]
    ranger_audit_data["role_arn"] = role_arn
    ranger_audit_data["ranger_audit_role"] = ranger_audit_role


@pytest.mark.aws
@pytest.mark.infra
def aws_ranger_audit_role_data_location_exist_validation(
    config: Dict[str, Any], iam_client: IAMClient
) -> None:  # pragma: no cover
    """Ranger data location exists."""  # noqa: D401
    data_location: str = get_config_value(
        config,
        "infra:aws:vpc:existing:storage:data",
        key_missing_message="No s3a url defined for config option: {0}",
        data_expected_error_message="No s3a url was provided for config option: {0}",
    )
    # data access s3 bucket arn
    data_location_arn = convert_s3a_to_arn(data_location)

    ranger_audit_data["data_location"] = data_location
    ranger_audit_data["data_location_arn"] = data_location_arn


@pytest.mark.aws
@pytest.mark.infra
def aws_ranger_audit_role_audit_location_exist_validation(
    config: Dict[str, Any], iam_client: IAMClient
) -> None:  # pragma: no cover
    """Ranger audit location exist."""  # noqa: D401
    ranger_audit_location: str = get_config_value(
        config,
        "infra:aws:vpc:existing:storage:ranger_audit",
        key_missing_message="No ranger audit s3a url defined for config option: {0}",
        data_expected_error_message="No ranger audit s3a url was provided for config "
        "option: {0}",
    )

    # ranger audit s3 bucket arn
    ranger_audit_location_arn = convert_s3a_to_arn(ranger_audit_location)
    ranger_audit_bucket_name = parse_arn(ranger_audit_location_arn)["resource_type"]
    ranger_audit_bucket_arn = convert_s3a_to_arn(f"s3a://{ranger_audit_bucket_name}")

    ranger_audit_data["ranger_audit_location"] = ranger_audit_location
    ranger_audit_data["ranger_audit_bucket_arn"] = ranger_audit_bucket_arn
    ranger_audit_data["ranger_audit_location_arn"] = ranger_audit_location_arn


@pytest.mark.aws
@pytest.mark.infra
def aws_ranger_audit_role_dynamoDB_table_exist_validation(
    config: Dict[str, Any], iam_client: IAMClient
) -> None:  # pragma: no cover
    """Ranger DynamoDB table exists."""  # noqa: D401
    dynamodb_table: str = get_config_value(
        config,
        "infra:aws:dynamodb:table_name",
        key_missing_message="No table name was defined for config option: {0}",
        data_expected_error_message="No table name was provided for config option: {0}",
    )
    # dynamoDB table arn
    dynamodb_table_arn = convert_dynamodb_table_to_arn(dynamodb_table)
    ranger_audit_data["dynamodb_table_arn"] = dynamodb_table_arn


@pytest.mark.aws
@pytest.mark.infra
def aws_ranger_audit_location_needed_actions_validation(
    ranger_audit_location_needed_actions: List[str], iam_client: IAMClient
) -> None:
    """Ranger audit role has needed actions for the audit location."""  # noqa: D401
    try:
        # aws-cdp-ranger-audit-s3-policy
        simulate_policy(
            iam_client,
            ranger_audit_data["role_arn"],
            [ranger_audit_data["ranger_audit_location_arn"] + "/*"],
            ranger_audit_location_needed_actions,
            f"""The role ({ranger_audit_data["ranger_audit_role"]}) requires the
            following actions for the datalake S3 bucket
            ({ranger_audit_data["ranger_audit_location_arn"] + "/*"}) : \n {{}}""",
        )
    except KeyError as e:
        pytest.fail(f"Validation error - missing required data : {e.args[0]}", False)


@pytest.mark.aws
@pytest.mark.infra
@pytest.mark.dependency(
    depends=[
        "aws_ranger_audit_role_exists_validation",
        "aws_ranger_audit_role_audit_location_exist_validation",
    ]
)
def aws_ranger_audit_s3_bucket_needed_actions_validation(
    ranger_audit_bucket_needed_actions: List[str], iam_client: IAMClient
) -> None:
    """Ranger audit role has the needed actions for audit s3."""  # noqa: D401
    try:
        simulate_policy(
            iam_client,
            ranger_audit_data["role_arn"],
            [ranger_audit_data["ranger_audit_bucket_arn"]],
            ranger_audit_bucket_needed_actions,
            f"""The role ({ranger_audit_data["ranger_audit_role"]}) requires the
            following actions for the datalake S3 bucket
            ({ranger_audit_data["ranger_audit_bucket_arn"]}) : \n {{}}""",
        )
    except KeyError as e:
        pytest.fail(f"Validation error - missing required data : {e.args[0]}", False)


@pytest.mark.aws
@pytest.mark.infra
def aws_ranger_audit_cdp_s3_needed_actions_validation(
    s3_needed_actions_to_all: List[str], iam_client: IAMClient
) -> None:
    """Ranger audit role has the needed actions for CDP S3."""  # noqa: D401
    try:
        # aws-cdp-bucket-access-policy
        simulate_policy(
            iam_client,
            ranger_audit_data["role_arn"],
            ["*"],
            s3_needed_actions_to_all,
            f"""The role ({ranger_audit_data["ranger_audit_role"]}) requires the
            following actions for all S3 resources ([*]) : \n {{}}""",
        )
    except KeyError as e:
        pytest.fail(f"Validation error - missing required data : {e.args[0]}", False)


@pytest.mark.aws
@pytest.mark.infra
def aws_ranger_audit_data_location_needed_actions_validation(
    data_location_needed_actions: List[str], iam_client: IAMClient
) -> None:
    """Ranger audit role has needed actions for the data location."""  # noqa: D401
    try:
        simulate_policy(
            iam_client,
            ranger_audit_data["role_arn"],
            [
                ranger_audit_data["data_location_arn"],
                ranger_audit_data["data_location_arn"] + "/*",
            ],
            data_location_needed_actions,
            f"""The role ({ranger_audit_data["ranger_audit_role"]}) requires the
            following actions for the S3 data location ({ranger_audit_data["data_location_arn"]
                + " "
                + ranger_audit_data["data_location_arn"]
                + "/*"}): \n {{}}""",
        )
    except KeyError as e:
        pytest.fail(f"Validation error - missing required data : {e.args[0]}", False)


@pytest.mark.aws
@pytest.mark.infra
@pytest.mark.dependency(depends=["aws_ranger_audit_role_exists_validation"])
def aws_ranger_audit_dynamoDB_needed_actions_validation(
    dynamodb_needed_actions_to_all: List[str], iam_client: IAMClient
) -> None:
    """Ranger audit role has the needed actions for DynamoDB."""  # noqa: D401
    try:
        # aws-cdp-dynamodb-policy
        simulate_policy(
            iam_client,
            ranger_audit_data["role_arn"],
            ["*"],
            dynamodb_needed_actions_to_all,
            f"""The role ({ranger_audit_data["ranger_audit_role"]}) requires the
            following actions for all Dynamodb resources ([*]) : \n {{}}""",
        )
    except KeyError as e:
        pytest.fail(f"Validation error - missing required data : {e.args[0]}", False)


@pytest.mark.aws
@pytest.mark.infra
@pytest.mark.dependency(
    depends=[
        "aws_ranger_audit_role_exists_validation",
        "aws_ranger_audit_role_dynamoDB_table_exist_validation",
    ],
)
def aws_ranger_audit_dynamoDB_table_needed_actions_validation(
    dynamodb_table_needed_actions: List[str], iam_client: IAMClient
) -> None:
    """Ranger audit role has the needed actions for the DynamoDB table."""  # noqa: D401, E501
    try:
        simulate_policy(
            iam_client,
            ranger_audit_data["role_arn"],
            [ranger_audit_data["dynamodb_table_arn"]],
            dynamodb_table_needed_actions,
            f"""The role ({ranger_audit_data["ranger_audit_role"]}) requires the
            following actions for the DynamoDB table
            ({ranger_audit_data["dynamodb_table_arn"]}) : \n {{}}""",
        )
    except KeyError as e:
        pytest.fail(f"Validation error - missing required data : {e.args[0]}", False)
