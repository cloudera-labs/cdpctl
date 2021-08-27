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
# Source File Name:  validate_aws_s3_locations.py
###
"""Validation of the storage locations."""
from typing import Any, Dict

import botocore
import pytest
from boto3_type_annotations.s3 import Client as S3Client

from cdpctl.validation import fail, get_config_value, validator
from cdpctl.validation.aws_utils import (
    convert_s3a_to_arn,
    get_client,
    is_valid_s3a_url,
    parse_arn,
)
from cdpctl.validation.infra.issues import (
    AWS_S3_BUCKET_DOES_NOT_EXIST,
    AWS_S3_BUCKET_FORBIDDEN_ACCESS,
    AWS_S3_BUCKET_INVALID,
    AWS_S3_BUCKET_NOT_IN_SAME_REGION_AS_ENVIRONMENT,
)


@pytest.fixture(autouse=True, name="s3_client")
def s3_client_fixture(config: Dict[str, Any]) -> S3Client:
    """Returns a AWS S3 Client."""  # noqa: D401
    return get_client("s3", config)


@pytest.mark.aws
@pytest.mark.infra
def aws_s3_data_bucket_exists_validation(
    config: Dict[str, Any], s3_client: S3Client
) -> None:  # pragma: no cover
    """S3 data storage bucket exists."""  # noqa: D401
    aws_s3_data_bucket_exists(config, s3_client)


@validator
def aws_s3_data_bucket_exists(config: Dict[str, Any], s3_client: S3Client) -> None:
    """Check to see if the s3 data bucket exists."""
    # make sure that an entry exists for the data storage path
    data_bucket_url: str = get_config_value(
        config,
        "infra:aws:vpc:existing:storage:data",
    )
    aws_s3_bucket_exists(config, data_bucket_url, s3_client)


@pytest.mark.aws
@pytest.mark.infra
def aws_s3_logs_bucket_exists_validation(
    config: Dict[str, Any], s3_client: S3Client
) -> None:  # pragma: no cover
    """S3 log storage location exists."""  # noqa: D401
    aws_s3_logs_bucket_exists(config, s3_client)


@validator
def aws_s3_logs_bucket_exists(config: Dict[str, Any], s3_client: S3Client) -> None:
    """Check to see if the s3 logs bucket exists."""
    # make sure that an entry exists for the data storage path
    logs_bucket_url: str = get_config_value(
        config,
        "infra:aws:vpc:existing:storage:logs",
    )
    aws_s3_bucket_exists(config, logs_bucket_url, s3_client)


@pytest.mark.aws
@pytest.mark.infra
def aws_s3_backup_bucket_exists_validation(
    config: Dict[str, Any]
) -> None:  # pragma: no cover
    """S3 backup storage location exists."""  # noqa: D401,E501
    s3_client: S3Client = get_client("s3", config)
    aws_s3_backup_bucket_exists(config, s3_client)


@validator
def aws_s3_backup_bucket_exists(config: Dict[str, Any], s3_client: S3Client) -> None:
    """Check to see if the s3 backup bucket exists."""
    # make sure that an entry exists for the data storage path
    backup_bucket_url: str = get_config_value(
        config,
        "infra:aws:vpc:existing:storage:backup",
    )
    # TODO: Handle a specific parameter for backup S3 location once it exists
    aws_s3_bucket_exists(config, backup_bucket_url, s3_client)


def aws_s3_bucket_exists(
    config: Dict[str, Any], bucket_url: str, s3_client: S3Client
) -> None:
    """Check to see if the s3 bucket exists."""
    if not is_valid_s3a_url(bucket_url):
        fail(AWS_S3_BUCKET_INVALID, bucket_url)

    # get bucket name
    bucket_name = parse_arn(convert_s3a_to_arn(bucket_url))["resource_type"]

    vpc_region: str = get_config_value(
        config,
        "infra:aws:region",
    )
    # check if bucket exists in same region
    try:
        if (
            s3_client.get_bucket_location(Bucket=bucket_name)["LocationConstraint"]
            != vpc_region
        ):
            fail(AWS_S3_BUCKET_NOT_IN_SAME_REGION_AS_ENVIRONMENT, bucket_name)
    except botocore.exceptions.ClientError as e:
        # if a client error is thrown, check if it is a NoSuchBucket error
        # if NoSuchBucket error thrown, the bucket does not exist
        error_code = e.response["Error"]["Code"]
        if error_code == "NoSuchBucket":
            fail(AWS_S3_BUCKET_DOES_NOT_EXIST, bucket_name)
        elif int(error_code) == 403:
            fail(AWS_S3_BUCKET_FORBIDDEN_ACCESS, bucket_name)
