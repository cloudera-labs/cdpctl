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
# Source File Name:  test_validate_azure_assumer_identity.py
###
"""Azure Validate Assumer Identity Tests."""
import dataclasses
from typing import Dict
from unittest.mock import Mock

from azure.core.exceptions import ResourceNotFoundError
from azure.mgmt.authorization import AuthorizationManagementClient
from azure.mgmt.resource import ResourceManagementClient

from cdpctl.validation.azure_utils import (
    get_resource_group_scope,
    get_storage_container_scope,
)
from cdpctl.validation.infra.validate_azure_assumer_identity import (
    azure_assumer_identity_exists_validation,
    azure_assumer_logs_contributor_validation,
    azure_assumer_managed_identity_operator_validation,
    azure_assumer_virtual_machine_contributor_validation,
)
from tests.validation import expect_validation_failure, expect_validation_success


def get_config(role_name):
    return {
        "infra": {
            "azure": {"subscription_id": "test_id", "metagroup": {"name": "rg_name"}}
        },
        "env": {
            "azure": {
                "role": {"name": {"idbroker": f"{role_name}"}},
                "storage": {
                    "name": "storage_name",
                    "path": {
                        "logs": "abfs://logs@storage_name.dfs.core.windows.net",
                    },
                },
            }
        },
    }


def setup_mocks(
    resource_client: ResourceManagementClient,
    auth_client: AuthorizationManagementClient,
    identity_name: str,
    azure_role: str,
    scope: str,
    assumer_info: Dict,
):
    ResourceGetbyidResponse = dataclasses.make_dataclass(
        "ResourceGetbyidResponse", [("properties", Dict)]
    )
    if identity_name == "notassumer":
        resource_client.resources.get_by_id.side_effect = ResourceNotFoundError()
    else:
        resource_client.resources.get_by_id.return_value = ResourceGetbyidResponse(
            {"principalId": identity_name}
        )

    AuthListResponseProperties = dataclasses.make_dataclass(
        "AuthListResponseProperties", [("role_definition_id", str), ("scope", str)]
    )
    AuthListResponse = dataclasses.make_dataclass(
        "AuthListResponse", [("properties", AuthListResponseProperties)]
    )
    auth_client.role_assignments.list.return_value = [
        AuthListResponse(AuthListResponseProperties(identity_name, scope))
    ]

    AuthGetByIdResponse = dataclasses.make_dataclass(
        "AuthGetByIdResponse", [("role_name", str)]
    )
    auth_client.role_definitions.get_by_id.return_value = AuthGetByIdResponse(
        azure_role
    )

    assumer_info["assignments"] = [
        AuthListResponse(AuthListResponseProperties(identity_name, scope))
    ]
    assumer_info["name"] = identity_name
    assumer_info["sub_id"] = "test_id"
    assumer_info["rg_name"] = "rg_name"


def test_azure_assumer_identity_exists_validation_success():
    scope = get_resource_group_scope("test_id", "rg_name")

    resource_client = Mock(spec=ResourceManagementClient)
    auth_client = Mock(spec=AuthorizationManagementClient)

    assumer_info = {}

    setup_mocks(
        resource_client=resource_client,
        auth_client=auth_client,
        identity_name="assumer",
        azure_role="Virtual Machine Contributor",
        scope=scope,
        assumer_info=assumer_info,
    )

    func = expect_validation_success(azure_assumer_identity_exists_validation)
    func(get_config("assumer"), auth_client, resource_client)


def test_azure_assumer_identity_exists_validation_fail():
    scope = get_resource_group_scope("test_id", "rg_name")

    resource_client = Mock(spec=ResourceManagementClient)
    auth_client = Mock(spec=AuthorizationManagementClient)

    assumer_info = {}

    setup_mocks(
        resource_client=resource_client,
        auth_client=auth_client,
        identity_name="notassumer",
        azure_role="Virtual Machine Contributor",
        scope=scope,
        assumer_info=assumer_info,
    )

    func = expect_validation_failure(azure_assumer_identity_exists_validation)
    func(get_config("assumer"), auth_client, resource_client)


