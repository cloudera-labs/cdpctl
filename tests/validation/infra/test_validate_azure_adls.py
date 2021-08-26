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
# Source File Name:  test_validate_azure_adls.py
###
"""Azure ADLS Tests."""
import pytest

from cdpctl.validation.infra.validate_azure_adls import (
    azure_adls_data_storage_validation,
    azure_adls_logs_storage_validation,
)
from tests.validation import expect_validation_failure, expect_validation_success


class DataLakeServiceClient:
    """Mock class for unit testing."""

    def __init__(self, config, url):
        """Mock init for testing."""
        self.config = config
        self.url = url
        self.client = None

    def get_file_system_client(self, file_system=None):
        """Mock method for testing."""
        if file_system == "failure":
            self.client = Client(False)
        else:
            self.client = Client(True)
        return self.client


class Client:
    """Mock class for unit testing."""

    def __init__(self, val):
        """Mock init for testing."""
        self.exists_val = val

    def exists(self):
        """Mock method for testing."""
        return self.exists_val


CONFIG = {
    "env": {
        "azure": {
            "storage": {
                "path": {
                    "data": "adls://container@test.dfs.core.windows.net",
                    "logs": "adls://container@test.dfs.core.windows.net",
                }
            }
        }
    }
}
FAILURE_CONFIG = {
    "env": {
        "azure": {
            "storage": {
                "path": {
                    "data": "adls://failure@test.dfs.core.windows.net",
                    "logs": "adls://failure@test.dfs.core.windows.net",
                }
            }
        }
    }
}
EMPTY_CONFIG = {}


@pytest.fixture(autouse=True, name="dls_client")
def datalake_service_client_fixture():
    """Return an Azure Datalake service Client."""

    def _get_client(config, url):
        # pylint: disable=redefined-outer-name
        return DataLakeServiceClient(config, url)

    return _get_client


def test_azure_adls_data_storage_validation_success(
    dls_client: DataLakeServiceClient,
) -> None:
    func = expect_validation_success(azure_adls_data_storage_validation)
    func(CONFIG, dls_client)


def test_azure_adls_data_storage_validation_failure(
    dls_client: DataLakeServiceClient,
) -> None:

    func = expect_validation_failure(azure_adls_data_storage_validation)
    func(FAILURE_CONFIG, dls_client)


def test_azure_adls_data_storage_validation_wo_config_failure(
    dls_client: DataLakeServiceClient,
) -> None:

    func = expect_validation_failure(azure_adls_data_storage_validation)
    func(EMPTY_CONFIG, dls_client)


def test_azure_adls_logs_storage_validation_success(
    dls_client: DataLakeServiceClient,
) -> None:
    func = expect_validation_success(azure_adls_logs_storage_validation)
    func(CONFIG, dls_client)


def test_azure_adls_logs_storage_validation_failure(
    dls_client: DataLakeServiceClient,
) -> None:
    func = expect_validation_failure(azure_adls_logs_storage_validation)
    func(FAILURE_CONFIG, dls_client)


def test_azure_adls_logs_storage_validation_wo_config_failure(
    dls_client: DataLakeServiceClient,
) -> None:
    func = expect_validation_failure(azure_adls_logs_storage_validation)
    func(EMPTY_CONFIG, dls_client)
