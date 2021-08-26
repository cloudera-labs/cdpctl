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
# Source File Name:  test_azure_utils.py
###
"""Azure Utils Test."""
import pytest
from azure.storage.filedatalake import DataLakeServiceClient
from cdpctl.validation.azure_utils import (
    AzureSupportedRegionFeatures,
    read_azure_supported_regions,
)
from cdpctl.validation.azure_utils import parse_adls_path, get_client


def test_read_azure_supported_regions():
    """Test of the basic config."""
    regions, regions_feature_map = read_azure_supported_regions()
    assert regions
    assert "West US 2" in regions
    assert "West US 2" in regions_feature_map
    assert regions_feature_map["West US 2"][
        AzureSupportedRegionFeatures.ENVIRONMENT.value
    ]
    assert regions_feature_map["West US 2"][AzureSupportedRegionFeatures.DATA_HUB.value]
    assert regions_feature_map["West US 2"][
        AzureSupportedRegionFeatures.DATA_WAREHOUSE.value
    ]
    assert regions_feature_map["West US 2"][
        AzureSupportedRegionFeatures.DATA_WAREHOUSE.value
    ]
    assert regions_feature_map["West US 2"][
        AzureSupportedRegionFeatures.MACHINE_LEARNING.value
    ]
    assert regions_feature_map["West US 2"][
        AzureSupportedRegionFeatures.OPERATIONAL_DATABASE.value
    ]
    assert "Germany Central" in regions_feature_map
    assert "Germany Central" not in regions


def test_get_client():
    """Test Datalake service client."""
    datalake_client_service = get_client(
        "datalake",
        {"infra": {"azure": {"subscription_id": 123}}},
        "https://test.dfs.core.windows.net",
    )
    assert isinstance(datalake_client_service, DataLakeServiceClient)


def test_parse_adls_path():
    """Test parse adls path."""
    parsed_url = parse_adls_path("adls://container@test.dfs.core.windows.net")
    assert parsed_url[0].startswith("https://")
    assert parsed_url[1] == ("container")


def test_parse_adls_path_invalid():
    """Test parse adls path with invalid value."""
    with pytest.raises(ValueError):
        parse_adls_path("container@test.dfs.core.windows.net")


def test_parse_adls_path_invalid_container():
    """Test parse adls path with invalid container value."""
    with pytest.raises(ValueError):
        parse_adls_path("adls://test.dfs.core.windows.net")
