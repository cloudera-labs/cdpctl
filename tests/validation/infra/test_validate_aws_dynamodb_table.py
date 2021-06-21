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
# Source File Name:  test_validate_aws_dynamodb_table.py
###
"""Test of dynamodb table location validation."""
from typing import Any, Dict

import pytest

from boto3_type_annotations.dynamodb import Client as DynamoDBClient
from botocore.stub import Stubber
from cdpctl.validation.infra.validate_aws_dynamodb_table import (
    aws_dynamodb_table_exists,
)
from cdpctl.validation.aws_utils import get_client
from tests.validation import expect_validation_failure, expect_validation_success


@pytest.fixture(autouse=True, name="dynamodb_client")
def dynamodb_client_fixture() -> DynamoDBClient:
    config: Dict[str, Any] = {"infra": {"aws": {"region": "us-west-2", "profile": ""}}}
    return get_client("dynamodb", config)


# type: ignore[misc]
def test_aws_dynamodb_table_exists(dynamodb_client: DynamoDBClient) -> None:
    """Test the validation that checks whether the DynamoDB table exists."""
    config: Dict[str, Any] = {"infra": {"aws": {"dynamodb": {"table_name": "test-db"}}}}
    stubber = Stubber(dynamodb_client)
    stubber.add_response(
        "describe_table",
        {
            "Table": {
                "TableId": "1234-adbcd",
                "TableName": "test-db",
                "TableSizeBytes": 999502,
                "TableStatus": "ACTIVE",
            }
        },
        expected_params={"TableName": "test-db"},
    )
    stubber.activate()
    func = expect_validation_success(aws_dynamodb_table_exists)
    func(config, dynamodb_client)


# type: ignore[misc]
def test_aws_dynamodb_table_missing(dynamodb_client: DynamoDBClient) -> None:
    """Test the validation that errors out when the DynamoDB table is missing."""
    config: Dict[str, Any] = {
        "infra": {"aws": {"dynamodb": {"table_name": "test-table"}}}
    }
    stubber = Stubber(dynamodb_client)
    stubber.add_client_error(
        "describe_table",
        service_error_code="ResourceNotFoundException",
        service_message="Table Not Found",
        http_status_code=404,
        expected_params={"TableName": "test-table"},
    )
    stubber.activate()
    func = expect_validation_failure(aws_dynamodb_table_exists)
    func(config, dynamodb_client)
