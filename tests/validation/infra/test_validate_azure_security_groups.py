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
# Source File Name:  test_validate_azure_security_groups.py
###
"""Azure Network Security Groups Tests."""
import dataclasses
from typing import Any, Dict
from unittest.mock import Mock

import pytest
from azure.core.exceptions import ResourceNotFoundError
from azure.mgmt.network import NetworkManagementClient

from cdpctl.validation.infra.validate_azure_security_groups import (
    azure_default_security_group_exists,
    azure_knox_security_group_exists,
    azure_security_group_allows_access_for_cdp_cidr_port,
    azure_subnets_accessable_by_default_security_group,
)
from tests.validation import (
    expect_validation_failure,
    expect_validation_success,
    expect_validation_warning,
)


@pytest.fixture(name="basic_azure_test_config")
def basic_azure_test_config_fixture() -> Dict[str, Any]:
    return {
        "infra": {
            "vpc": {"name": "some-vnet"},
            "azure": {
                "subscription_id": "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX",
                "metagroup": {"name": "some-resource-group"},
            },
            "security_group": {
                "default": {"name": "default-nsg"},
                "knox": {"name": "knox-nsg"},
            },
        }
    }


def test_azure_default_security_group_exists_success(basic_azure_test_config):
    NetworkSecurityGroup = dataclasses.make_dataclass("NetworkSecurityGroup", ["name"])
    nsg = NetworkSecurityGroup(
        basic_azure_test_config["infra"]["security_group"]["default"]["name"]
    )
    mock_network_mgmt_client = Mock(spec=NetworkManagementClient)
    mock_network_mgmt_client.network_security_groups.get.return_value = nsg
    func = expect_validation_success(azure_default_security_group_exists)
    func(basic_azure_test_config, mock_network_mgmt_client)


def test_azure_default_security_group_exists_failure(basic_azure_test_config):
    mock_network_mgmt_client = Mock(spec=NetworkManagementClient)
    mock_network_mgmt_client.network_security_groups.get.side_effect = (
        ResourceNotFoundError()
    )
    func = expect_validation_failure(azure_default_security_group_exists)
    func(basic_azure_test_config, mock_network_mgmt_client)


def test_azure_knox_security_group_exists_success(basic_azure_test_config):
    NetworkSecurityGroup = dataclasses.make_dataclass("NetworkSecurityGroup", ["name"])
    nsg = NetworkSecurityGroup(
        basic_azure_test_config["infra"]["security_group"]["knox"]["name"]
    )
    mock_network_mgmt_client = Mock(spec=NetworkManagementClient)
    mock_network_mgmt_client.network_security_groups.get.return_value = nsg
    func = expect_validation_success(azure_knox_security_group_exists)
    func(basic_azure_test_config, mock_network_mgmt_client)


def test_azure_knox_security_group_exists_failure(basic_azure_test_config):
    mock_network_mgmt_client = Mock(spec=NetworkManagementClient)
    mock_network_mgmt_client.network_security_groups.get.side_effect = (
        ResourceNotFoundError()
    )
    func = expect_validation_failure(azure_knox_security_group_exists)
    func(basic_azure_test_config, mock_network_mgmt_client)


def test_azure_subnets_accessable_by_default_security_group_validation_success():
    AddressSpace = dataclasses.make_dataclass("AddressSpace", ["address_prefixes"])
    Subnet = dataclasses.make_dataclass(
        "Subnet", ["name", "address_prefix", "delegations"]
    )
    VirtualNetwork = dataclasses.make_dataclass(
        "VirtualNetwork", ["name", "address_space", "subnets"]
    )

    vnet = VirtualNetwork(
        "vnet",
        AddressSpace(["10.0.0.0/16"]),
        [
            Subnet("default", "10.3.0.0/24", []),
            Subnet("default", "10.3.1.0/26", []),
        ],
    )

    SecurityRule = dataclasses.make_dataclass(
        "SecurityRule",
        [
            "name",
            "direction",
            "access",
            "source_address_prefix",
            "protocol",
            "destination_port_range",
            "destination_port_ranges",
            "source_port_range",
            "source_port_ranges",
        ],
    )
    NetworkSecurityGroup = dataclasses.make_dataclass(
        "NetworkSecurityGroup", ["name", "security_rules"]
    )
    nsg = NetworkSecurityGroup(
        "nsg",
        [
            SecurityRule(
                "default", "Inbound", "Allow", "10.3.0.0/16", "*", "*", None, "*", None
            )
        ],
    )
    func = expect_validation_success(azure_subnets_accessable_by_default_security_group)
    func(vnet, nsg, "Test")

    nsg2 = NetworkSecurityGroup(
        "nsg2",
        [
            SecurityRule(
                "defaultTCP",
                "Inbound",
                "Allow",
                "10.3.0.0/16",
                "TCP",
                "*",
                None,
                "*",
                None,
            ),
            SecurityRule(
                "defaultUDP",
                "Inbound",
                "Allow",
                "10.3.0.0/16",
                "UDP",
                "*",
                None,
                "*",
                None,
            ),
        ],
    )

    func = expect_validation_success(azure_subnets_accessable_by_default_security_group)
    func(vnet, nsg2, "Test")


