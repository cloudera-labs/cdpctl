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
# Source File Name:  test_validate_aws_datalake_admin_role.py
###
"""Test of AWS IAM roles."""
from typing import Any, Dict

import pytest

from boto3_type_annotations.iam import Client as IAMClient
from tests.validation import expect_validation_failure, expect_validation_success
from cdpctl.validation.infra.validate_aws_datalake_admin_role import (
    aws_datalake_admin_role_has_bucket_access_policy,
    aws_datalake_admin_role_has_bucket_access_policy_all_resources,
    aws_datalake_admin_role_has_s3_policy,
    aws_datalake_admin_role_has_dynamodb_policy,
)
from botocore.stub import Stubber
from cdpctl.validation.aws_utils import get_client
from tests.validation.test_aws_utils import (
    add_simulate_policy_response,
    add_get_role_response,
)


@pytest.fixture(autouse=True, name="iam_client")
def iam_stubber_fixture() -> IAMClient:
    config: Dict[str, Any] = {"infra": {"aws": {"region": "us-west-2", "profile": ""}}}
    return get_client("iam", config)


def test_has_bucket_access_policy_with_missing_actions(iam_client: IAMClient) -> None:
    config: Dict[str, Any] = {
        "env": {
            "aws": {
                "role": {
                    "name": {
                        "datalake_admin": "arn:aws:iam::214178861886:role/datalake_admin_role"
                    }
                }
            }
        },
        "infra": {
            "aws": {"vpc": {"existing": {"storage": {"data": "s3a://data/location"}}}}
        },
    }

    stubber = Stubber(iam_client)

    add_get_role_response(
        stubber, "arn:aws:iam::214178861886:role/datalake_admin_role", False
    )
    add_simulate_policy_response(
        stubber,
        "arn:aws:iam::214178861886:role/datalake_admin_role",
        ["arn:aws:s3:::data", "arn:aws:s3:::data/*"],
        ["ListBucket"],
        failSimulatePolicy=True,
    )

    with stubber:
        func = expect_validation_failure(
            aws_datalake_admin_role_has_bucket_access_policy
        )
        func(config, iam_client, ["ListBucket"])


def test_has_bucket_access_policy_with_valid_actions(iam_client: IAMClient) -> None:
    config: Dict[str, Any] = {
        "env": {
            "aws": {
                "role": {
                    "name": {
                        "datalake_admin": "arn:aws:iam::214178861886:role/datalake_admin_role"
                    }
                }
            }
        },
        "infra": {
            "aws": {"vpc": {"existing": {"storage": {"data": "s3a://data/location"}}}}
        },
    }

    stubber = Stubber(iam_client)

    add_get_role_response(
        stubber, "arn:aws:iam::214178861886:role/datalake_admin_role", False
    )
    add_simulate_policy_response(
        stubber,
        "arn:aws:iam::214178861886:role/datalake_admin_role",
        ["arn:aws:s3:::data", "arn:aws:s3:::data/*"],
        ["ListBucket"],
        failSimulatePolicy=False,
    )

    with stubber:
        func = expect_validation_success(
            aws_datalake_admin_role_has_bucket_access_policy
        )
        func(config, iam_client, ["ListBucket"])


def test_has_s3_policy_with_missing_actions(iam_client: IAMClient) -> None:
    config: Dict[str, Any] = {
        "env": {
            "aws": {
                "role": {
                    "name": {
                        "datalake_admin": "arn:aws:iam::214178861886:role/datalake_admin_role"
                    }
                }
            }
        },
        "infra": {
            "aws": {"vpc": {"existing": {"storage": {"data": "s3a://data/location"}}}}
        },
    }

    stubber = Stubber(iam_client)

    add_get_role_response(
        stubber, "arn:aws:iam::214178861886:role/datalake_admin_role", False
    )
    add_simulate_policy_response(
        stubber,
        "arn:aws:iam::214178861886:role/datalake_admin_role",
        ["arn:aws:s3:::data/location", "arn:aws:s3:::data/location/*"],
        ["ListBucket"],
        failSimulatePolicy=True,
    )

    with stubber:
        func = expect_validation_failure(aws_datalake_admin_role_has_s3_policy)
        func(config, iam_client, ["ListBucket"])


