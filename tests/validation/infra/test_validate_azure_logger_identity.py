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
# Source File Name:  test_validate_azure_logger_identity.py
###
"""Azure Validate Logger Identity Tests."""

from cdpctl.validation.infra.validate_azure_logger_identity import (
    azure_logger_blob_role_validation,
)
from tests.validation import expect_validation_failure, expect_validation_success


def get_config(role_name):
    return {
        "infra": {
            "azure": {"subscription_id": "test_id", "metagroup": {"name": "rg_name"}}
        },
        "env": {
            "azure": {
                "role": {"name": {"log": f"{role_name}"}},
                "storage": {
                    "name": "storage_name",
                    "path": {"logs": "abfs://logs@storage_name.dfs.core.windows.net"},
                },
            }
        },
    }


class PropertiesType:
    """Mock for AuthResponseType.Properties."""

    role_definition_id = "success"
    scope = "/subscriptions/test_id/resourceGroups/rg_name/providers/Microsoft.Storage/storageAccounts/storage_name/blobServices/default/containers/logs"


class AuthResponseType:
    """Mock return type for AuthorizationManagementClient."""

    properties = PropertiesType
    role_name = "Storage Blob Data Contributor"


class ResourceResponseType:
    """Mock return type for ResourceManagementClient."""

    properties = {"principalId": "success"}


class ResourceManagementClientHelper:
    """Mock ResourceManagementClient Interface."""

    def get_by_id(
        resource_id, api_version
    ):  # pylint: disable=no-self-argument,unused-argument
        """Mock get_by_id."""
        resource = ResourceResponseType
        if (
            resource_id
            == "/subscriptions/test_id/resourcegroups/rg_name/providers/Microsoft.ManagedIdentity/userAssignedIdentities/fail"
        ):
            resource.properties["principalId"] = "fail"
        return resource


class AuthorizationManagementClientHelper:
    """Mock Auth Interface."""

    def get_by_id(resource_id):  # pylint: disable=no-self-argument
        """Mock get_by_id."""
        resource = AuthResponseType
        if resource_id == "fail":
            resource.role_name = "fail"
        return resource

    def list(filter):  # pylint: disable=no-self-argument,redefined-builtin
        """Mock list function."""
        response = AuthResponseType
        if filter == "principalId eq 'fail'":
            response.properties.role_definition_id = "fail"
        return [response]


class ResourceManagementClient:
    """Mock ResourceManagementClient interface."""

    resources = ResourceManagementClientHelper


class AuthorizationManagementClient:
    """Mock AuthorizationManagementClient interface."""

    role_assignments = AuthorizationManagementClientHelper
    role_definitions = AuthorizationManagementClientHelper


def test_azure_logger_blob_role_validation_success() -> None:

    auth_client = AuthorizationManagementClient()
    resource_client = ResourceManagementClient

    func = expect_validation_success(azure_logger_blob_role_validation)
    func(get_config("success"), auth_client, resource_client)


def test_azure_logger_blob_role_validation_fail() -> None:

    auth_client = AuthorizationManagementClient
    resource_client = ResourceManagementClient

    func = expect_validation_failure(azure_logger_blob_role_validation)
    func(get_config("fail"), auth_client, resource_client)
