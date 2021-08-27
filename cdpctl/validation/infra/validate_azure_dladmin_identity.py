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
# Source File Name:  validate_azure_dladmin_identity.py
###
"""Validation of Azure Datalake Admin Identity."""
from typing import Any, Dict

import pytest
from azure.mgmt.authorization import AuthorizationManagementClient
from azure.mgmt.resource import ResourceManagementClient

from cdpctl.validation import fail, get_config_value
from cdpctl.validation.azure_utils import (
    get_client,
    parse_adls_path,
    get_role_assignments,
    check_for_role,
)
from cdpctl.validation.infra.issues import AZURE_IDENTITY_MISSING_ROLE


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
def azure_dladmin_logs_owner_validation(
    config: Dict[str, Any],
    auth_client: AuthorizationManagementClient,
    resource_client: ResourceManagementClient,
) -> None:  # pragma: no cover
    """Datalake Admin Identity has the Logs Container Owner Role."""  # noqa: D401,E501

    sub_id: str = get_config_value(config=config, key="infra:azure:subscription_id")
    rg_name: str = get_config_value(config=config, key="infra:azure:metagroup:name")
    storage_name: str = get_config_value(config=config, key="env:azure:storage:name")
    log_path: str = get_config_value(config=config, key="env:azure:storage:path:logs")
    datalake_admin: str = get_config_value(
        config=config, key="env:azure:role:name:datalake_admin"
    )

    parsed_logger_path = parse_adls_path(log_path)
    container_name = parsed_logger_path[1]

    role_assignments = get_role_assignments(
        auth_client=auth_client,
        resource_client=resource_client,
        identity_name=datalake_admin,
        subscription_id=sub_id,
        resource_group=rg_name,
    )

    proper_scope = f"/subscriptions/{sub_id}/resourceGroups/{rg_name}/providers/Microsoft.Storage/storageAccounts/{storage_name}/blobServices/default/containers/{container_name}"  # noqa: E501
    proper_role = "Storage Blob Data Owner"

    if not check_for_role(
        auth_client=auth_client,
        role_assigments=role_assignments,
        proper_role=proper_role,
        proper_scope=proper_scope,
    ):
        fail(
            AZURE_IDENTITY_MISSING_ROLE,
            subjects=[
                datalake_admin,
                proper_role,
                f"storageAccounts/{storage_name}/blobServices/default/containers/{container_name}",  # noqa: E501
            ],
        )


@pytest.mark.azure
@pytest.mark.infra
def azure_dladmin_data_owner_validation(
    config: Dict[str, Any],
    auth_client: AuthorizationManagementClient,
    resource_client: ResourceManagementClient,
) -> None:  # pragma: no cover
    """Datalake Admin Identity has the Storage Container Owner Role."""  # noqa: D401,E501

    sub_id: str = get_config_value(config=config, key="infra:azure:subscription_id")
    rg_name: str = get_config_value(config=config, key="infra:azure:metagroup:name")
    storage_name: str = get_config_value(config=config, key="env:azure:storage:name")
    data_path: str = get_config_value(config=config, key="env:azure:storage:path:data")
    datalake_admin: str = get_config_value(
        config=config, key="env:azure:role:name:datalake_admin"
    )

    parsed_data_path = parse_adls_path(data_path)
    container_name = parsed_data_path[1]

    role_assignments = get_role_assignments(
        auth_client=auth_client,
        resource_client=resource_client,
        identity_name=datalake_admin,
        subscription_id=sub_id,
        resource_group=rg_name,
    )

    proper_scope = f"/subscriptions/{sub_id}/resourceGroups/{rg_name}/providers/Microsoft.Storage/storageAccounts/{storage_name}/blobServices/default/containers/{container_name}"  # noqa: E501
    proper_role = "Storage Blob Data Owner"

    if not check_for_role(
        auth_client=auth_client,
        role_assigments=role_assignments,
        proper_role=proper_role,
        proper_scope=proper_scope,
    ):
        fail(
            AZURE_IDENTITY_MISSING_ROLE,
            subjects=[
                datalake_admin,
                proper_role,
                f"storageAccounts/{storage_name}/blobServices/default/containers/{container_name}",  # noqa: E501
            ],
        )