def test_has_s3_policy_with_valid_actions(iam_client: IAMClient) -> None:
    config: Dict[str, Any] = {
        "env": {
            "aws": {
                "role": {
                    "name": {
                        "datalake_admin": "arn:aws:iam::214178861886:role/datalake_admin_role"
                    }
                }
            }
        },
        "infra": {
            "aws": {"vpc": {"existing": {"storage": {"data": "s3a://data/location"}}}}
        },
    }

    stubber = Stubber(iam_client)

    add_get_role_response(
        stubber, "arn:aws:iam::214178861886:role/datalake_admin_role", False
    )
    add_simulate_policy_response(
        stubber,
        "arn:aws:iam::214178861886:role/datalake_admin_role",
        ["arn:aws:s3:::data/location", "arn:aws:s3:::data/location/*"],
        ["ListBucket"],
        failSimulatePolicy=False,
    )

    with stubber:
        func = expect_validation_success(aws_datalake_admin_role_has_s3_policy)
        func(config, iam_client, ["ListBucket"])


def test_has_bucket_access_policy_all_resources_with_missing_actions(
    iam_client: IAMClient,
) -> None:
    config: Dict[str, Any] = {
        "env": {
            "aws": {
                "role": {
                    "name": {
                        "datalake_admin": "arn:aws:iam::214178861886:role/datalake_admin_role"
                    }
                }
            }
        },
        "infra": {
            "aws": {"vpc": {"existing": {"storage": {"data": "s3a://data/location"}}}}
        },
    }

    stubber = Stubber(iam_client)

    add_get_role_response(
        stubber, "arn:aws:iam::214178861886:role/datalake_admin_role", False
    )
    add_simulate_policy_response(
        stubber,
        "arn:aws:iam::214178861886:role/datalake_admin_role",
        ["*"],
        ["ListBucket"],
        failSimulatePolicy=True,
    )

    with stubber:
        func = expect_validation_failure(
            aws_datalake_admin_role_has_bucket_access_policy_all_resources
        )
        func(config, iam_client, ["ListBucket"])


def test_has_bucket_access_policy_all_resources_with_valid_actions(
    iam_client: IAMClient,
) -> None:
    config: Dict[str, Any] = {
        "env": {
            "aws": {
                "role": {
                    "name": {
                        "datalake_admin": "arn:aws:iam::214178861886:role/datalake_admin_role"
                    }
                }
            }
        },
        "infra": {
            "aws": {"vpc": {"existing": {"storage": {"data": "s3a://data/location"}}}}
        },
    }

    stubber = Stubber(iam_client)

    add_get_role_response(
        stubber, "arn:aws:iam::214178861886:role/datalake_admin_role", False
    )
    add_simulate_policy_response(
        stubber,
        "arn:aws:iam::214178861886:role/datalake_admin_role",
        ["*"],
        ["ListBucket"],
        failSimulatePolicy=False,
    )

    with stubber:
        func = expect_validation_success(
            aws_datalake_admin_role_has_bucket_access_policy_all_resources
        )
        func(config, iam_client, ["ListBucket"])


def test_has_dynamodb_policy_with_missing_actions(
    iam_client: IAMClient,
) -> None:
    config: Dict[str, Any] = {
        "env": {
            "aws": {
                "role": {
                    "name": {
                        "datalake_admin": "arn:aws:iam::214178861886:role/datalake_admin_role"
                    }
                }
            }
        },
        "infra": {"aws": {"dynamodb": {"table_name": "table_name"}}},
    }

    stubber = Stubber(iam_client)

    add_get_role_response(
        stubber, "arn:aws:iam::214178861886:role/datalake_admin_role", False
    )
    add_simulate_policy_response(
        stubber,
        "arn:aws:iam::214178861886:role/datalake_admin_role",
        ["arn:aws:dynamodb:::table/table_name"],
        ["ListBucket"],
        failSimulatePolicy=True,
    )

    with stubber:
        func = expect_validation_failure(aws_datalake_admin_role_has_dynamodb_policy)
        func(config, iam_client, ["ListBucket"])


def test_has_dynamodb_policy_with_valid_actions(
    iam_client: IAMClient,
) -> None:
    config: Dict[str, Any] = {
        "env": {
            "aws": {
                "role": {
                    "name": {
                        "datalake_admin": "arn:aws:iam::214178861886:role/datalake_admin_role"
                    }
                }
            }
        },
        "infra": {"aws": {"dynamodb": {"table_name": "table_name"}}},
    }

    stubber = Stubber(iam_client)

    add_get_role_response(
        stubber, "arn:aws:iam::214178861886:role/datalake_admin_role", False
    )
    add_simulate_policy_response(
        stubber,
        "arn:aws:iam::214178861886:role/datalake_admin_role",
        ["arn:aws:dynamodb:::table/table_name"],
        ["ListBucket"],
        failSimulatePolicy=False,
    )

    with stubber:
        func = expect_validation_success(aws_datalake_admin_role_has_dynamodb_policy)
        func(config, iam_client, ["ListBucket"])
