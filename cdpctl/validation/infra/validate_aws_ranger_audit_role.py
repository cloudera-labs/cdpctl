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
# Source File Name:  validate_aws_ranger_audit_role.py
###
"""Validation of AWS IAM Ranger Audit Role."""
from typing import Any, Dict, List

import pytest
from boto3_type_annotations.iam import Client as IAMClient

from cdpctl.validation import fail, get_config_value
from cdpctl.validation.aws_utils import (
    convert_s3a_to_arn,
    get_client,
    get_role,
    parse_arn,
    simulate_policy,
)
from cdpctl.validation.infra.issues import (
    AWS_REQUIRED_DATA_MISSING,
    AWS_ROLE_FOR_DATA_BUCKET_MISSING_ACTIONS,
    AWS_ROLE_FOR_DL_BUCKET_MISSING_ACTIONS,
    AWS_ROLE_REQUIRES_ACTIONS_FOR_ALL_S3_RESOURCES,
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
    )

    # ranger audit role arn
    role = get_role(iam_client, ranger_audit_role)
    role_arn = role["Role"]["Arn"]
    ranger_audit_data["role_arn"] = role_arn
    ranger_audit_data["ranger_audit_role"] = ranger_audit_role


@pytest.mark.aws
@pytest.mark.infra
def aws_ranger_audit_role_data_location_exist_validation(
    config: Dict[str, Any]
) -> None:  # pragma: no cover
    """Ranger data location exists."""  # noqa: D401
    data_location: str = get_config_value(
        config,
        "infra:aws:vpc:existing:storage:data",
    )
    # data access s3 bucket arn
    data_location_arn = convert_s3a_to_arn(data_location)

    ranger_audit_data["data_location"] = data_location
    ranger_audit_data["data_location_arn"] = data_location_arn


@pytest.mark.aws
@pytest.mark.infra
def aws_ranger_audit_role_backup_location_exist_validation(
    config: Dict[str, Any]
) -> None:  # pragma: no cover
    """Ranger backup location exists."""  # noqa: D401
    backup_location: str = get_config_value(
        config,
        "infra:aws:vpc:existing:storage:backup",
    )
    # data access s3 bucket arn
    backup_location_arn = convert_s3a_to_arn(backup_location)

    ranger_audit_data["backup_location"] = backup_location
    ranger_audit_data["backup_location_arn"] = backup_location_arn


@pytest.mark.aws
@pytest.mark.infra
def aws_ranger_audit_role_audit_location_exist_validation(
    config: Dict[str, Any]
) -> None:  # pragma: no cover
    """Ranger audit location exist."""  # noqa: D401
    ranger_audit_location: str = get_config_value(
        config,
        "infra:aws:vpc:existing:storage:ranger_audit",
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
@pytest.mark.dependency(depends=["aws_ranger_audit_role_exists_validation"])
def aws_ranger_audit_location_needed_actions_validation(
    ranger_audit_location_needed_actions: List[str], iam_client: IAMClient
) -> None:
    """Ranger audit role has needed actions for the audit location."""  # noqa: D401
    try:
        # aws-cdp-ranger-audit-s3-policy
        simulate_policy(
            iam_client=iam_client,
            policy_source_arn=ranger_audit_data["role_arn"],
            resource_arns=[ranger_audit_data["ranger_audit_location_arn"] + "/*"],
            needed_actions=ranger_audit_location_needed_actions,
            subjects=[
                ranger_audit_data["ranger_audit_role"],
                ranger_audit_data["ranger_audit_location_arn"] + "/*",
            ],
            missing_actions_issue=AWS_ROLE_FOR_DL_BUCKET_MISSING_ACTIONS,
        )
    except KeyError as e:
        fail(AWS_REQUIRED_DATA_MISSING, e.args[0])


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
            iam_client=iam_client,
            policy_source_arn=ranger_audit_data["role_arn"],
            resource_arns=[ranger_audit_data["ranger_audit_bucket_arn"]],
            needed_actions=ranger_audit_bucket_needed_actions,
            subjects=[
                ranger_audit_data["ranger_audit_role"],
                ranger_audit_data["ranger_audit_bucket_arn"],
            ],
            missing_actions_issue=AWS_ROLE_FOR_DL_BUCKET_MISSING_ACTIONS,
        )
    except KeyError as e:
        fail(AWS_REQUIRED_DATA_MISSING, e.args[0])


@pytest.mark.aws
@pytest.mark.infra
@pytest.mark.dependency(depends=["aws_ranger_audit_role_exists_validation"])
def aws_ranger_audit_cdp_s3_needed_actions_validation(
    s3_needed_actions_to_all: List[str], iam_client: IAMClient
) -> None:
    """Ranger audit role has the needed actions for CDP S3."""  # noqa: D401
    try:
        # aws-cdp-bucket-access-policy
        simulate_policy(
            iam_client=iam_client,
            policy_source_arn=ranger_audit_data["role_arn"],
            resource_arns=["*"],
            needed_actions=s3_needed_actions_to_all,
            subjects=[ranger_audit_data["ranger_audit_role"]],
            missing_actions_issue=AWS_ROLE_REQUIRES_ACTIONS_FOR_ALL_S3_RESOURCES,
        )
    except KeyError as e:
        fail(AWS_REQUIRED_DATA_MISSING, e.args[0])


@pytest.mark.aws
@pytest.mark.infra
@pytest.mark.dependency(depends=["aws_ranger_audit_role_exists_validation"])
def aws_ranger_audit_data_location_needed_actions_validation(
    data_location_needed_actions: List[str], iam_client: IAMClient
) -> None:
    """Ranger audit role has needed actions for the data location."""  # noqa: D401
    try:
        simulate_policy(
            iam_client=iam_client,
            policy_source_arn=ranger_audit_data["role_arn"],
            resource_arns=[
                ranger_audit_data["data_location_arn"],
                ranger_audit_data["data_location_arn"] + "/*",
            ],
            needed_actions=data_location_needed_actions,
            subjects=[
                ranger_audit_data["ranger_audit_role"],
                ranger_audit_data["data_location_arn"] + "/*",
            ],
            missing_actions_issue=AWS_ROLE_FOR_DATA_BUCKET_MISSING_ACTIONS,
        )
    except KeyError as e:
        fail(AWS_REQUIRED_DATA_MISSING, e.args[0])


@pytest.mark.aws
@pytest.mark.infra
@pytest.mark.dependency(
    depends=[
        "aws_ranger_audit_role_exists_validation",
        "aws_ranger_audit_role_backup_location_exist_validation",
    ]
)
def aws_ranger_audit_backup_location_needed_actions_validation(
    data_location_needed_actions: List[str], iam_client: IAMClient
) -> None:
    """Ranger audit role has needed actions for the data location."""  # noqa: D401
    try:
        simulate_policy(
            iam_client=iam_client,
            policy_source_arn=ranger_audit_data["role_arn"],
            resource_arns=[
                ranger_audit_data["backup_location_arn"],
                ranger_audit_data["backup_location_arn"] + "/*",
            ],
            needed_actions=data_location_needed_actions,
            subjects=[
                ranger_audit_data["ranger_audit_role"],
                ranger_audit_data["backup_location_arn"] + "/*",
            ],
            missing_actions_issue=AWS_ROLE_FOR_DATA_BUCKET_MISSING_ACTIONS,
        )
    except KeyError as e:
        fail(AWS_REQUIRED_DATA_MISSING, e.args[0])
