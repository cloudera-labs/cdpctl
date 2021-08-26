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
"""Azure VNet Tests."""
import dataclasses
from typing import Any, Dict
from unittest.mock import Mock

import pytest
from azure.core.exceptions import ResourceNotFoundError
from azure.mgmt.network import NetworkManagementClient

from cdpctl.validation.infra.validate_azure_vnet import (
    azure_vnet_cidr_range,
    azure_vnet_cidr_range_private,
    azure_vnet_cidr_ranges_not_reserved,
    azure_vnet_exists,
    azure_vnet_subnets_count,
    azure_vnet_subnets_for_de,
    azure_vnet_subnets_for_ml,
    azure_vnet_subnets_range_for_dl_and_dh,
    azure_vnet_subnets_range_for_dw,
    vnet_reserved_ip_cidrs,
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
        }
    }


def test_azure_vnet_exists_success(basic_azure_test_config):
    VirtualNetwork = dataclasses.make_dataclass("VirtualNetwork", ["name", "subnets"])
    ret_vnet = VirtualNetwork(basic_azure_test_config["infra"]["vpc"]["name"], [])
    mock_network_mgmt_client = Mock(spec=NetworkManagementClient)
    mock_network_mgmt_client.virtual_networks.get.return_value = ret_vnet
    func = expect_validation_success(azure_vnet_exists)
    func(basic_azure_test_config, mock_network_mgmt_client)


def test_azure_vnet_exists_failure(basic_azure_test_config):
    mock_network_mgmt_client = Mock(spec=NetworkManagementClient)
    mock_network_mgmt_client.virtual_networks.get.side_effect = ResourceNotFoundError()
    func = expect_validation_failure(azure_vnet_exists)
    func(basic_azure_test_config, mock_network_mgmt_client)


def test_azure_vnet_subnets_count_success(basic_azure_test_config):
    VirtualNetwork = dataclasses.make_dataclass("VirtualNetwork", ["name", "subnets"])
    Subnet = dataclasses.make_dataclass("Subnet", ["name"])
    vnet = VirtualNetwork(
        basic_azure_test_config["infra"]["vpc"]["name"], [Subnet("a-subnet")]
    )
    func = expect_validation_success(azure_vnet_subnets_count)
    func(vnet)


def test_azure_vnet_subnets_count_failue(basic_azure_test_config):
    VirtualNetwork = dataclasses.make_dataclass("VirtualNetwork", ["name", "subnets"])
    vnet = VirtualNetwork(basic_azure_test_config["infra"]["vpc"]["name"], [])
    func = expect_validation_failure(azure_vnet_subnets_count)
    func(vnet)


def test_azure_vnet_cidr_range_success(basic_azure_test_config):
    AddressSpace = dataclasses.make_dataclass("AddressSpace", ["address_prefixes"])
    VirtualNetwork = dataclasses.make_dataclass(
        "VirtualNetwork", ["name", "address_space"]
    )
    vnet = VirtualNetwork(
        basic_azure_test_config["infra"]["vpc"]["name"], AddressSpace(["10.3.0.0/16"])
    )
    func = expect_validation_success(azure_vnet_cidr_range)
    func(vnet)


def test_azure_vnet_cidr_range_failure(basic_azure_test_config):
    AddressSpace = dataclasses.make_dataclass("AddressSpace", ["address_prefixes"])
    VirtualNetwork = dataclasses.make_dataclass(
        "VirtualNetwork", ["name", "address_space"]
    )
    vnet = VirtualNetwork(
        basic_azure_test_config["infra"]["vpc"]["name"], AddressSpace(["10.3.0.0/24"])
    )
    func = expect_validation_failure(azure_vnet_cidr_range)
    func(vnet)


def test_azure_vnet_cidr_range_multiple_success(basic_azure_test_config):
    AddressSpace = dataclasses.make_dataclass("AddressSpace", ["address_prefixes"])
    VirtualNetwork = dataclasses.make_dataclass(
        "VirtualNetwork", ["name", "address_space"]
    )
    vnet = VirtualNetwork(
        basic_azure_test_config["infra"]["vpc"]["name"],
        AddressSpace(["10.3.0.0/17", "10.3.128.0/17"]),
    )
    func = expect_validation_success(azure_vnet_cidr_range)
    func(vnet)


def test_azure_vnet_cidr_range_multiple_failure(basic_azure_test_config):
    AddressSpace = dataclasses.make_dataclass("AddressSpace", ["address_prefixes"])
    VirtualNetwork = dataclasses.make_dataclass(
        "VirtualNetwork", ["name", "address_space"]
    )
    vnet = VirtualNetwork(
        basic_azure_test_config["infra"]["vpc"]["name"],
        AddressSpace(["10.3.0.0/24", "10.3.1.0/24"]),
    )
    func = expect_validation_failure(azure_vnet_cidr_range)
    func(vnet)