def test_azure_assumer_logs_contributor_validation_success():
    identity_name = "assumer"
    scope = get_storage_container_scope("test_id", "rg_name", "storage_name", "logs")
    resource_client = Mock(spec=ResourceManagementClient)
    auth_client = Mock(spec=AuthorizationManagementClient)

    assumer_info = {}

    setup_mocks(
        resource_client=resource_client,
        auth_client=auth_client,
        identity_name="assumer",
        azure_role="Storage Blob Data Contributor",
        scope=scope,
        assumer_info=assumer_info,
    )

    func = expect_validation_success(azure_assumer_logs_contributor_validation)
    func(get_config(identity_name), auth_client, assumer_info)


def test_azure_assumer_logs_contributor_validation_fail():
    identity_name = "datalake_admin"
    scope = get_storage_container_scope("test_id", "rg_name", "storage_name", "logs")

    resource_client = Mock(spec=ResourceManagementClient)
    auth_client = Mock(spec=AuthorizationManagementClient)

    assumer_info = {}

    setup_mocks(
        resource_client=resource_client,
        auth_client=auth_client,
        identity_name="datalake_admin",
        azure_role="Failing Azure Role",
        scope=scope,
        assumer_info=assumer_info,
    )

    func = expect_validation_failure(azure_assumer_logs_contributor_validation)
    func(get_config(identity_name), auth_client, assumer_info)


def test_azure_assumer_managed_identity_operator_validation_success():
    scope = get_resource_group_scope("test_id", "rg_name")

    resource_client = Mock(spec=ResourceManagementClient)
    auth_client = Mock(spec=AuthorizationManagementClient)

    assumer_info = {}

    setup_mocks(
        resource_client=resource_client,
        auth_client=auth_client,
        identity_name="assumer",
        azure_role="Managed Identity Operator",
        scope=scope,
        assumer_info=assumer_info,
    )

    func = expect_validation_success(azure_assumer_managed_identity_operator_validation)
    func(auth_client, assumer_info)


def test_azure_assumer_managed_identity_operator_validation_fails():
    scope = get_resource_group_scope("test_id", "rg_name")

    resource_client = Mock(spec=ResourceManagementClient)
    auth_client = Mock(spec=AuthorizationManagementClient)

    assumer_info = {}

    setup_mocks(
        resource_client=resource_client,
        auth_client=auth_client,
        identity_name="assumer",
        azure_role="Managed Identity Operator Fails",
        scope=scope,
        assumer_info=assumer_info,
    )

    func = expect_validation_failure(azure_assumer_managed_identity_operator_validation)
    func(auth_client, assumer_info)


def test_azure_assumer_virtual_machine_contributor_validation_success():
    scope = get_resource_group_scope("test_id", "rg_name")

    resource_client = Mock(spec=ResourceManagementClient)
    auth_client = Mock(spec=AuthorizationManagementClient)

    assumer_info = {}

    setup_mocks(
        resource_client=resource_client,
        auth_client=auth_client,
        identity_name="assumer",
        azure_role="Virtual Machine Contributor",
        scope=scope,
        assumer_info=assumer_info,
    )

    func = expect_validation_success(
        azure_assumer_virtual_machine_contributor_validation
    )
    func(auth_client, assumer_info)


def test_azure_assumer_virtual_machine_contributor_validation_fails():
    scope = get_resource_group_scope("test_id", "rg_name")

    resource_client = Mock(spec=ResourceManagementClient)
    auth_client = Mock(spec=AuthorizationManagementClient)

    assumer_info = {}

    setup_mocks(
        resource_client=resource_client,
        auth_client=auth_client,
        identity_name="assumer",
        azure_role="Virtual Machine Contributor Fails",
        scope=scope,
        assumer_info=assumer_info,
    )

    func = expect_validation_failure(
        azure_assumer_virtual_machine_contributor_validation
    )
    func(auth_client, assumer_info)
