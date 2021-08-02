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
# Source File Name:  validate_aws_cross_account_role.py
###
"""Validation of AWS IAM Cross Account Role."""
from typing import Any, Dict, List

import pytest
from boto3_type_annotations.iam import Client as IAMClient

from cdpctl.validation import get_config_value
from cdpctl.validation.aws_utils import get_client, get_role, simulate_policy

cross_account_role_data = {}


@pytest.fixture(autouse=True, name="iam_client")
def iam_client_fixture(config: Dict[str, Any]) -> IAMClient:
    """Returns the IAMClient."""  # noqa: D401
    return get_client("iam", config)


@pytest.mark.aws
@pytest.mark.infra
def aws_cross_account_role_exists_validation(
    config: Dict[str, Any],
    iam_client: IAMClient,
) -> None:  # pragma: no cover
    """Cross Account role exists."""  # noqa: D401
    cross_account_role: str = get_config_value(
        config,
        "env:aws:role:name:cross_account",
        key_missing_message="No role defined for config option: {0}",
        data_expected_error_message="No role was provided for config option: {0}",
    )

    role = get_role(iam_client, cross_account_role)
    role_arn = role["Role"]["Arn"]
    cross_account_role_data["role_arn"] = role_arn
    cross_account_role_data["cross_account_role"] = cross_account_role
    cross_account_role_data["role"] = role


@pytest.mark.aws
@pytest.mark.infra
@pytest.mark.dependency(depends=["aws_cross_account_role_exists_validation"])
def aws_cross_account_role_account_id_validation(
    config: Dict[str, Any]
) -> None:  # pragma: no cover
    """Cross Account role has an associated Account Id."""  # noqa: D401,E501
    account_id: str = get_config_value(
        config,
        "env:cdp:cross_account:account_id",
        key_missing_message="No account id defined for config option: {0}",
        data_expected_error_message="No account id was provided for config option: {0}",
    )
    found_account_id = False
    for s in cross_account_role_data["role"]["Role"]["AssumeRolePolicyDocument"][
        "Statement"
    ]:
        if "Principal" in s.keys():
            if "AWS" in s["Principal"].keys():
                for arn in s["Principal"]["AWS"]:
                    if str(account_id) in arn.split(":"):
                        found_account_id = True

    if not found_account_id:
        pytest.fail("Account id not in cross account role", False)


@pytest.mark.aws
@pytest.mark.infra
@pytest.mark.dependency(depends=["aws_cross_account_role_exists_validation"])
def aws_cross_account_role_external_id_validation(
    config: Dict[str, Any]
) -> None:  # pragma: no cover
    """Cross Account role has an associated External Id."""  # noqa: D401,E501
    external_id: str = get_config_value(
        config,
        "env:cdp:cross_account:external_id",
        key_missing_message="No external id defined for config option: {0}",
        data_expected_error_message="No external was provided for config option: {0}",
    )
    for s in cross_account_role_data["role"]["Role"]["AssumeRolePolicyDocument"][
        "Statement"
    ]:
        if "Condition" in s.keys():
            if s["Condition"]["StringEquals"]["sts:ExternalId"]:
                if external_id not in s["Condition"]["StringEquals"]["sts:ExternalId"]:
                    pytest.fail("External id not in cross account role", False)


@pytest.mark.aws
@pytest.mark.infra
@pytest.mark.dependency(depends=["aws_cross_account_role_exists_validation"])
def aws_cross_account_role_ec2_needed_actions_validation(
    ec2_needed_actions: List[str],
    iam_client: IAMClient,
) -> None:
    """Cross Account role has the needed actions for EC2."""  # noqa: D401
    try:
        simulate_policy(
            iam_client,
            cross_account_role_data["role_arn"],
            ["*"],
            ec2_needed_actions,
            f"""The role ({0}) requires the following actions for all ec2
            resources ([*]) : \n {{}}""".format(
                cross_account_role_data["cross_account_role"]
            ),
        )
    except KeyError as e:
        pytest.fail(f"Validation error - missing required data : {e.args[0]}", False)