def test_azure_vnet_cidr_ranges_not_reserved_failure(basic_azure_test_config):
    AddressSpace = dataclasses.make_dataclass("AddressSpace", ["address_prefixes"])
    VirtualNetwork = dataclasses.make_dataclass(
        "VirtualNetwork", ["name", "address_space"]
    )
    vnet = VirtualNetwork(
        basic_azure_test_config["infra"]["vpc"]["name"],
        AddressSpace(["10.0.0.0/16"]),
    )
    func = expect_validation_failure(azure_vnet_cidr_ranges_not_reserved)
    func(vnet, vnet_reserved_ip_cidrs)

    vnet2 = VirtualNetwork(
        basic_azure_test_config["infra"]["vpc"]["name"],
        AddressSpace(["10.3.0.0/17", "10.0.0.0/17"]),
    )
    func(vnet2, vnet_reserved_ip_cidrs)


def test_azure_vnet_cidr_ranges_not_reserved_success(basic_azure_test_config):
    AddressSpace = dataclasses.make_dataclass("AddressSpace", ["address_prefixes"])
    VirtualNetwork = dataclasses.make_dataclass(
        "VirtualNetwork", ["name", "address_space"]
    )
    vnet = VirtualNetwork(
        basic_azure_test_config["infra"]["vpc"]["name"],
        AddressSpace(["10.3.0.0/16"]),
    )
    func = expect_validation_success(azure_vnet_cidr_ranges_not_reserved)
    func(vnet, vnet_reserved_ip_cidrs)


def test_azure_vnet_cidr_range_private_success(basic_azure_test_config):
    AddressSpace = dataclasses.make_dataclass("AddressSpace", ["address_prefixes"])
    VirtualNetwork = dataclasses.make_dataclass(
        "VirtualNetwork", ["name", "address_space"]
    )
    vnet = VirtualNetwork(
        basic_azure_test_config["infra"]["vpc"]["name"],
        AddressSpace(["10.3.0.0/16"]),
    )
    func = expect_validation_success(azure_vnet_cidr_range_private)
    func(vnet)


def test_azure_vnet_cidr_range_private_failure(basic_azure_test_config):
    AddressSpace = dataclasses.make_dataclass("AddressSpace", ["address_prefixes"])
    VirtualNetwork = dataclasses.make_dataclass(
        "VirtualNetwork", ["name", "address_space"]
    )
    vnet = VirtualNetwork(
        basic_azure_test_config["infra"]["vpc"]["name"],
        AddressSpace(["11.0.0.0/16"]),
    )
    func = expect_validation_failure(azure_vnet_cidr_range_private)
    func(vnet)


def test_azure_vnet_subnets_range_for_dl_and_dh_success(basic_azure_test_config):
    Subnet = dataclasses.make_dataclass("Subnet", ["name", "address_prefix"])
    VirtualNetwork = dataclasses.make_dataclass("VirtualNetwork", ["name", "subnets"])
    vnet = VirtualNetwork(
        basic_azure_test_config["infra"]["vpc"]["name"],
        [Subnet("default", "10.3.0.0/24")],
    )
    func = expect_validation_success(azure_vnet_subnets_range_for_dl_and_dh)
    func(vnet)


def test_azure_vnet_subnets_range_for_dl_and_dh_failure(basic_azure_test_config):
    Subnet = dataclasses.make_dataclass("Subnet", ["name", "address_prefix"])
    VirtualNetwork = dataclasses.make_dataclass("VirtualNetwork", ["name", "subnets"])
    vnet = VirtualNetwork(
        basic_azure_test_config["infra"]["vpc"]["name"],
        [Subnet("default", "10.3.0.0/25")],
    )
    func = expect_validation_failure(azure_vnet_subnets_range_for_dl_and_dh)
    func(vnet)


def test_azure_vnet_subnets_range_for_dw_success(basic_azure_test_config):
    Subnet = dataclasses.make_dataclass("Subnet", ["name", "address_prefix"])
    VirtualNetwork = dataclasses.make_dataclass("VirtualNetwork", ["name", "subnets"])
    vnet = VirtualNetwork(
        basic_azure_test_config["infra"]["vpc"]["name"],
        [
            Subnet("default", "10.3.0.0/24"),
            Subnet("default", "10.3.16.0/20"),
            Subnet("default", "10.3.32.0/20"),
            Subnet("default", "10.3.48.0/20"),
        ],
    )
    func = expect_validation_success(azure_vnet_subnets_range_for_dw)
    func(vnet)


