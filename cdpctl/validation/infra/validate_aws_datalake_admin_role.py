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
# Source File Name:  validate_aws_datalake_admin_role.py
###
"""Validation of AWS IAM datalake_admin role."""
from typing import Any, Dict, List

import pytest
from boto3_type_annotations.iam import Client as IAMClient

from cdpctl.validation import get_config_value, validator
from cdpctl.validation.aws_utils import (
    convert_s3a_to_arn,
    get_client,
    get_role,
    parse_arn,
    simulate_policy,
)
from cdpctl.validation.infra.issues import (
    AWS_ROLE_FOR_DATA_BUCKET_MISSING_ACTIONS,
    AWS_ROLE_FOR_DL_BUCKET_MISSING_ACTIONS,
    AWS_ROLE_REQUIRES_ACTIONS_FOR_ALL_S3_RESOURCES,
)


@pytest.fixture(scope="module", name="bucket_access_policy_actions")
def bucket_access_policy_actions_fixture() -> List[str]:
    """
    Actions that must be allowed against the "datalake bucket" resource.

    SID: AllowListingOfDataLakeFolder.
    """
    return [
        "s3:GetAccelerateConfiguration",
        "s3:GetAnalyticsConfiguration",
        "s3:GetBucketAcl",
        "s3:GetBucketCORS",
        "s3:GetBucketLocation",
        "s3:GetBucketLogging",
        "s3:GetBucketNotification",
        "s3:GetBucketPolicy",
        "s3:GetBucketPolicyStatus",
        "s3:GetBucketPublicAccessBlock",
        "s3:GetBucketRequestPayment",
        "s3:GetBucketTagging",
        "s3:GetBucketVersioning",
        "s3:GetBucketWebsite",
        "s3:GetEncryptionConfiguration",
        "s3:GetInventoryConfiguration",
        "s3:GetLifecycleConfiguration",
        "s3:GetMetricsConfiguration",
        "s3:GetObject",
        "s3:GetObjectAcl",
        "s3:GetObjectTagging",
        "s3:GetObjectVersion",
        "s3:GetObjectVersionAcl",
        "s3:GetObjectVersionTagging",
        "s3:GetReplicationConfiguration",
        "s3:ListBucket",
        "s3:ListBucketMultipartUploads",
        "s3:ListMultipartUploadParts",
    ]


@pytest.fixture(scope="module", name="bucket_access_policy_all_resources_actions")
def bucket_access_policy_all_resources_actions_fixture() -> List[str]:
    """Actions that must be allowed against all S3 resources."""
    return ["s3:CreateJob", "s3:GetAccountPublicAccessBlock", "s3:ListJobs"]


@pytest.fixture(scope="module", name="datalake_admin_s3_policy_actions")
def datalake_admin_s3_policy_actions_fixture() -> List[str]:
    """Actions that must be allowed against the data storage location."""
    return [
        "s3:AbortMultipartUpload",
        "s3:DeleteObject",
        "s3:DeleteObjectVersion",
        "s3:GetAccelerateConfiguration",
        "s3:GetAnalyticsConfiguration",
        "s3:GetBucketAcl",
        "s3:GetBucketCORS",
        "s3:GetBucketLocation",
        "s3:GetBucketLogging",
        "s3:GetBucketNotification",
        "s3:GetBucketObjectLockConfiguration",
        "s3:GetBucketPolicy",
        "s3:GetBucketPolicyStatus",
        "s3:GetBucketPublicAccessBlock",
        "s3:GetBucketRequestPayment",
        "s3:GetBucketTagging",
        "s3:GetBucketVersioning",
        "s3:GetBucketWebsite",
        "s3:GetEncryptionConfiguration",
        "s3:GetInventoryConfiguration",
        "s3:GetLifecycleConfiguration",
        "s3:GetMetricsConfiguration",
        "s3:GetObject",
        "s3:GetObjectAcl",
        "s3:GetObjectLegalHold",
        "s3:GetObjectRetention",
        "s3:GetObjectTagging",
        "s3:GetObjectVersion",
        "s3:GetObjectVersionAcl",
        "s3:GetObjectVersionTagging",
        "s3:GetReplicationConfiguration",
        "s3:ListBucket",
        "s3:ListBucketMultipartUploads",
        "s3:ListBucketVersions",
        "s3:ListMultipartUploadParts",
        "s3:PutObject",
    ]


