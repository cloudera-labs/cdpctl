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
# Source File Name:  validate_azure_logger_identity.py
###
"""Validation of Azure Logger Identity."""
from typing import Any, Dict

import pytest
from azure.mgmt.authorization import AuthorizationManagementClient
from azure.mgmt.resource import ResourceManagementClient

from cdpctl.validation import fail, get_config_value
from cdpctl.validation.azure_utils import get_client, parse_adls_path
from cdpctl.validation.infra.issues import (
    AZURE_LOGGER_IDENTITY_MISSING_BLOB_CONTRIBUTOR,
    AZURE_LOGGER_IDENTITY_NOT_FOUND,
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
def azure_logger_blob_role_validation(
    config: Dict[str, Any],
    auth_client: AuthorizationManagementClient,
    resource_client: ResourceManagementClient,
) -> None:  # pragma: no cover
    """Logger Identity has the Storage Blob Data Contributor Role."""  # noqa: D401,E501

    sub_id: str = get_config_value(config=config, key="infra:azure:subscription_id")
    rg_name: str = get_config_value(config=config, key="infra:azure:metagroup:name")
    logger_name: str = get_config_value(config=config, key="env:azure:role:name:log")
    storage_name: str = get_config_value(config=config, key="env:azure:storage:name")
    log_path: str = get_config_value(config=config, key="env:azure:storage:path:logs")

    parsed_logger_path = parse_adls_path(log_path)
    container_name = parsed_logger_path[1]

    logger_id = f"/subscriptions/{sub_id}/resourcegroups/{rg_name}/providers/Microsoft.ManagedIdentity/userAssignedIdentities/{logger_name}"  # noqa: E501
    logger_identity = resource_client.resources.get_by_id(
        resource_id=logger_id, api_version="2018-11-30"
    )

    if not logger_identity:
        fail(AZURE_LOGGER_IDENTITY_NOT_FOUND, logger_name)

    logger_identity_pricipalid = logger_identity.properties["principalId"]

    role_assignments = auth_client.role_assignments.list(
        filter=f"principalId eq '{logger_identity_pricipalid}'"
    )

    found_blob_data_contributor = False
    proper_scope = f"/subscriptions/{sub_id}/resourceGroups/{rg_name}/providers/Microsoft.Storage/storageAccounts/{storage_name}/blobServices/default/containers/{container_name}"  # noqa: E501

    for role_assignment in role_assignments:

        definition = auth_client.role_definitions.get_by_id(
            role_assignment.properties.role_definition_id
        )

        if (
            definition.role_name == "Storage Blob Data Contributor"
            and role_assignment.properties.scope == proper_scope
        ):
            found_blob_data_contributor = True

    if not found_blob_data_contributor:
        fail(AZURE_LOGGER_IDENTITY_MISSING_BLOB_CONTRIBUTOR, logger_name)
