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
# Source File Name:  test_validate_aws_s3_locations.py
###
"""Test of S3 storage locations validation."""
from typing import Any, Dict

import pytest
from boto3_type_annotations.s3 import Client as S3Client
from botocore.stub import Stubber

from cdpctl.validation.aws_utils import get_client
from cdpctl.validation.infra.validate_aws_s3_locations import (
    aws_s3_backup_bucket_exists,
    aws_s3_data_bucket_exists,
    aws_s3_logs_bucket_exists,
)
from tests.validation import expect_validation_failure, expect_validation_success


@pytest.fixture(autouse=True, name="s3_client")
def s3_client_fixture() -> S3Client:
    """Get the S3 client."""
    config: Dict[str, Any] = {"infra": {"aws": {"region": "us-west-2", "profile": ""}}}
    return get_client("s3", config)


# type: ignore[misc]
def test_aws_s3_data_bucket_exists(s3_client: S3Client) -> None:
    """Test the check of an existing s3 bucket."""
    config: Dict[str, Any] = {
        "infra": {
            "aws": {
                "region": "us-west-2",
                "vpc": {"existing": {"storage": {"data": "s3a://mybucket/data"}}},
            }
        }
    }
    stubber = Stubber(s3_client)
    stubber.add_response(
        "get_bucket_location",
        {"LocationConstraint": "us-west-2"},
        expected_params={"Bucket": "mybucket"},
    )
    stubber.activate()
    func = expect_validation_success(aws_s3_data_bucket_exists)
    func(config, s3_client)


# type: ignore[misc]
def test_aws_s3_data_bucket_missing(s3_client: S3Client) -> None:
    """Test the validation with a missing s3 bucket fails."""
    config: Dict[str, Any] = {
        "infra": {
            "aws": {"vpc": {"existing": {"storage": {"data": "s3a://mybucket/data"}}}}
        }
    }
    stubber = Stubber(s3_client)
    stubber.add_client_error(
        "get_bucket_location",
        service_error_code="NoSuchBucket",
        service_message="The specified bucket does not exist",
        expected_params={"Bucket": "mybucket"},
    )
    stubber.activate()
    func = expect_validation_failure(aws_s3_data_bucket_exists)
    func(config, s3_client)


# type: ignore[misc]
def test_aws_s3_data_bucket_config_is_invalid(s3_client: S3Client) -> None:
    """Test the check of an S3 bucket with an invalid configuration."""
    func = expect_validation_failure(aws_s3_data_bucket_exists)

    config: Dict[str, Any] = {
        "infra": {"aws": {"vpc": {"existing": {"storage": {"data": ""}}}}}
    }
    func(config, s3_client)

    config2: Dict[str, Any] = {
        "infra": {"aws": {"vpc": {"existing": {"storage": {"data": "bad/s3a/url"}}}}}
    }
    func(config2, s3_client)


# type: ignore[misc]
def test_aws_s3_logs_bucket_exists(s3_client: S3Client) -> None:
    """Test the check of an existing s3 bucket."""
    config: Dict[str, Any] = {
        "infra": {
            "aws": {
                "region": "us-west-2",
                "vpc": {"existing": {"storage": {"logs": "s3a://mybucket/logs"}}},
            }
        }
    }
    stubber = Stubber(s3_client)
    stubber.add_response(
        "get_bucket_location",
        {"LocationConstraint": "us-west-2"},
        expected_params={"Bucket": "mybucket"},
    )
    stubber.activate()
    func = expect_validation_success(aws_s3_logs_bucket_exists)
    func(config, s3_client)


# type: ignore[misc]
def test_aws_s3_logs_bucket_missing(s3_client: S3Client) -> None:
    """Test the validation with a missing s3 bucket fails."""
    config: Dict[str, Any] = {
        "infra": {
            "aws": {"vpc": {"existing": {"storage": {"logs": "s3a://mybucket/logs"}}}}
        }
    }
    stubber = Stubber(s3_client)
    stubber.add_client_error(
        "get_bucket_location",
        service_error_code="NoSuchBucket",
        service_message="The specified bucket does not exist",
        expected_params={"Bucket": "mybucket"},
    )
    stubber.activate()
    func = expect_validation_failure(aws_s3_logs_bucket_exists)
    func(config, s3_client)


# type: ignore[misc]
def test_aws_s3_logs_bucket_config_is_invalid(s3_client: S3Client) -> None:
    """Test the check of an S3 bucket with an invalid configuration."""
    func = expect_validation_failure(aws_s3_logs_bucket_exists)

    config: Dict[str, Any] = {
        "infra": {"aws": {"vpc": {"existing": {"storage": {"logs": ""}}}}}
    }
    func(config, s3_client)

    config2: Dict[str, Any] = {
        "infra": {"aws": {"vpc": {"existing": {"storage": {"logs": "bad/s3a/url"}}}}}
    }
    func(config2, s3_client)


# type: ignore[misc]
def test_aws_s3_backup_bucket_exists(s3_client: S3Client) -> None:
    """Test the check of an existing s3 bucket."""
    config: Dict[str, Any] = {
        "infra": {
            "aws": {
                "region": "us-west-2",
                "vpc": {"existing": {"storage": {"backup": "s3a://mybucket/backup"}}},
            }
        }
    }
    stubber = Stubber(s3_client)
    stubber.add_response(
        "get_bucket_location",
        {"LocationConstraint": "us-west-2"},
        expected_params={"Bucket": "mybucket"},
    )
    stubber.activate()
    func = expect_validation_success(aws_s3_backup_bucket_exists)
    func(config, s3_client)


# type: ignore[misc]
def test_aws_s3_backup_bucket_missing(s3_client: S3Client) -> None:
    """Test the validation with a missing s3 bucket fails."""
    config: Dict[str, Any] = {
        "infra": {
            "aws": {
                "vpc": {"existing": {"storage": {"backup": "s3a://mybucket/backup"}}}
            }
        }
    }
    stubber = Stubber(s3_client)
    stubber.add_client_error(
        "get_bucket_location",
        service_error_code="NoSuchBucket",
        service_message="The specified bucket does not exist",
        expected_params={"Bucket": "mybucket"},
    )
    stubber.activate()
    func = expect_validation_failure(aws_s3_backup_bucket_exists)
    func(config, s3_client)


# type: ignore[misc]
def test_aws_s3_backup_bucket_config_is_invalid(s3_client: S3Client) -> None:
    """Test the check of an S3 bucket with an invalid configuration."""
    func = expect_validation_failure(aws_s3_backup_bucket_exists)

    config: Dict[str, Any] = {
        "infra": {"aws": {"vpc": {"existing": {"storage": {"backup": ""}}}}}
    }
    func(config, s3_client)

    config2: Dict[str, Any] = {
        "infra": {"aws": {"vpc": {"existing": {"storage": {"backup": "bad/s3a/url"}}}}}
    }
    func(config2, s3_client)