@pytest.fixture(autouse=True, name="iam_client")
def iam_client_fixture(config: Dict[str, Any]) -> IAMClient:
    """Returns the AWS IAM Client."""  # noqa: D401
    return get_client("iam", config)


@pytest.mark.aws
@pytest.mark.infra
@pytest.mark.dependency(
    depends=[
        "infra/validate_aws_s3_locations.py::aws_s3_data_bucket_exists_validation",
    ],
    scope="session",
)
def aws_datalake_admin_role_has_bucket_access_policy_validation(
    config: Dict[str, Any],
    iam_client: IAMClient,
    bucket_access_policy_actions: List[str],
) -> None:  # pragma: no cover
    """Datalake Admin role has the needed access to the S3 data bucket."""  # noqa: D401,E501
    aws_datalake_admin_role_has_bucket_access_policy(
        config, iam_client, bucket_access_policy_actions
    )


@validator
def aws_datalake_admin_role_has_bucket_access_policy(
    config: Dict[str, Any],
    iam_client: IAMClient,
    bucket_access_policy_actions: List[str],
) -> None:
    """Validate datalake_admin role has the needed access to the S3 data bucket."""

    datalake_admin_role_name: str = get_config_value(
        config,
        "env:aws:role:name:datalake_admin",
    )

    data_location: str = get_config_value(
        config,
        "infra:aws:vpc:existing:storage:data",
    )

    data_location_arn = convert_s3a_to_arn(data_location)
    bucket_name = parse_arn(data_location_arn)["resource_type"]
    bucket_arn = convert_s3a_to_arn(f"s3a://{bucket_name}")

    datalake_admin_role = get_role(iam_client, datalake_admin_role_name)
    datalake_admin_role_arn = datalake_admin_role["Role"]["Arn"]

    simulate_policy(
        iam_client=iam_client,
        policy_source_arn=datalake_admin_role_arn,
        resource_arns=[bucket_arn, f"{bucket_arn}/*"],
        needed_actions=bucket_access_policy_actions,
        subjects=[datalake_admin_role_name, bucket_name],
        missing_actions_issue=AWS_ROLE_FOR_DL_BUCKET_MISSING_ACTIONS,
    )


@pytest.mark.aws
@pytest.mark.infra
@pytest.mark.dependency(
    depends=[
        "infra/validate_aws_s3_locations.py::aws_s3_data_bucket_exists_validation",
    ],
    scope="session",
)
def aws_datalake_admin_role_has_bucket_access_policy_all_resources_validation(
    config: Dict[str, Any],
    iam_client: IAMClient,
    bucket_access_policy_all_resources_actions: List[str],
) -> None:  # pragma: no cover
    """Datalake Admin role has the needed access to all resources."""  # noqa: D401,E501
    aws_datalake_admin_role_has_bucket_access_policy_all_resources(
        config, iam_client, bucket_access_policy_all_resources_actions
    )


@validator
def aws_datalake_admin_role_has_bucket_access_policy_all_resources(
    config: Dict[str, Any],
    iam_client: IAMClient,
    bucket_access_policy_all_resources_actions: List[str],
) -> None:
    """Validate that datalake_admin role has the needed access to all resources."""

    datalake_admin_role_name: str = get_config_value(
        config,
        "env:aws:role:name:datalake_admin",
    )

    datalake_admin_role = get_role(iam_client, datalake_admin_role_name)
    datalake_admin_role_arn = datalake_admin_role["Role"]["Arn"]

    simulate_policy(
        iam_client=iam_client,
        policy_source_arn=datalake_admin_role_arn,
        resource_arns=["*"],
        needed_actions=bucket_access_policy_all_resources_actions,
        subjects=[datalake_admin_role_name],
        missing_actions_issue=AWS_ROLE_REQUIRES_ACTIONS_FOR_ALL_S3_RESOURCES,
    )


