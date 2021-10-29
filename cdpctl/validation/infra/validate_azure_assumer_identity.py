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
# Source File Name:  validate_azure_assumer_identity.py
###
"""Validation of Azure Assumer Identity."""
from typing import Any, Dict, List

import pytest
from azure.mgmt.authorization import AuthorizationManagementClient
from azure.mgmt.resource import ResourceManagementClient

from cdpctl.validation import fail, get_config_value
from cdpctl.validation.azure_utils import (
    check_for_actions,
    get_client,
    get_resource_group_scope,
    get_role_assignments,
    get_storage_container_scope,
    parse_adls_path,
)
from cdpctl.validation.infra.issues import (
    AZURE_IDENTITY_MISSING_ACTIONS_FOR_LOCATION,
    AZURE_IDENTITY_MISSING_DATA_ACTIONS_FOR_LOCATION,
)

_assumer_info = {}


@pytest.fixture(name="assumer_info")
def assumer_info_fixture():
    """Get the info for the Assumer Identity."""
    return _assumer_info


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
def azure_assumer_identity_exists_validation(
    config: Dict[str, Any],
    auth_client: AuthorizationManagementClient,
    resource_client: ResourceManagementClient,
) -> None:  # pragma: no cover
    """Azure Assumer Identity exists."""

    _assumer_info["sub_id"] = get_config_value(
        config=config, key="infra:azure:subscription_id"
    )
    _assumer_info["rg_name"] = get_config_value(
        config=config, key="infra:azure:metagroup:name"
    )
    _assumer_info["name"] = get_config_value(
        config=config, key="env:azure:role:name:idbroker"
    )

    _assumer_info["assignments"] = get_role_assignments(
        auth_client=auth_client,
        resource_client=resource_client,
        identity_name=_assumer_info["name"],
        subscription_id=_assumer_info["sub_id"],
        resource_group=_assumer_info["rg_name"],
    )


@pytest.mark.azure
@pytest.mark.infra
@pytest.mark.dependency(depends=["azure_assumer_identity_exists_validation"])
def azure_assumer_logs_actions_validation(
    config: Dict[str, Any],
    auth_client: AuthorizationManagementClient,
    azure_assumer_required_logs_actions: List[str],
    assumer_info,
) -> None:  # pragma: no cover
    """Assumer Identity has the necessary actions on the Logs Container."""  # noqa: D401,E501

    storage_name: str = get_config_value(config=config, key="env:azure:storage:name")
    log_path: str = get_config_value(config=config, key="env:azure:storage:path:logs")

    parsed_logger_path = parse_adls_path(log_path)
    container_name = parsed_logger_path[1]

    proper_scope = get_storage_container_scope(
        assumer_info["sub_id"], assumer_info["rg_name"], storage_name, container_name
    )

    missing_actions, _ = check_for_actions(
        auth_client=auth_client,
        role_assigments=assumer_info["assignments"],
        proper_scope=proper_scope,
        required_actions=azure_assumer_required_logs_actions,
        required_data_actions=[],
    )

    if missing_actions:
        fail(
            AZURE_IDENTITY_MISSING_ACTIONS_FOR_LOCATION,
            subjects=[
                assumer_info["name"],
                f"storageAccounts/{storage_name}/blobServices/default/containers/{container_name}",  # noqa: E501
            ],
            resources=missing_actions,
        )


@pytest.mark.azure
@pytest.mark.infra
@pytest.mark.dependency(depends=["azure_assumer_identity_exists_validation"])
def azure_assumer_logs_data_actions_validation(
    config: Dict[str, Any],
    auth_client: AuthorizationManagementClient,
    azure_assumer_required_logs_data_actions: List[str],
    assumer_info,
) -> None:  # pragma: no cover
    """Assumer Identity has the necessary data actions on the Logs Container."""  # noqa: D401,E501

    storage_name: str = get_config_value(config=config, key="env:azure:storage:name")
    log_path: str = get_config_value(config=config, key="env:azure:storage:path:logs")

    parsed_logger_path = parse_adls_path(log_path)
    container_name = parsed_logger_path[1]

    proper_scope = get_storage_container_scope(
        assumer_info["sub_id"], assumer_info["rg_name"], storage_name, container_name
    )

    _, missing_data_actions = check_for_actions(
        auth_client=auth_client,
        role_assigments=assumer_info["assignments"],
        proper_scope=proper_scope,
        required_actions=[],
        required_data_actions=azure_assumer_required_logs_data_actions,
    )

    if missing_data_actions:
        fail(
            AZURE_IDENTITY_MISSING_DATA_ACTIONS_FOR_LOCATION,
            subjects=[
                assumer_info["name"],
                f"storageAccounts/{storage_name}/blobServices/default/containers/{container_name}",  # noqa: E501
            ],
            resources=missing_data_actions,
        )


@pytest.mark.azure
@pytest.mark.infra
@pytest.mark.dependency(depends=["azure_assumer_identity_exists_validation"])
def azure_assumer_rg_actions_validation(
    auth_client: AuthorizationManagementClient,
    azure_assumer_required_resource_group_actions: List[str],
    assumer_info,
) -> None:  # pragma: no cover
    """Assumer Identity has the necessary actions on the resource group."""  # noqa: D401,E501

    proper_scope = get_resource_group_scope(
        subscription_id=assumer_info["sub_id"], resource_group=assumer_info["rg_name"]
    )

    missing_actions, _ = check_for_actions(
        auth_client=auth_client,
        role_assigments=assumer_info["assignments"],
        proper_scope=proper_scope,
        required_actions=azure_assumer_required_resource_group_actions,
        required_data_actions=[],
    )

    if missing_actions:
        fail(
            AZURE_IDENTITY_MISSING_ACTIONS_FOR_LOCATION,
            subjects=[
                assumer_info["name"],
                proper_scope,  # noqa: E501
            ],
            resources=missing_actions,
        )