@pytest.mark.aws
@pytest.mark.infra
@pytest.mark.dependency(depends=["aws_cross_account_role_exists_validation"])
def aws_cross_account_role_autoscaling_resources_needed_actions_validation(
    autoscaling_resources_needed_actions: List[str],
    iam_client: IAMClient,
) -> None:
    """Cross Account role has the needed actions for autoscaling resources."""  # noqa: D401,E501
    try:
        simulate_policy(
            iam_client,
            cross_account_role_data["role_arn"],
            ["*"],
            autoscaling_resources_needed_actions,
            f"""The role ({0}) requires the following actions for all resources
            ([*]) : \n {{}}""".format(
                cross_account_role_data["cross_account_role"]
            ),
        )
    except KeyError as e:
        pytest.fail(f"Validation error - missing required data : {e.args[0]}", False)


@pytest.mark.aws
@pytest.mark.infra
@pytest.mark.dependency(depends=["aws_cross_account_role_exists_validation"])
def aws_cross_account_role_cloud_formation_needed_actions_validation(
    cloud_formation_needed_actions: List[str],
    iam_client: IAMClient,
) -> None:
    """Cross Account role has the needed actions for CloudFormation."""  # noqa: D401,E501
    try:
        simulate_policy(
            iam_client,
            cross_account_role_data["role_arn"],
            ["*"],
            cloud_formation_needed_actions,
            f"""The role ({0}) requires the following actions for all resources
            ([*]) : \n {{}}""".format(
                cross_account_role_data["cross_account_role"]
            ),
        )
    except KeyError as e:
        pytest.fail(f"Validation error - missing required data : {e.args[0]}", False)


@pytest.mark.aws
@pytest.mark.infra
@pytest.mark.dependency(depends=["aws_cross_account_role_exists_validation"])
def aws_cross_account_role_cdp_environment_resources_needed_actions_validation(
    cdp_environment_resources_needed_actions: List[str],
    iam_client: IAMClient,
) -> None:
    """Cross Account role has the needed actions for CDP environment resources."""  # noqa: D401,E501
    try:
        simulate_policy(
            iam_client,
            cross_account_role_data["role_arn"],
            ["*"],
            cdp_environment_resources_needed_actions,
            f"""The role ({0}) requires the following actions for all resources
            ([*]) : \n {{}}""".format(
                cross_account_role_data["cross_account_role"]
            ),
        )
    except KeyError as e:
        pytest.fail(f"Validation error - missing required data : {e.args[0]}", False)


@pytest.mark.aws
@pytest.mark.infra
@pytest.mark.dependency(depends=["aws_cross_account_role_exists_validation"])
def aws_cross_account_role_pass_role_needed_actions_validation(
    pass_role_needed_actions: List[str],
    iam_client: IAMClient,
) -> None:
    """Cross Account role has the needed actions for the pass role."""  # noqa: D401,E501
    try:
        simulate_policy(
            iam_client,
            cross_account_role_data["role_arn"],
            ["*"],
            pass_role_needed_actions,
            f"""The role ({0}) requires the following actions for all resources
            ([*]) : \n {{}}""".format(
                cross_account_role_data["cross_account_role"]
            ),
        )
    except KeyError as e:
        pytest.fail(f"Validation error - missing required data : {e.args[0]}", False)


@pytest.mark.aws
@pytest.mark.infra
@pytest.mark.dependency(depends=["aws_cross_account_role_exists_validation"])
def aws_cross_account_identity_management_needed_actions_validation(
    identity_management_needed_actions: List[str],
    iam_client: IAMClient,
) -> None:
    """Cross Account role has the needed actions for identity management."""  # noqa: D401,E501
    try:
        simulate_policy(
            iam_client,
            cross_account_role_data["role_arn"],
            ["arn:aws:iam::*:role/aws-service-role/*"],
            identity_management_needed_actions,
            f"""The role ({0}) requires the following actions for all resources
            ("arn:aws:iam::*:role/aws-service-role/*") : \n {{}}""".format(
                cross_account_role_data["cross_account_role"]
            ),
        )
    except KeyError as e:
        pytest.fail(f"Validation error - missing required data : {e.args[0]}", False)
