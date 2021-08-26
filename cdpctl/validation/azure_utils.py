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
# Source File Name:  azure_utils.py
###
"""Azure Specific Utils."""
import csv
import os
from enum import Enum
from typing import Optional, Tuple

from azure.identity import AzureCliCredential
from azure.mgmt.authorization import AuthorizationManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.resource import ResourceManagementClient
from azure.storage.filedatalake import DataLakeServiceClient

from cdpctl.validation import UnrecoverableValidationError, get_config_value
from cdpctl.validation.issues import AZURE_NO_SUBSCRIPTION_HAS_BEEN_DEFINED


def get_client(client_type: str, config, url=None):
    """
    Get an Azure client for the specified type.

    If the subscription_id is not defined, it will throw an exception.
    """
    subscription_id: Optional[str] = get_config_value(
        config,
        "infra:azure:subscription_id",
        key_value_expected=True,
        data_expected_issue=AZURE_NO_SUBSCRIPTION_HAS_BEEN_DEFINED,
    )

    credential = AzureCliCredential()

    if client_type == "resource":
        return ResourceManagementClient(credential, subscription_id)

    if client_type == "auth":
        return AuthorizationManagementClient(credential, subscription_id)

    if client_type == "datalake":
        return DataLakeServiceClient(url, credential)

    if client_type == "network":
        return NetworkManagementClient(
            credential=credential, subscription_id=subscription_id
        )

    raise Exception(f"Unable to create Azure client for type {client_type}")


def validate_azure_config(config):
    """Validate that the nessesary Azure configs are set."""
    try:
        get_client("resource", config)
    except Exception as ex:
        raise UnrecoverableValidationError(ex) from ex


class AzureSupportedRegionFeatures(Enum):
    """Enum of CDP Features."""

    ENVIRONMENT = "Environment"
    DATA_HUB = "Data Hub"
    DATA_WAREHOUSE = "Data Warehouse"
    MACHINE_LEARNING = "Machine Learning"
    DATA_ENGINEERING = "Data Engineering"
    OPERATIONAL_DATABASE = "Operational Database"


# Function to convert a CSV to JSON
# Takes the file paths as arguments
def read_azure_supported_regions():
    """Load the Azure Supported Regions and Feature Matrix."""

    support_features_map = {}
    basic_supported_regions = []

    csv_file = os.path.join(
        os.path.dirname(__file__), "resources/AzureRegionSupport.csv"
    )

    with open(csv_file, encoding="utf-8") as csvf:
        csvReader = csv.DictReader(csvf)
        for rows in csvReader:
            region = rows["Region Name"]
            support_features_map[region] = rows
            del support_features_map[region]["Region Name"]

            for name, val in support_features_map[region].items():
                support_features_map[region][name] = val.lower() == "true"
            if support_features_map[region][
                AzureSupportedRegionFeatures.ENVIRONMENT.value
            ]:
                basic_supported_regions.append(region)
    return basic_supported_regions, support_features_map


def parse_adls_path(path: str) -> Tuple:
    """Parse Azure ADLS path."""
    try:
        if not path.startswith("adls://"):
            raise ValueError(f"Invalid adls path: {path}")

        if not path.replace("adls://", "").split("@", 1)[0]:
            raise ValueError(f"Invalid adls path: {path}")

        return (
            "https://" + path.replace("adls://", "").split("@", 1)[1],
            path.replace("adls://", "").split("@", 1)[0],
        )

    except IndexError as ie:
        raise ValueError(f"Invalid adls path: {path}") from ie
