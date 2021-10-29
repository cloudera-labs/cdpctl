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
# Source File Name:  test_validate_aws_ranger_audit_role.py
###
"""Test of AWS Ranger Audit role validation."""
from typing import Any, Dict, List

import pytest
from boto3_type_annotations.iam import Client as IAMClient
from botocore.stub import Stubber

from cdpctl.validation.aws_utils import get_client
from cdpctl.validation.infra.validate_aws_ranger_audit_role import (
    aws_ranger_audit_backup_location_needed_actions_validation,
    aws_ranger_audit_cdp_s3_needed_actions_validation,
    aws_ranger_audit_data_location_needed_actions_validation,
    aws_ranger_audit_location_needed_actions_validation,
    aws_ranger_audit_role_exists_validation,
    aws_ranger_audit_s3_bucket_needed_actions_validation,
    ranger_audit_data,
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


def test_aws_ranger_audit_role_exists_validation_success(
    iam_client: IAMClient,
) -> None:
    """Unit test Ranger role validation success."""
    config: Dict[str, Any] = {
        "env": {
            "aws": {
                "role": {
                    "name": {"ranger_audit": "arn:aws:iam::1234:role/ranger_audit_role"}
                }
            }
        }
    }
    stubber = Stubber(iam_client)
    add_get_role_response(
        stubber=stubber,
        role_arn="arn:aws:iam::1234:role/ranger_audit_role",
        includeTrustPolicy=True,
    )
    with stubber:
        func = expect_validation_success(aws_ranger_audit_role_exists_validation)
        func(config, iam_client)


def test_aws_ranger_audit_role_exists_validation_failure(
    iam_client: IAMClient,
) -> None:
    """Unit test Ranger role validation failure scenario."""
    config: Dict[str, Any] = {
        "env": {
            "aws": {
                "role": {
                    "name": {"ranger_audit": "arn:aws:iam::1F:role/ranger_audit_role"}
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
        func = expect_validation_failure(
            aws_ranger_audit_location_needed_actions_validation
        )
        func(config, iam_client)


def test_aws_ranger_audit_location_needed_actions_validation_success(
    ranger_audit_location_needed_actions: List[str],
    iam_client: IAMClient,
) -> None:
    """Unit test Ranger role audit location needed actions validation success."""
    ranger_audit_data["role_arn"] = "arn:aws:iam::1234:role/ranger_audit_role"
    ranger_audit_data["ranger_audit_location_arn"] = "arn:aws:s3:::test-new-bucket"
    stubber = Stubber(iam_client)

    add_simulate_policy_response(
        stubber=stubber,
        role_arn=ranger_audit_data["role_arn"],
        resource_arns=[ranger_audit_data["ranger_audit_location_arn"] + "/*"],
        actions=ranger_audit_location_needed_actions,
        failSimulatePolicy=False,
    )
    with stubber:
        func = expect_validation_success(
            aws_ranger_audit_location_needed_actions_validation
        )
        func(ranger_audit_location_needed_actions, iam_client)


def test_aws_ranger_audit_location_needed_actions_validation_failure(
    ranger_audit_location_needed_actions: List[str],
    iam_client: IAMClient,
) -> None:
    """Unit test Ranger role audit location needed actions validation failure."""
    ranger_audit_data["role_arn"] = "arn:aws:iam::1234:role/ranger_audit_role"
    ranger_audit_data["ranger_audit_location_arn"] = "arn:aws:s3:::test-new-bucket"
    stubber = Stubber(iam_client)

    add_simulate_policy_response(
        stubber=stubber,
        role_arn=ranger_audit_data["role_arn"],
        resource_arns=[ranger_audit_data["ranger_audit_location_arn"] + "/*"],
        actions=ranger_audit_location_needed_actions,
        failSimulatePolicy=True,
    )
    with stubber:
        func = expect_validation_failure(
            aws_ranger_audit_location_needed_actions_validation
        )
        func(ranger_audit_location_needed_actions, iam_client)


def test_aws_ranger_audit_s3_bucket_needed_actions_validation_success(
    ranger_audit_bucket_needed_actions: List[str],
    iam_client: IAMClient,
) -> None:
    """Unit test Ranger role audit s3 bucket needed actions validation success."""
    ranger_audit_data["role_arn"] = "arn:aws:iam::1234:role/ranger_audit_role"
    ranger_audit_data["ranger_audit_bucket_arn"] = "arn:aws:s3:::test-new-bucket"

    stubber = Stubber(iam_client)

    add_simulate_policy_response(
        stubber=stubber,
        role_arn=ranger_audit_data["role_arn"],
        resource_arns=[ranger_audit_data["ranger_audit_bucket_arn"]],
        actions=ranger_audit_bucket_needed_actions,
        failSimulatePolicy=False,
    )
    with stubber:
        func = expect_validation_success(
            aws_ranger_audit_s3_bucket_needed_actions_validation
        )
        func(ranger_audit_bucket_needed_actions, iam_client)


def test_aws_ranger_audit_s3_bucket_needed_actions_validation_failure(
    ranger_audit_bucket_needed_actions: List[str],
    iam_client: IAMClient,
) -> None:
    """Unit test Ranger role audit s3 bucket needed actions validation failure."""
    ranger_audit_data["role_arn"] = "arn:aws:iam::1234:role/ranger_audit_role"
    ranger_audit_data["ranger_audit_bucket_arn"] = "arn:aws:s3:::test-new-bucket"

    stubber = Stubber(iam_client)

    add_simulate_policy_response(
        stubber=stubber,
        role_arn=ranger_audit_data["role_arn"],
        resource_arns=[ranger_audit_data["ranger_audit_bucket_arn"]],
        actions=ranger_audit_bucket_needed_actions,
        failSimulatePolicy=True,
    )
    with stubber:
        func = expect_validation_failure(
            aws_ranger_audit_s3_bucket_needed_actions_validation
        )
        func(ranger_audit_bucket_needed_actions, iam_client)


def test_aws_ranger_audit_cdp_s3_needed_actions_validation_success(
    s3_needed_actions_to_all: List[str],
    iam_client: IAMClient,
) -> None:
    """Unit test Ranger role audit cdp s3 needed actions validation success."""
    ranger_audit_data["role_arn"] = "arn:aws:iam::1234:role/ranger_audit_role"

    stubber = Stubber(iam_client)

    add_simulate_policy_response(
        stubber=stubber,
        role_arn=ranger_audit_data["role_arn"],
        resource_arns=["*"],
        actions=s3_needed_actions_to_all,
        failSimulatePolicy=False,
    )
    with stubber:
        func = expect_validation_success(
            aws_ranger_audit_cdp_s3_needed_actions_validation
        )
        func(s3_needed_actions_to_all, iam_client)


def test_aws_ranger_audit_cdp_s3_needed_actions_validation_failure(
    s3_needed_actions_to_all: List[str],
    iam_client: IAMClient,
) -> None:
    """Unit test Ranger role audit cdp s3 needed actions validation failure."""
    ranger_audit_data["role_arn"] = "arn:aws:iam::1234:role/ranger_audit_role"

    stubber = Stubber(iam_client)

    add_simulate_policy_response(
        stubber=stubber,
        role_arn=ranger_audit_data["role_arn"],
        resource_arns=["*"],
        actions=s3_needed_actions_to_all,
        failSimulatePolicy=True,
    )
    with stubber:
        func = expect_validation_failure(
            aws_ranger_audit_cdp_s3_needed_actions_validation
        )
        func(s3_needed_actions_to_all, iam_client)


def test_aws_ranger_audit_data_location_needed_actions_validation_success(
    data_location_needed_actions: List[str],
    iam_client: IAMClient,
) -> None:
    """Unit test Ranger role audit data location needed actions validation success."""
    ranger_audit_data["role_arn"] = "arn:aws:iam::1234:role/ranger_audit_role"
    ranger_audit_data["data_location_arn"] = "arn:aws:s3:::data-new-bucket'"

    stubber = Stubber(iam_client)

    add_simulate_policy_response(
        stubber=stubber,
        role_arn=ranger_audit_data["role_arn"],
        resource_arns=[
            ranger_audit_data["data_location_arn"],
            ranger_audit_data["data_location_arn"] + "/*",
        ],
        actions=data_location_needed_actions,
        failSimulatePolicy=False,
    )
    with stubber:
        func = expect_validation_success(
            aws_ranger_audit_data_location_needed_actions_validation
        )
        func(data_location_needed_actions, iam_client)


def test_aws_ranger_audit_data_location_needed_actions_validation_failure(
    data_location_needed_actions: List[str],
    iam_client: IAMClient,
) -> None:
    """Unit test Ranger role audit data location needed actions validation failure."""
    ranger_audit_data["role_arn"] = "arn:aws:iam::1234:role/ranger_audit_role"
    ranger_audit_data["data_location_arn"] = "arn:aws:s3:::data-new-bucket'"

    stubber = Stubber(iam_client)

    add_simulate_policy_response(
        stubber=stubber,
        role_arn=ranger_audit_data["role_arn"],
        resource_arns=[
            ranger_audit_data["data_location_arn"],
            ranger_audit_data["data_location_arn"] + "/*",
        ],
        actions=data_location_needed_actions,
        failSimulatePolicy=True,
    )
    with stubber:
        func = expect_validation_failure(
            aws_ranger_audit_data_location_needed_actions_validation
        )
        func(data_location_needed_actions, iam_client)


def test_aws_ranger_audit_backup_location_needed_actions_validation_success(
    data_location_needed_actions: List[str],
    iam_client: IAMClient,
) -> None:
    """Unit test Ranger role audit data location needed actions validation success."""
    ranger_audit_data["role_arn"] = "arn:aws:iam::1234:role/ranger_audit_role"
    ranger_audit_data["backup_location_arn"] = "arn:aws:s3:::backup-new-bucket'"

    stubber = Stubber(iam_client)

    add_simulate_policy_response(
        stubber=stubber,
        role_arn=ranger_audit_data["role_arn"],
        resource_arns=[
            ranger_audit_data["backup_location_arn"],
            ranger_audit_data["backup_location_arn"] + "/*",
        ],
        actions=data_location_needed_actions,
        failSimulatePolicy=False,
    )
    with stubber:
        func = expect_validation_success(
            aws_ranger_audit_backup_location_needed_actions_validation
        )
        func(data_location_needed_actions, iam_client)


def test_aws_ranger_audit_backup_location_needed_actions_validation_failure(
    data_location_needed_actions: List[str],
    iam_client: IAMClient,
) -> None:
    """Unit test Ranger role audit data location needed actions validation failure."""
    ranger_audit_data["role_arn"] = "arn:aws:iam::1234:role/ranger_audit_role"
    ranger_audit_data["backup_location_arn"] = "arn:aws:s3:::backup-new-bucket'"

    stubber = Stubber(iam_client)

    add_simulate_policy_response(
        stubber=stubber,
        role_arn=ranger_audit_data["role_arn"],
        resource_arns=[
            ranger_audit_data["backup_location_arn"],
            ranger_audit_data["backup_location_arn"] + "/*",
        ],
        actions=data_location_needed_actions,
        failSimulatePolicy=True,
    )
    with stubber:
        func = expect_validation_failure(
            aws_ranger_audit_backup_location_needed_actions_validation
        )
        func(data_location_needed_actions, iam_client)
