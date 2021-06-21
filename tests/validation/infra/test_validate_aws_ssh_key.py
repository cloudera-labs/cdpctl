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
# Source File Name:  test_validate_aws_ssh_key.py
###

"""Test of AWS SSH key validation."""
from cdpctl.validation.infra.validate_aws_ssh_key import aws_ssh_key_validation
from typing import Any, Dict

import pytest

from botocore.stub import Stubber
from tests.validation import expect_validation_success, expect_validation_failure
from cdpctl.validation.aws_utils import get_client
from boto3_type_annotations.iam import Client as EC2Client


@pytest.fixture(autouse=True, name="ec2_client")
def iam_client_fixture() -> EC2Client:
    config: Dict[str, Any] = {"infra": {"aws": {"region": "us-west-2", "profile": ""}}}
    return get_client("ec2", config)


def test_aws_ssh_key_validation_success(
    ec2_client: EC2Client,
) -> None:
    """Unit test aws ssh key validation success."""
    config: Dict[str, Any] = {"globals": {"ssh": {"public_key_id": "test123"}}}
    stubber = Stubber(ec2_client)
    stubber = Stubber(ec2_client)
    stubber.add_response(
        "describe_key_pairs",
        {"KeyPairs": [{"KeyPairId": "test123"}]},
        expected_params={"KeyPairIds": ["test123"]},
    )
    with stubber:
        func = expect_validation_success(aws_ssh_key_validation)
        func(config, ec2_client)


def test_aws_ssh_key_validation_failure(
    ec2_client: EC2Client,
) -> None:
    """Unit test aws ssh key validation failure scenario."""
    config: Dict[str, Any] = {"globals": {"ssh": {"public_key_id": "test123"}}}
    stubber = Stubber(ec2_client)
    stubber.add_response(
        "describe_key_pairs",
        {"KeyPairs": []},
        expected_params={"KeyPairIds": ["test123"]},
    )
    with stubber:
        func = expect_validation_failure(aws_ssh_key_validation)
        func(config, ec2_client)
