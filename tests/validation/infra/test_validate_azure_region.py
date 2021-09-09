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
# Source File Name:  test_validate_azure_region.py
###
"""Azure Region Tests."""

from typing import Any, Dict

from cdpctl.validation.azure_utils import AzureSupportedRegionFeatures
from cdpctl.validation.infra.validate_azure_region import (
    azure_region,
    azure_region_experiences,
)
from tests.validation import (
    expect_validation_failure,
    expect_validation_success,
    expect_validation_warning,
)


def test_azure_region_success():
    config: Dict[str, Any] = {"infra": {"azure": {"region": "West US 2"}}}
    supported_regions_list = ["West US 2"]

    func = expect_validation_success(azure_region)
    func(config, supported_regions_list)


def test_azure_region_failure():
    config: Dict[str, Any] = {"infra": {"azure": {"region": "Germany Central"}}}
    supported_regions_list = ["West US 2"]

    func = expect_validation_failure(azure_region)
    func(config, supported_regions_list)


def test_azure_region_experiences_success():
    config: Dict[str, Any] = {"infra": {"azure": {"region": "West US 2"}}}
    supported_regions_experiences = {
        "West US 2": {
            AzureSupportedRegionFeatures.ENVIRONMENT.value: True,
            AzureSupportedRegionFeatures.DATA_HUB.value: True,
            AzureSupportedRegionFeatures.DATA_WAREHOUSE.value: True,
            AzureSupportedRegionFeatures.DATA_ENGINEERING.value: True,
            AzureSupportedRegionFeatures.OPERATIONAL_DATABASE.value: True,
            AzureSupportedRegionFeatures.MACHINE_LEARNING.value: True,
        }
    }
    func = expect_validation_success(azure_region_experiences)
    func(config, supported_regions_experiences)


def test_azure_region_experiences_failure():
    config: Dict[str, Any] = {"infra": {"azure": {"region": "West US 2"}}}
    supported_regions_experiences = {}
    func = expect_validation_failure(azure_region_experiences)
    func(config, supported_regions_experiences)


def test_azure_region_experiences_warnings():
    config: Dict[str, Any] = {"infra": {"azure": {"region": "West US 2"}}}
    supported_regions_experiences = {
        "West US 2": {
            AzureSupportedRegionFeatures.ENVIRONMENT.value: True,
            AzureSupportedRegionFeatures.DATA_HUB.value: True,
            AzureSupportedRegionFeatures.DATA_WAREHOUSE.value: False,
            AzureSupportedRegionFeatures.DATA_ENGINEERING.value: True,
            AzureSupportedRegionFeatures.OPERATIONAL_DATABASE.value: True,
            AzureSupportedRegionFeatures.MACHINE_LEARNING.value: False,
        }
    }
    func = expect_validation_warning(azure_region_experiences)
    func(config, supported_regions_experiences)
