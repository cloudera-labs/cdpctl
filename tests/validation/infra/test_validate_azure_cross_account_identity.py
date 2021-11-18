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
# Source File Name:  test_validate_azure_cross_account_identity.py
###
"""Azure Validate Cross Account Identity Tests."""
import dataclasses
from typing import Dict, List
from unittest.mock import Mock

from azure.core.exceptions import ResourceNotFoundError
from azure.mgmt.authorization import AuthorizationManagementClient
from azure.mgmt.resource import ResourceManagementClient

from cdpctl.validation.azure_utils import get_resource_group_scope
from cdpctl.validation.infra.validate_azure_cross_account_identity import (
    azure_cross_account_identity_exists_validation,
    azure_cross_account_rg_actions_validation,
    azure_cross_account_rg_data_actions_validation,
)
from tests.validation import expect_validation_failure, expect_validation_success


def get_config(role_name):
    return {
        "infra": {
            "azure": {"subscription_id": "test_id", "metagroup": {"name": "rg_name"}}
        },
        "env": {
            "azure": {
                "role": {"name": {"cross_account": f"{role_name}"}},
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
    cross_account_info: Dict,
    actions: List,
    data_actions: List,
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
    auth_client.role_assignments.list.return_value = [
        AuthListResponseProperties(identity_name, scope)
    ]

    Permission = dataclasses.make_dataclass(
        "Permission",
        [
            "actions",
            "not_actions",
            "data_actions",
            "not_data_actions",
        ],
    )

    RoleDefinition = dataclasses.make_dataclass(
        "RoleDefinition", ["role_name", "permissions"]
    )

    auth_client.role_definitions.get_by_id.return_value = RoleDefinition(
        azure_role,
        [
            Permission(
                actions=actions,
                not_actions=[],
                data_actions=data_actions,
                not_data_actions=[],
            )
        ],
    )

    cross_account_info["assignments"] = [
        AuthListResponseProperties(identity_name, scope)
    ]
    cross_account_info["name"] = identity_name
    cross_account_info["sub_id"] = "test_id"
    cross_account_info["rg_name"] = "rg_name"


def test_azure_cross_account_identity_exists_validation_success():
    scope = get_resource_group_scope("test_id", "rg_name")

    resource_client = Mock(spec=ResourceManagementClient)
    auth_client = Mock(spec=AuthorizationManagementClient)

    cross_account_info = {}

    setup_mocks(
        resource_client=resource_client,
        auth_client=auth_client,
        identity_name="cross_account",
        azure_role="Virtual Machine Contributor",
        scope=scope,
        cross_account_info=cross_account_info,
        actions=[],
        data_actions=[],
    )

    func = expect_validation_success(azure_cross_account_identity_exists_validation)
    func(get_config("cross_account"), auth_client, resource_client)


def test_azure_cross_account_identity_exists_validation_fail():
    scope = get_resource_group_scope("test_id", "rg_name")

    resource_client = Mock(spec=ResourceManagementClient)
    auth_client = Mock(spec=AuthorizationManagementClient)

    cross_account_info = {}

    setup_mocks(
        resource_client=resource_client,
        auth_client=auth_client,
        identity_name="notassumer",
        azure_role="Virtual Machine Contributor",
        scope=scope,
        cross_account_info=cross_account_info,
        actions=[],
        data_actions=[],
    )

    func = expect_validation_failure(azure_cross_account_identity_exists_validation)
    func(get_config("cross_account"), auth_client, resource_client)


def test_azure_cross_account_rg_actions_validation_success(
    azure_cross_account_required_resource_group_actions: List[str],
):
    identity_name = "cross_account"
    scope = get_resource_group_scope("test_id", "rg_name")
    resource_client = Mock(spec=ResourceManagementClient)
    auth_client = Mock(spec=AuthorizationManagementClient)

    cross_account_info = {}

    setup_mocks(
        resource_client=resource_client,
        auth_client=auth_client,
        identity_name=identity_name,
        azure_role="Storage Blob Data Contributor",
        scope=scope,
        cross_account_info=cross_account_info,
        actions=azure_cross_account_required_resource_group_actions,
        data_actions=[],
    )

    func = expect_validation_success(azure_cross_account_rg_actions_validation)
    func(
        auth_client,
        azure_cross_account_required_resource_group_actions,
        cross_account_info,
    )


def test_azure_cross_account_rg_actions_validation_fail(
    azure_cross_account_required_resource_group_actions: List[str],
):
    identity_name = "cross_account"
    scope = get_resource_group_scope("test_id", "rg_name")
    resource_client = Mock(spec=ResourceManagementClient)
    auth_client = Mock(spec=AuthorizationManagementClient)

    cross_account_info = {}

    setup_mocks(
        resource_client=resource_client,
        auth_client=auth_client,
        identity_name=identity_name,
        azure_role="Storage Blob Data Contributor",
        scope=scope,
        cross_account_info=cross_account_info,
        actions=[],
        data_actions=[],
    )

    func = expect_validation_failure(azure_cross_account_rg_actions_validation)
    func(
        auth_client,
        azure_cross_account_required_resource_group_actions,
        cross_account_info,
    )


def test_azure_cross_account_rg_data_actions_validation_success(
    azure_cross_account_required_resource_group_data_actions: List[str],
):
    identity_name = "cross_account"
    scope = get_resource_group_scope("test_id", "rg_name")
    resource_client = Mock(spec=ResourceManagementClient)
    auth_client = Mock(spec=AuthorizationManagementClient)

    cross_account_info = {}

    setup_mocks(
        resource_client=resource_client,
        auth_client=auth_client,
        identity_name=identity_name,
        azure_role="Storage Blob Data Contributor",
        scope=scope,
        cross_account_info=cross_account_info,
        actions=[],
        data_actions=azure_cross_account_required_resource_group_data_actions,
    )

    func = expect_validation_success(azure_cross_account_rg_data_actions_validation)
    func(
        auth_client,
        azure_cross_account_required_resource_group_data_actions,
        cross_account_info,
    )


def test_azure_cross_account_rg_data_actions_validation_fail(
    azure_cross_account_required_resource_group_data_actions: List[str],
):
    identity_name = "cross_account"
    scope = get_resource_group_scope("test_id", "rg_name")
    resource_client = Mock(spec=ResourceManagementClient)
    auth_client = Mock(spec=AuthorizationManagementClient)

    cross_account_info = {}

    setup_mocks(
        resource_client=resource_client,
        auth_client=auth_client,
        identity_name=identity_name,
        azure_role="Storage Blob Data Contributor",
        scope=scope,
        cross_account_info=cross_account_info,
        actions=[],
        data_actions=[],
    )

    func = expect_validation_failure(azure_cross_account_rg_data_actions_validation)
    func(
        auth_client,
        azure_cross_account_required_resource_group_data_actions,
        cross_account_info,
    )