def test_azure_vnet_subnets_range_for_dw_warning_not_sized(basic_azure_test_config):
    Subnet = dataclasses.make_dataclass("Subnet", ["name", "address_prefix"])
    VirtualNetwork = dataclasses.make_dataclass("VirtualNetwork", ["name", "subnets"])
    vnet = VirtualNetwork(
        basic_azure_test_config["infra"]["vpc"]["name"],
        [
            Subnet("default", "10.3.0.0/24"),
            Subnet("default", "10.3.16.0/24"),
            Subnet("default", "10.3.32.0/20"),
            Subnet("default", "10.3.48.0/20"),
        ],
    )
    func = expect_validation_warning(azure_vnet_subnets_range_for_dw)
    func(vnet)


def test_azure_vnet_subnets_range_for_dw_warning_not_enough(basic_azure_test_config):
    Subnet = dataclasses.make_dataclass("Subnet", ["name", "address_prefix"])
    VirtualNetwork = dataclasses.make_dataclass("VirtualNetwork", ["name", "subnets"])
    vnet = VirtualNetwork(
        basic_azure_test_config["infra"]["vpc"]["name"],
        [
            Subnet("default", "10.3.16.0/20"),
            Subnet("default", "10.3.32.0/20"),
            Subnet("default", "10.3.48.0/20"),
        ],
    )
    func = expect_validation_warning(azure_vnet_subnets_range_for_dw)
    func(vnet)


def test_azure_vnet_subnets_for_ml_success(basic_azure_test_config):
    Delegation = dataclasses.make_dataclass("Delegation", ["service_name"])
    Subnet = dataclasses.make_dataclass(
        "Subnet", ["name", "address_prefix", "delegations"]
    )
    VirtualNetwork = dataclasses.make_dataclass("VirtualNetwork", ["name", "subnets"])
    vnet = VirtualNetwork(
        basic_azure_test_config["infra"]["vpc"]["name"],
        [
            Subnet("default", "10.3.0.0/24", []),
            Subnet("default", "10.3.1.0/24", []),
            Subnet("default", "10.3.2.0/28", [Delegation("Microsoft.Netapp/volumes")]),
        ],
    )
    func = expect_validation_success(azure_vnet_subnets_for_ml)
    func(vnet)


def test_azure_vnet_subnets_for_ml_warning_no_delegration(basic_azure_test_config):
    Subnet = dataclasses.make_dataclass(
        "Subnet", ["name", "address_prefix", "delegations"]
    )
    VirtualNetwork = dataclasses.make_dataclass("VirtualNetwork", ["name", "subnets"])
    vnet = VirtualNetwork(
        basic_azure_test_config["infra"]["vpc"]["name"],
        [
            Subnet("default", "10.3.0.0/24", []),
            Subnet("default", "10.3.1.0/24", []),
            Subnet("default", "10.3.2.0/25", []),
        ],
    )
    func = expect_validation_warning(azure_vnet_subnets_for_ml)
    func(vnet)


def test_azure_vnet_subnets_for_ml_warning_not_enough_subnets(basic_azure_test_config):
    Delegation = dataclasses.make_dataclass("Delegation", ["service_name"])
    Subnet = dataclasses.make_dataclass(
        "Subnet", ["name", "address_prefix", "delegations"]
    )
    VirtualNetwork = dataclasses.make_dataclass("VirtualNetwork", ["name", "subnets"])
    vnet = VirtualNetwork(
        basic_azure_test_config["infra"]["vpc"]["name"],
        [
            Subnet("default", "10.3.0.0/24", []),
            Subnet("default", "10.3.2.0/25", [Delegation("Microsoft.Netapp/volumes")]),
        ],
    )
    func = expect_validation_warning(azure_vnet_subnets_for_ml)
    func(vnet)


def test_azure_vnet_subnets_for_de_success(basic_azure_test_config):
    Subnet = dataclasses.make_dataclass(
        "Subnet", ["name", "address_prefix", "delegations"]
    )
    VirtualNetwork = dataclasses.make_dataclass("VirtualNetwork", ["name", "subnets"])
    vnet = VirtualNetwork(
        basic_azure_test_config["infra"]["vpc"]["name"],
        [
            Subnet("default", "10.3.0.0/24", []),
            Subnet("default", "10.3.1.0/24", []),
        ],
    )
    func = expect_validation_success(azure_vnet_subnets_for_de)
    func(vnet)


def test_azure_vnet_subnets_for_de_warning_not_enough_subnets(basic_azure_test_config):
    Subnet = dataclasses.make_dataclass(
        "Subnet", ["name", "address_prefix", "delegations"]
    )
    VirtualNetwork = dataclasses.make_dataclass("VirtualNetwork", ["name", "subnets"])
    vnet = VirtualNetwork(
        basic_azure_test_config["infra"]["vpc"]["name"],
        [
            Subnet("default", "10.3.0.0/24", []),
            Subnet("default", "10.3.1.0/26", []),
        ],
    )
    func = expect_validation_warning(azure_vnet_subnets_for_de)
    func(vnet)
