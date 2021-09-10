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
# Source File Name:  validate_azure_region.py
###
"""Validation of Azure."""
from typing import Any, Dict, List

import pytest

from cdpctl.validation import fail, get_config_value, validator, warn
from cdpctl.validation.infra.issues import (
    AZURE_REGION_FEATURES_NOT_SUPPORTED,
    AZURE_REGION_NOT_SUPPORTED,
)


@pytest.mark.azure
@pytest.mark.infra
def azure_region_validation(
    config: Dict[str, Any], azure_supported_regions: List[str]
) -> None:  # pragma: no cover
    """Azure Region Supported."""  # noqa: D401
    azure_region(config, azure_supported_regions)


@validator
def azure_region(
    config: Dict[str, Any], azure_supported_regions: List[str]
) -> None:  # pragma: no cover
    """Check that the Azure region is supported."""  # noqa: D401,E501
    config_region: str = get_config_value(config=config, key="infra:azure:region")
    if config_region not in azure_supported_regions:
        fail(AZURE_REGION_NOT_SUPPORTED, config_region)


@pytest.mark.azure
@pytest.mark.infra
@pytest.mark.dependency(depends=["azure_region_validation"])
def azure_region_experiences_validation(
    config: Dict[str, Any], azure_supported_region_experiences: Dict[str, bool]
) -> None:  # pragma: no cover
    """Azure Region Experience Support."""  # noqa: D401
    azure_region_experiences(config, azure_supported_region_experiences)


@validator
def azure_region_experiences(
    config: Dict[str, Any], azure_supported_region_experiences: Dict[str, bool]
) -> None:  # pragma: no cover
    """Check for unsupported experiences."""  # noqa: D401,E501
    config_region: str = get_config_value(config=config, key="infra:azure:region")
    if config_region not in azure_supported_region_experiences:
        fail(AZURE_REGION_FEATURES_NOT_SUPPORTED, config_region)

    unsupported_experiences = []
    for experience, supported in azure_supported_region_experiences[
        config_region
    ].items():
        if not supported:
            unsupported_experiences.append(experience)

    if unsupported_experiences:
        warn(
            AZURE_REGION_FEATURES_NOT_SUPPORTED, config_region, unsupported_experiences
        )
