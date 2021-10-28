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
# Source File Name:  validate_azure_ranger_identity.py
###
"""Validation of Azure Ranger Audit Identity."""
from typing import Any, Dict, List

import pytest
from azure.mgmt.authorization import AuthorizationManagementClient
from azure.mgmt.resource import ResourceManagementClient

from cdpctl.validation import fail, get_config_value
from cdpctl.validation.azure_utils import (
    check_for_actions,
    get_client,
    get_role_assignments,
    get_storage_container_scope,
    parse_adls_path,
)
from cdpctl.validation.infra.issues import (
    AZURE_IDENTITY_MISSING_ACTIONS_FOR_LOCATION,
    AZURE_IDENTITY_MISSING_DATA_ACTIONS_FOR_LOCATION,
)


@pytest.fixture(autouse=True, name="resource_client")
def resource_client_fixture(config: Dict[str, Any]) -> ResourceManagementClient:
    """Return an Azure Resource Client."""
    return get_client("resource", config)


@pytest.fixture(autouse=True, name="auth_client")
def auth_client_fixture(config: Dict[str, Any]) -> AuthorizationManagementClient:
    """Return an Azure Auth Client."""
    return get_client("auth", config)


@pytest.mark.azure
@pytest.mark.infra
def azure_ranger_audit_container_actions_validation(
    config: Dict[str, Any],
    auth_client: AuthorizationManagementClient,
    resource_client: ResourceManagementClient,
    azure_ranger_audit_required_actions,
) -> None:  # pragma: no cover
    """Ranger Audit Identity has all required Actions on data storage location."""
    _azure_ranger_audit_container_actions_check(
        config=config,
        auth_client=auth_client,
        resource_client=resource_client,
        azure_actions_required_actions=azure_ranger_audit_required_actions,
    )


def _azure_ranger_audit_container_actions_check(
    config: Dict[str, Any],
    auth_client: AuthorizationManagementClient,
    resource_client: ResourceManagementClient,
    azure_actions_required_actions: List[str],
) -> None:  # pragma: no cover
    # noqa: D401,E501

    sub_id: str = get_config_value(config=config, key="infra:azure:subscription_id")
    rg_name: str = get_config_value(config=config, key="infra:azure:metagroup:name")
    ident_name: str = get_config_value(
        config=config, key="env:azure:role:name:ranger_audit"
    )
    storage_name: str = get_config_value(config=config, key="env:azure:storage:name")
    path: str = get_config_value(config=config, key="env:azure:storage:path:data")

    parsed_path = parse_adls_path(path)
    container_name = parsed_path[1]

    role_assignments = get_role_assignments(
        auth_client=auth_client,
        resource_client=resource_client,
        identity_name=ident_name,
        subscription_id=sub_id,
        resource_group=rg_name,
    )

    proper_scope = get_storage_container_scope(
        sub_id, rg_name, storage_name, container_name
    )

    missing_actions, _ = check_for_actions(
        auth_client=auth_client,
        role_assigments=role_assignments,
        proper_scope=proper_scope,
        required_actions=azure_actions_required_actions,
        required_data_actions=[],
    )

    if missing_actions:
        fail(
            AZURE_IDENTITY_MISSING_ACTIONS_FOR_LOCATION,
            subjects=[
                ident_name,
                f"storageAccounts/{storage_name}/blobServices/default/containers/{container_name}",  # noqa: E501
            ],
            resources=missing_actions,
        )


@pytest.mark.azure
@pytest.mark.infra
def azure_ranger_audit_container_data_actions_validation(
    config: Dict[str, Any],
    auth_client: AuthorizationManagementClient,
    resource_client: ResourceManagementClient,
    azure_ranger_audit_required_data_actions: List[str],
) -> None:  # pragma: no cover
    """Ranger Audit Identity has all required Data Actions on data storage location."""
    _azure_ranger_audit_container_data_actions_check(
        config=config,
        auth_client=auth_client,
        resource_client=resource_client,
        azure_ranger_audit_required_data_actions=azure_ranger_audit_required_data_actions,  # noqa: E501
    )


def _azure_ranger_audit_container_data_actions_check(
    config: Dict[str, Any],
    auth_client: AuthorizationManagementClient,
    resource_client: ResourceManagementClient,
    azure_ranger_audit_required_data_actions: List[str],
) -> None:  # pragma: no cover
    # noqa: D401,E501

    sub_id: str = get_config_value(config=config, key="infra:azure:subscription_id")
    rg_name: str = get_config_value(config=config, key="infra:azure:metagroup:name")
    ident_name: str = get_config_value(
        config=config, key="env:azure:role:name:ranger_audit"
    )
    storage_name: str = get_config_value(config=config, key="env:azure:storage:name")
    path: str = get_config_value(config=config, key="env:azure:storage:path:data")

    parsed_path = parse_adls_path(path)
    container_name = parsed_path[1]

    role_assignments = get_role_assignments(
        auth_client=auth_client,
        resource_client=resource_client,
        identity_name=ident_name,
        subscription_id=sub_id,
        resource_group=rg_name,
    )

    proper_scope = get_storage_container_scope(
        sub_id, rg_name, storage_name, container_name
    )

    _, missing_data_actions = check_for_actions(
        auth_client=auth_client,
        role_assigments=role_assignments,
        proper_scope=proper_scope,
        required_actions=[],
        required_data_actions=azure_ranger_audit_required_data_actions,
    )

    if missing_data_actions:
        fail(
            AZURE_IDENTITY_MISSING_DATA_ACTIONS_FOR_LOCATION,
            subjects=[
                ident_name,
                f"storageAccounts/{storage_name}/blobServices/default/containers/{container_name}",  # noqa: E501
            ],
            resources=missing_data_actions,
        )