def test_azure_subnets_accessable_by_default_security_group_validation_warn_not_covered():
    AddressSpace = dataclasses.make_dataclass("AddressSpace", ["address_prefixes"])
    Subnet = dataclasses.make_dataclass(
        "Subnet", ["name", "address_prefix", "delegations"]
    )
    VirtualNetwork = dataclasses.make_dataclass(
        "VirtualNetwork", ["name", "address_space", "subnets"]
    )

    vnet = VirtualNetwork(
        "vnet",
        AddressSpace(["10.0.0.0/16"]),
        [
            Subnet("default", "10.3.0.0/24", []),
            Subnet("default", "10.3.1.0/26", []),
        ],
    )

    SecurityRule = dataclasses.make_dataclass(
        "SecurityRule",
        [
            "name",
            "direction",
            "access",
            "source_address_prefix",
            "protocol",
            "destination_port_range",
            "destination_port_ranges",
            "source_port_range",
            "source_port_ranges",
        ],
    )
    NetworkSecurityGroup = dataclasses.make_dataclass(
        "NetworkSecurityGroup", ["name", "security_rules"]
    )
    nsg = NetworkSecurityGroup(
        "nsg",
        [
            SecurityRule(
                "default", "Inbound", "Allow", "10.3.0.0/24", "*", "*", None, "*", None
            )
        ],
    )
    func = expect_validation_warning(azure_subnets_accessable_by_default_security_group)
    func(vnet, nsg, "Test")


def test_azure_subnets_accessable_by_default_security_group_validation_fail_ports():
    AddressSpace = dataclasses.make_dataclass("AddressSpace", ["address_prefixes"])
    Subnet = dataclasses.make_dataclass(
        "Subnet", ["name", "address_prefix", "delegations"]
    )
    VirtualNetwork = dataclasses.make_dataclass(
        "VirtualNetwork", ["name", "address_space", "subnets"]
    )

    vnet = VirtualNetwork(
        "vnet",
        AddressSpace(["10.0.0.0/16"]),
        [
            Subnet("default", "10.3.0.0/24", []),
            Subnet("default", "10.3.1.0/26", []),
        ],
    )

    SecurityRule = dataclasses.make_dataclass(
        "SecurityRule",
        [
            "name",
            "direction",
            "access",
            "source_address_prefix",
            "protocol",
            "destination_port_range",
            "destination_port_ranges",
            "source_port_range",
            "source_port_ranges",
        ],
    )
    NetworkSecurityGroup = dataclasses.make_dataclass(
        "NetworkSecurityGroup", ["name", "security_rules"]
    )
    nsg = NetworkSecurityGroup(
        "nsg",
        [
            SecurityRule(
                "default",
                "Inbound",
                "Allow",
                "10.3.0.0/16",
                "*",
                "0-1024",
                None,
                "*",
                None,
            )
        ],
    )
    func = expect_validation_failure(azure_subnets_accessable_by_default_security_group)
    func(vnet, nsg, "Test")


def test_azure_security_group_allows_access_for_cdp_cidr_port_success():
    SecurityRule = dataclasses.make_dataclass(
        "SecurityRule",
        [
            "name",
            "direction",
            "access",
            "source_address_prefix",
            "source_address_prefixes",
            "protocol",
            "destination_port_range",
            "destination_port_ranges",
            "source_port_range",
            "source_port_ranges",
        ],
    )
    NetworkSecurityGroup = dataclasses.make_dataclass(
        "NetworkSecurityGroup", ["name", "security_rules"]
    )
    nsg = NetworkSecurityGroup(
        "nsg",
        [
            SecurityRule(
                "default",
                "Inbound",
                "Allow",
                None,
                ["52.36.110.208", "52.40.165.49", "35.166.86.177"],
                "*",
                None,
                ["443", "9443"],
                "*",
                None,
            )
        ],
    )
    func = expect_validation_success(
        azure_security_group_allows_access_for_cdp_cidr_port
    )
    func(
        nsg,
        ["52.36.110.208/32", "52.40.165.49/32", "35.166.86.177/32"],
        "Test",
        "TCP",
        443,
    )


def test_azure_security_group_allows_access_for_cdp_cidr_port_failure():
    SecurityRule = dataclasses.make_dataclass(
        "SecurityRule",
        [
            "name",
            "direction",
            "access",
            "source_address_prefix",
            "source_address_prefixes",
            "protocol",
            "destination_port_range",
            "destination_port_ranges",
            "source_port_range",
            "source_port_ranges",
        ],
    )
    NetworkSecurityGroup = dataclasses.make_dataclass(
        "NetworkSecurityGroup", ["name", "security_rules"]
    )
    nsg = NetworkSecurityGroup(
        "nsg",
        [
            SecurityRule(
                "default",
                "Inbound",
                "Allow",
                None,
                ["52.36.110.208", "52.40.165.49", "35.166.86.177"],
                "*",
                None,
                ["9443"],
                "*",
                None,
            )
        ],
    )
    func = expect_validation_failure(
        azure_security_group_allows_access_for_cdp_cidr_port
    )
    func(
        nsg,
        ["52.36.110.208/32", "52.40.165.49/32", "35.166.86.177/32"],
        "Test",
        "TCP",
        443,
    )
