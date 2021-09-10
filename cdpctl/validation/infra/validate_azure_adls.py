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
# Source File Name:  validate_azure_adls.py
###
"""Validation of Azure ADLS."""
from typing import Any, Dict

import pytest
from azure.storage.filedatalake import DataLakeServiceClient

from cdpctl.validation import fail, get_config_value
from cdpctl.validation.azure_utils import get_client, parse_adls_path
from cdpctl.validation.issues import (
    AZURE_INVALID_STORAGE_HAS_BEEN_DEFINED,
    AZURE_STORAGE_CONTAINER_DOES_NOT_EXIST,
    AZURE_STORAGE_NOT_DEFINED,
)


@pytest.fixture(autouse=True, name="dls_client")
def datalake_service_client_fixture():
    """Return an Azure Datalake service Client."""

    def _get_client(config, url):
        return get_client("datalake", config, url)

    return _get_client


@pytest.mark.azure
@pytest.mark.infra
def azure_adls_data_storage_validation(
    config: Dict[str, Any], dls_client: DataLakeServiceClient
) -> None:  # pragma: no cover
    """ADLS Storage Data Container exists."""  # noqa: D401
    try:
        data_path: str = get_config_value(
            config,
            "env:azure:storage:path:data",
            key_value_expected=True,
            data_expected_issue=AZURE_STORAGE_NOT_DEFINED,
        )
        parsed_url = parse_adls_path(data_path)
        service_client = dls_client(config, parsed_url[0])
        fsc = service_client.get_file_system_client(file_system=parsed_url[1])
        if not fsc.exists():
            fail(
                template=AZURE_STORAGE_CONTAINER_DOES_NOT_EXIST,
                subjects=[data_path],
            )
    except ValueError:
        fail(
            template=AZURE_INVALID_STORAGE_HAS_BEEN_DEFINED,
            subjects=[data_path],
        )


@pytest.mark.azure
@pytest.mark.infra
def azure_adls_logs_storage_validation(
    config: Dict[str, Any], dls_client: DataLakeServiceClient
) -> None:  # pragma: no cover
    """ADLS Storage Logs Container exists."""  # noqa: D401
    try:
        logs_path: str = get_config_value(
            config,
            "env:azure:storage:path:logs",
            key_value_expected=True,
            data_expected_issue=AZURE_STORAGE_NOT_DEFINED,
        )
        parsed_url = parse_adls_path(logs_path)
        service_client = dls_client(config, parsed_url[0])
        fsc = service_client.get_file_system_client(file_system=parsed_url[1])
        if not fsc.exists():
            fail(
                template=AZURE_STORAGE_CONTAINER_DOES_NOT_EXIST,
                subjects=[parsed_url[1]],
            )
    except ValueError:
        fail(
            template=AZURE_INVALID_STORAGE_HAS_BEEN_DEFINED,
            subjects=[logs_path],
        )