@pytest.mark.azure
@pytest.mark.infra
def azure_ranger_audit_backup_storage_actions_validation(
    config: Dict[str, Any],
    auth_client: AuthorizationManagementClient,
    resource_client: ResourceManagementClient,
    azure_ranger_audit_required_actions,
) -> None:  # pragma: no cover
    """Ranger Audit Identity has all required Actions on backup storage location."""
    _azure_ranger_audit_backup_storage_actions_check(
        config=config,
        auth_client=auth_client,
        resource_client=resource_client,
        azure_actions_required_actions=azure_ranger_audit_required_actions,
    )


def _azure_ranger_audit_backup_storage_actions_check(
    config: Dict[str, Any],
    auth_client: AuthorizationManagementClient,
    resource_client: ResourceManagementClient,
    azure_actions_required_actions: List[str],
) -> None:  # pragma: no cover
    # noqa: D401,E501

    sub_id: str = get_config_value(config=config, key="infra:azure:subscription_id")
    rg_name: str = get_config_value(config=config, key="infra:azure:metagroup:name")
    ident_name: str = get_config_value(
        config=config, key="env:azure:role:name:ranger_audit"
    )
    storage_name: str = get_config_value(config=config, key="env:azure:storage:name")
    path: str = get_config_value(config=config, key="env:azure:storage:path:backup")

    parsed_path = parse_adls_path(path)
    container_name = parsed_path[1]

    role_assignments = get_role_assignments(
        auth_client=auth_client,
        resource_client=resource_client,
        identity_name=ident_name,
        subscription_id=sub_id,
        resource_group=rg_name,
    )

    proper_scope = get_storage_container_scope(
        sub_id, rg_name, storage_name, container_name
    )

    missing_actions, _ = check_for_actions(
        auth_client=auth_client,
        role_assigments=role_assignments,
        proper_scope=proper_scope,
        required_actions=azure_actions_required_actions,
        required_data_actions=[],
    )

    if missing_actions:
        fail(
            AZURE_IDENTITY_MISSING_ACTIONS_FOR_LOCATION,
            subjects=[
                ident_name,
                f"storageAccounts/{storage_name}/blobServices/default/containers/{container_name}",  # noqa: E501
            ],
            resources=missing_actions,
        )


@pytest.mark.azure
@pytest.mark.infra
def azure_ranger_audit_backup_storage_data_actions_validation(
    config: Dict[str, Any],
    auth_client: AuthorizationManagementClient,
    resource_client: ResourceManagementClient,
    azure_ranger_audit_required_data_actions: List[str],
) -> None:  # pragma: no cover
    """Ranger Audit Identity has all required Data Actions on backup storage location."""  # noqa: E501
    _azure_ranger_audit_backup_storage_data_actions_check(
        config=config,
        auth_client=auth_client,
        resource_client=resource_client,
        azure_ranger_audit_required_data_actions=azure_ranger_audit_required_data_actions,  # noqa: E501
    )


def _azure_ranger_audit_backup_storage_data_actions_check(
    config: Dict[str, Any],
    auth_client: AuthorizationManagementClient,
    resource_client: ResourceManagementClient,
    azure_ranger_audit_required_data_actions: List[str],
) -> None:  # pragma: no cover
    # noqa: D401,E501

    sub_id: str = get_config_value(config=config, key="infra:azure:subscription_id")
    rg_name: str = get_config_value(config=config, key="infra:azure:metagroup:name")
    ident_name: str = get_config_value(
        config=config, key="env:azure:role:name:ranger_audit"
    )
    storage_name: str = get_config_value(config=config, key="env:azure:storage:name")
    path: str = get_config_value(config=config, key="env:azure:storage:path:backup")

    parsed_path = parse_adls_path(path)
    container_name = parsed_path[1]

    role_assignments = get_role_assignments(
        auth_client=auth_client,
        resource_client=resource_client,
        identity_name=ident_name,
        subscription_id=sub_id,
        resource_group=rg_name,
    )

    proper_scope = get_storage_container_scope(
        sub_id, rg_name, storage_name, container_name
    )

    _, missing_data_actions = check_for_actions(
        auth_client=auth_client,
        role_assigments=role_assignments,
        proper_scope=proper_scope,
        required_actions=[],
        required_data_actions=azure_ranger_audit_required_data_actions,
    )

    if missing_data_actions:
        fail(
            AZURE_IDENTITY_MISSING_DATA_ACTIONS_FOR_LOCATION,
            subjects=[
                ident_name,
                f"storageAccounts/{storage_name}/blobServices/default/containers/{container_name}",  # noqa: E501
            ],
            resources=missing_data_actions,
        )
