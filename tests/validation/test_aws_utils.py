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
# Source File Name:  test_aws_utils.py
###
"""Tests for the aws utilities."""
import json
from typing import Any, Dict, List

import boto3
from boto3_type_annotations.iam import Client as IAMClient
from botocore.stub import Stubber
from moto import mock_iam

from cdpctl.validation.aws_utils import get_role, is_valid_s3a_url, simulate_policy
from tests.validation import expect_validation_failure, expect_validation_success


def test_is_valid_s3a_url_with_invalid_input() -> None:
    """Test the is_valid_s3a_url function with invalid input."""
    assert not is_valid_s3a_url("")


def test_is_valid_s3a_url_with_invalid_url() -> None:
    """Test the is_valid_s3a_url function with invalid url."""
    assert not is_valid_s3a_url("s3://my-bucket/data")


def test_is_valid_s3a_url_with_valid_url() -> None:
    """Test the is_valid_s3a_url function with valid url."""
    assert is_valid_s3a_url("s3a://my-bucket/data")
    assert is_valid_s3a_url("s3a://my-bucket")


@mock_iam
def test_validation_failure_if_role_is_missing() -> None:
    """Test that the get_role function fails if the role does not exst."""
    client: IAMClient = boto3.client("iam")
    func = expect_validation_failure(get_role)
    func(client, "bad-role")


@mock_iam
def test_validation_success_if_role_exists() -> None:
    """Test that the get_role function returns the existing role."""
    role: str = "test-role"
    client: IAMClient = boto3.client("iam")
    client.create_role(
        RoleName=role,
        AssumeRolePolicyDocument=json.dumps(
            {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"Sevice": "ec2.amazonaws.com"},
                        "Action": "sts:AssumeRole",
                    }
                ],
            }
        ),
    )

    func = expect_validation_success(get_role)
    func(client, role)

    role = get_role(client, role)
    assert role


def test_simulate_policy_with_missing_action() -> None:
    """Test policy simulation with a missing action to ensure validation fails."""
    bucket_arn: str = "arn:aws:s3:::test-bucket"
    role_arn: str = "arn:aws:iam::214178861886:role/test-role"
    actions = ["GetObject", "DeleteObject"]

    iam_client: IAMClient = boto3.client("iam")
    stubber: Stubber = Stubber(iam_client)
    add_simulate_policy_response_with_evaluation_results(
        stubber,
        role_arn,
        [bucket_arn],
        actions,
        [
            {
                "EvalActionName": "GetObject",
                "EvalResourceName": "s3-resource",
                "EvalDecision": "allowed",
            },
            {
                "EvalActionName": "DeleteObject",
                "EvalResourceName": "s3-resource",
                "EvalDecision": "implicitDeny",
            },
        ],
    )

    with stubber:
        func = expect_validation_failure(simulate_policy)
        func(
            iam_client,
            role_arn,
            [bucket_arn],
            actions,
        )


def test_simulate_policy_with_all_valid_policies() -> None:
    """Test policy simulation with all required actions to ensure validation success."""
    bucket_arn: str = "arn:aws:s3:::test-bucket"
    role_arn: str = "arn:aws:iam::214178861886:role/test-role"
    actions = ["GetObject", "DeleteObject"]

    iam_client: IAMClient = boto3.client("iam")
    stubber: Stubber = Stubber(iam_client)
    add_simulate_policy_response_with_evaluation_results(
        stubber,
        role_arn,
        [bucket_arn],
        actions,
        [
            {
                "EvalActionName": "GetObject",
                "EvalResourceName": "s3-resource",
                "EvalDecision": "allowed",
            },
            {
                "EvalActionName": "DeleteObject",
                "EvalResourceName": "s3-resource",
                "EvalDecision": "allowed",
            },
        ],
    )

    with stubber:
        func = expect_validation_success(simulate_policy)
        func(
            iam_client,
            role_arn,
            [bucket_arn],
            actions,
        )


def add_simulate_policy_response_with_evaluation_results(
    stubber: Stubber,
    role_arn: str,
    resource_arns: List[str],
    actions: List[str],
    evaluation_results: List[Dict[str, Any]],
) -> None:
    """Add a simulate_policy_response response to a Stubber with custom evaluation results."""

    stubber.add_response(
        "simulate_principal_policy",
        {"EvaluationResults": evaluation_results},
        expected_params={
            "PolicySourceArn": role_arn,
            "ResourceArns": resource_arns,
            "ActionNames": actions,
        },
    )


def add_simulate_policy_response(
    stubber: Stubber,
    role_arn: str,
    resource_arns: List[str],
    actions: List[str],
    failSimulatePolicy: bool,
) -> None:
    """Add a simulate_policy_response response to a Stubber."""

    evalDecision = "allowed"
    if failSimulatePolicy:
        evalDecision = "denied"

    stubber.add_response(
        "simulate_principal_policy",
        {
            "EvaluationResults": [
                {
                    "EvalActionName": "ListBucket",
                    "EvalResourceName": "s3-resource",
                    "EvalDecision": evalDecision,
                },
            ],
        },
        expected_params={
            "PolicySourceArn": role_arn,
            "ResourceArns": resource_arns,
            "ActionNames": actions,
        },
    )


def add_get_role_response(stubber: Stubber, role_arn: str, includeTrustPolicy: bool):
    """Add a get_role response to a Stubber."""

    policy = '{"Statement": []}'
    if includeTrustPolicy:
        policy = '{"Statement": [{"Effect": "Allow", "Principal": {"Service": ["s3.amazonaws.com", "ec2.amazonaws.com"]}, "Action": "sts:AssumeRole"}]}'  # noqa: E501

    stubber.add_response(
        "get_role",
        {
            "Role": {
                "Path": "/",
                "RoleName": role_arn,
                "RoleId": "testtesttesttest",
                "CreateDate": "2016-01-01T00:00:00.000Z",
                "Arn": role_arn,
                "AssumeRolePolicyDocument": policy,
            }
        },
        expected_params={"RoleName": role_arn},
    )


def add_get_profile_response(
    stubber: Stubber, role_arn: str, includeRole: bool, includeTrustPolicy: bool
) -> None:
    """Add a get_instance_profile response to a Stubber."""

    policy = '{"Statement": []}'
    if includeTrustPolicy:
        policy = '{"Statement": [{"Effect": "Allow", "Principal": {"Service": ["s3.amazonaws.com", "ec2.amazonaws.com"]}, "Action": "sts:AssumeRole"}]}'  # noqa: E501

    roles = []
    if includeRole:
        roles.append(
            {
                "Path": "/",
                "RoleName": role_arn,
                "RoleId": "testtesttesttest",
                "CreateDate": "2016-01-01T00:00:00.000Z",
                "Arn": role_arn,
                "AssumeRolePolicyDocument": policy,
            }
        )

    stubber.add_response(
        "get_instance_profile",
        {
            "InstanceProfile": {
                "Path": "/",
                "InstanceProfileName": role_arn,
                "InstanceProfileId": "TESTTESTTESTTEST",
                "Arn": role_arn,
                "CreateDate": "2016-01-01T00:00:00.000Z",
                "Roles": roles,
            }
        },
        expected_params={"InstanceProfileName": role_arn},
    )
