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
# Source File Name:  validate_azure_example.py
###
"""Validation of Azure."""
from typing import Any, Dict

import pytest
from azure.mgmt.resource import ResourceManagementClient

from cdpctl.validation import validator
from cdpctl.validation.azure_utils import get_client


@pytest.fixture(autouse=True, name="resource_client")
def resource_client_fixture(config: Dict[str, Any]) -> ResourceManagementClient:
    """Return an Azure Client."""
    return get_client("resource", config)


@pytest.mark.aws
@pytest.mark.infra
def azure_client_validation(
    config: Dict[str, Any], resource_client: ResourceManagementClient
) -> None:  # pragma: no cover
    """Azure test example."""  # noqa: D401
    _azure_client_validation(config, resource_client)


@validator
def _azure_client_validation(
    config: Dict[str, Any],  # pylint: disable=unused-argument
    resource_client: ResourceManagementClient,
) -> None:  # pragma: no cover
    """Azure test example."""  # noqa: D401,E501

    # Retrieve the list of resource groups
    group_list = resource_client.resource_groups.list()

    # Show the groups in formatted output
    column_width = 40

    print("Resource Group".ljust(column_width) + "Location")
    print("-" * (column_width * 2))

    for group in list(group_list):
        print(f"{group.name:<{column_width}}{group.location}")