@pytest.mark.aws
@pytest.mark.infra
@pytest.mark.dependency(
    depends=[
        "infra/validate_aws_s3_locations.py::aws_s3_data_bucket_exists_validation",
    ],
    scope="session",
)
def aws_datalake_admin_role_has_s3_policy_validation(
    config: Dict[str, Any],
    iam_client: IAMClient,
    datalake_admin_s3_policy_actions: List[str],
) -> None:  # pragma: no cover
    """Datalake Admin role has the needed access to the data location."""  # noqa: D401,E501
    aws_datalake_admin_role_has_s3_policy(
        config,
        iam_client,
        datalake_admin_s3_policy_actions,
    )


@validator
def aws_datalake_admin_role_has_s3_policy(
    config: Dict[str, Any],
    iam_client: IAMClient,
    datalake_admin_s3_policy_actions: List[str],
) -> None:
    """Validate that datalake_admin role has the needed access to the data location."""

    datalake_admin_role_name: str = get_config_value(
        config,
        "env:aws:role:name:datalake_admin",
    )

    data_location: str = get_config_value(
        config,
        "infra:aws:vpc:existing:storage:data",
    )

    data_location_arn = convert_s3a_to_arn(data_location)

    datalake_admin_role = get_role(iam_client, datalake_admin_role_name)
    datalake_admin_role_arn = datalake_admin_role["Role"]["Arn"]

    simulate_policy(
        iam_client=iam_client,
        policy_source_arn=datalake_admin_role_arn,
        resource_arns=[data_location_arn, f"{data_location_arn}/*"],
        needed_actions=datalake_admin_s3_policy_actions,
        subjects=[datalake_admin_role_name, data_location],
        missing_actions_issue=AWS_ROLE_FOR_DATA_BUCKET_MISSING_ACTIONS,
    )


@pytest.mark.aws
@pytest.mark.infra
@pytest.mark.dependency(
    depends=[
        "infra/validate_aws_s3_locations.py::aws_s3_backup_bucket_exists_validation",
    ],
    scope="session",
)
def aws_datalake_admin_role_has_backup_bucket_access_policy_validation(
    config: Dict[str, Any],
    iam_client: IAMClient,
    bucket_access_policy_actions: List[str],
) -> None:  # pragma: no cover
    """Datalake Admin role has the needed access to the S3 backup bucket."""  # noqa: D401,E501
    aws_datalake_admin_role_has_backup_bucket_access_policy(
        config, iam_client, bucket_access_policy_actions
    )


@validator
def aws_datalake_admin_role_has_backup_bucket_access_policy(
    config: Dict[str, Any],
    iam_client: IAMClient,
    bucket_access_policy_actions: List[str],
) -> None:
    """Validate datalake_admin role has the needed access to the S3 backup bucket."""

    datalake_admin_role_name: str = get_config_value(
        config,
        "env:aws:role:name:datalake_admin",
    )

    data_location: str = get_config_value(
        config,
        "infra:aws:vpc:existing:storage:backup",
    )

    data_location_arn = convert_s3a_to_arn(data_location)
    bucket_name = parse_arn(data_location_arn)["resource_type"]
    bucket_arn = convert_s3a_to_arn(f"s3a://{bucket_name}")

    datalake_admin_role = get_role(iam_client, datalake_admin_role_name)
    datalake_admin_role_arn = datalake_admin_role["Role"]["Arn"]

    simulate_policy(
        iam_client=iam_client,
        policy_source_arn=datalake_admin_role_arn,
        resource_arns=[bucket_arn, f"{bucket_arn}/*"],
        needed_actions=bucket_access_policy_actions,
        subjects=[datalake_admin_role_name, bucket_name],
        missing_actions_issue=AWS_ROLE_FOR_DL_BUCKET_MISSING_ACTIONS,
    )
