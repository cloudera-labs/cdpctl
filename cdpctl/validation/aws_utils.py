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
# Source File Name:  aws_utils.py
###
"""AWS Specific Utils."""
import re
from typing import Dict, List, Optional

import boto3
from boto3_type_annotations.iam import Client as IAMClient
from botocore.exceptions import ClientError, ProfileNotFound

from cdpctl.validation import UnrecoverableValidationError, fail, get_config_value
from cdpctl.validation.issues import (
    AWS_INSTANCE_PROFILE_NOT_FOUND,
    AWS_MISSING_ACTIONS,
    AWS_PROFILE_CONFIG_NOT_DEFINED,
    AWS_PROFILE_NOT_DEFINED,
    AWS_REGION_CONFIG_NOT_DEFINED,
    AWS_REGION_NOT_DEFINED,
    AWS_ROLE_MISSING,
)


def get_client(client_type: str, config):
    """
    Get an AWS client for the specified type.

    If a profile is defined, it will create a client using it.
    Otherwise, it will create a client using the specified region.
    If neither are defined, it will throw an exception.
    """
    profile_name: Optional[str] = get_config_value(
        config,
        "infra:aws:profile",
        key_value_expected=False,
        key_not_found_issue=AWS_PROFILE_CONFIG_NOT_DEFINED,
        data_expected_issue=AWS_PROFILE_NOT_DEFINED,
    )
    region_name: Optional[str] = get_config_value(
        config,
        "infra:aws:region",
        key_value_expected=False,
        key_not_found_issue=AWS_REGION_CONFIG_NOT_DEFINED,
        data_expected_issue=AWS_REGION_NOT_DEFINED,
    )

    if region_name:
        if profile_name:
            session = boto3.session.Session(profile_name=profile_name)
            return session.client(client_type, region_name=region_name)
        return boto3.client(client_type, region_name=region_name)
    raise UnrecoverableValidationError(
        "No AWS region name has been defined for the config option infra:aws:region."
    )


def parse_arn(arn: str) -> Dict[str, str]:
    """Parse an AWS ARN to dict of components."""
    # http://docs.aws.amazon.com/general/latest/gr/aws-arns-and-namespaces.html
    elements = arn.split(":", 5)
    result: Dict[str, str] = {
        "arn": elements[0],
        "partition": elements[1],
        "service": elements[2],
        "region": elements[3],
        "account": elements[4],
        "resource": elements[5],
        "resource_type": "",
    }
    if "/" in result["resource"]:
        result["resource_type"], result["resource"] = result["resource"].split("/", 1)
    elif ":" in result["resource"]:
        result["resource_type"], result["resource"] = result["resource"].split(":", 1)
    else:
        result["resource_type"], result["resource"] = (
            result["resource"],
            result["resource"],
        )
    return result


def validate_aws_config(config):
    """Validate that the nessesary AWS configs are set."""
    try:
        get_client("ec2", config)
    except ProfileNotFound as pnf:
        raise UnrecoverableValidationError(pnf) from pnf


def convert_s3a_to_arn(s3a_url: str) -> str:
    """Convert a S3A url to a AWS ARN format."""
    return f"arn:aws:s3:::{s3a_url.replace('s3a://', '')}"


def is_valid_s3a_url(s3a_url: str) -> bool:
    """Validate an S3A URL."""
    return bool(re.match("^s3a://([^/]+).*", s3a_url))


def simulate_policy(
    iam_client: IAMClient,
    policy_source_arn: str,
    resource_arns: List[str],
    needed_actions: List[str],
    subjects: List[str] = None,
    missing_actions_issue: str = AWS_MISSING_ACTIONS,
) -> None:
    """
    Simulate a list of actions against a resource.

    If any of these actions are not allowed, fail using the message specified
    in missing_actions_message. The first string-formatted argument is the
    list of actions that were missing from the required list.
    """
    response = iam_client.simulate_principal_policy(
        PolicySourceArn=policy_source_arn,
        ActionNames=needed_actions,
        ResourceArns=resource_arns,
    )

    missing_actions = [
        action["EvalActionName"]
        for action in response["EvaluationResults"]
        if action["EvalDecision"] != "allowed"
    ]

    if len(missing_actions) > 0:
        fail(
            template=missing_actions_issue, subjects=subjects, resources=missing_actions
        )


def get_instance_profile(iam_client: IAMClient, name: str) -> Dict:
    """Get the instance profile form AWS configs."""
    try:
        instance_profile = iam_client.get_instance_profile(InstanceProfileName=name)
    except iam_client.exceptions.NoSuchEntityException:
        fail(AWS_INSTANCE_PROFILE_NOT_FOUND, name)
    except iam_client.exceptions.ServiceFailureException as e:
        raise Exception(
            "Unable to retrieve role information due to a service failure"
        ) from e

    return instance_profile


def get_role(
    iam_client: IAMClient,
    role_name: str,
    missing_issue: str = AWS_ROLE_MISSING,
    service_failure_message: str = "Unable to retrieve role information due to a \
        service failure",
) -> Dict:
    """Retrieve role details by name. Fail with a message if the role does not exist."""

    role: Dict
    try:
        role = iam_client.get_role(RoleName=role_name)
    except iam_client.exceptions.NoSuchEntityException:
        fail(template=missing_issue, resources=[role_name])
    except iam_client.exceptions.ServiceFailureException as e:
        raise UnrecoverableValidationError(service_failure_message) from e
    # handling stub client error
    except ClientError as ce:
        fail(missing_issue, ce.args[0])

    return role
