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
# Source File Name:  validate_aws_ssh_key.py
###

"""Validation of AWS SSH Key."""
from typing import Any, Dict, List

import pytest
from boto3_type_annotations.iam import Client as EC2Client

from cdpctl.validation import get_config_value
from cdpctl.validation.aws_utils import get_client

subnets_data = {}


@pytest.fixture(autouse=True, name="ec2_client")
def iam_client_fixture(config: Dict[str, Any]) -> EC2Client:
    """Return an AWS EC2 Client."""
    return get_client("ec2", config)


@pytest.mark.aws
@pytest.mark.infra
def aws_ssh_key_validation(
    config: Dict[str, Any],
    ec2_client: EC2Client,
) -> None:
    """SSH key exist."""  # noqa: D401,E501
    try:
        ssh_key_id: List[str] = get_config_value(
            config,
            "globals:ssh:public_key_id",
            key_missing_message="No ssh key is defined for config option: {0}",
            data_expected_error_message="No ssh key were provided for config option: {0}",  # noqa: E501
        )

        key_pairs = ec2_client.describe_key_pairs(KeyPairIds=[ssh_key_id])["KeyPairs"]
        if not key_pairs:
            pytest.fail(f"SSH key id ({ssh_key_id}) do not exist.", False)
    except KeyError as e:
        pytest.fail(f"Validation error - missing required data : {e.args[0]}", False)
    except ec2_client.exceptions.ClientError as ce:
        pytest.fail(f"Validation error - invalid ssh key id : {ce.args[0]}", False)
