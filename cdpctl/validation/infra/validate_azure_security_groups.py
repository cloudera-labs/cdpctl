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
# Source File: validate_azure_secutiry_groups.py
"""Azure Network Security Groups Validations."""
import ipaddress
from typing import Any, Dict, List

import pytest
from azure.core.exceptions import ResourceNotFoundError
from azure.mgmt.network import NetworkManagementClient

from cdpctl.validation import fail, get_config_value, validator, warn
from cdpctl.validation.azure_utils import get_client
from cdpctl.validation.infra.issues import (
    AZURE_CDP_CIDR_ACCESS_NOT_ALLOWED_FOR_PORT,
    AZURE_NSG_NOT_FOUND,
    AZURE_SUBNETS_NOT_COVERED_BY_NSG,
    AZURE_SUBNETS_NOT_VALID_NSG,
    AZURE_VNET_NOT_FOUND,
)

_info = {}


@pytest.fixture(autouse=True, name="azure_network_client")
def azure_network_client_fixture(config: Dict[str, Any]) -> NetworkManagementClient:
    """Return an Azure Client."""
    return get_client("network", config)


def _load_vnet_info(vnet_name, resource_group_name, azure_network_client):
    if "vnet" not in _info:
        try:
            _info["vnet"] = azure_network_client.virtual_networks.get(
                virtual_network_name=vnet_name, resource_group_name=resource_group_name
            )
        except ResourceNotFoundError:
            fail(AZURE_VNET_NOT_FOUND, [vnet_name, resource_group_name])


@pytest.fixture(name="azure_resource_group_name")
def azure_resource_group_name_fixture(config: Dict[str, Any]):
    """Return the resource group name."""
    return get_config_value(config=config, key="infra:azure:metagroup:name")


@pytest.fixture(name="azure_vnet_name")
def azure_vnet_name_fixture(config: Dict[str, Any]):
    """Return the vnet name."""
    return get_config_value(config=config, key="infra:vpc:name")


@pytest.fixture(name="azure_vnet_info")
def azure_vnet_info_fixture(
    azure_vnet_name, azure_resource_group_name, azure_network_client
):
    """Return the vnet info."""
    _load_vnet_info(
        vnet_name=azure_vnet_name,
        resource_group_name=azure_resource_group_name,
        azure_network_client=azure_network_client,
    )
    return _info["vnet"]


@pytest.fixture(name="azure_default_nsg_info")
def azure_default_nsg_info_fixture():
    """Return the default nsg info."""
    return _info["default_nsg"]


@pytest.fixture(name="azure_knox_nsg_info")
def azure_knox_nsg_info_fixture():
    """Return the knox NSG info."""
    return _info["knox_nsg"]


@pytest.mark.azure
@pytest.mark.infra
@pytest.mark.dependency(
    depends=[
        "infra/validate_azure_region.py::azure_region_validation",
    ],
    scope="session",
)
def azure_default_security_group_exists_validation(
    config: Dict[str, Any],
    azure_network_client: NetworkManagementClient,
) -> None:  # pragma: no cover
    """Default Security Group exists."""  # noqa: D401
    azure_default_security_group_exists(config, azure_network_client)


@validator
def azure_default_security_group_exists(
    config: Dict[str, Any],
    azure_network_client: NetworkManagementClient,
) -> None:  # pragma: no cover
    """Check that the Security Group exists."""  # noqa: D401,E501
    resource_group_name = get_config_value(
        config=config, key="infra:azure:metagroup:name"
    )
    nsg_name = get_config_value(config=config, key="infra:security_group:default:name")
    try:
        _info["default_nsg"] = azure_network_client.network_security_groups.get(
            resource_group_name=resource_group_name,
            network_security_group_name=nsg_name,
        )
        pass
    except ResourceNotFoundError:
        fail(AZURE_NSG_NOT_FOUND, ["Default", nsg_name, resource_group_name])


@pytest.mark.azure
@pytest.mark.infra
@pytest.mark.dependency(
    depends=[
        "infra/validate_azure_region.py::azure_region_validation",
    ],
    scope="session",
)
def azure_knox_security_group_exists_validation(
    config: Dict[str, Any],
    azure_network_client: NetworkManagementClient,
) -> None:  # pragma: no cover
    """Knox Security Group exists."""  # noqa: D401
    azure_knox_security_group_exists(config, azure_network_client)


@validator
def azure_knox_security_group_exists(
    config: Dict[str, Any],
    azure_network_client: NetworkManagementClient,
) -> None:
    """Check that the Security Group exists."""  # noqa: D401,E501
    resource_group_name = get_config_value(
        config=config, key="infra:azure:metagroup:name"
    )
    nsg_name = get_config_value(config=config, key="infra:security_group:knox:name")
    try:
        _info["knox_nsg"] = azure_network_client.network_security_groups.get(
            resource_group_name=resource_group_name,
            network_security_group_name=nsg_name,
        )
        pass
    except ResourceNotFoundError:
        fail(AZURE_NSG_NOT_FOUND, ["Knox", nsg_name, resource_group_name])


def _do_ranges_cover_all(port_ranges):
    port_ranges = [port_ranges] if not isinstance(port_ranges, list) else port_ranges
    ports = []
    for port_range in port_ranges:
        if port_range == "*":
            return True
        if "-" in port_range:
            start_stop = port_range.split("-")
            ports = ports + list(range(int(start_stop[0]), int(start_stop[1]) + 1))
        else:
            ports.append(int(port_range))
    return sorted(list(set(ports))) == list(range(0, 65535 + 1))


def _do_ranges_cover_port(port_ranges, port_needed):
    port_ranges = [port_ranges] if not isinstance(port_ranges, list) else port_ranges
    ports = []
    for port_range in port_ranges:
        if "-" in port_range:
            start_stop = port_range.split("-")
            ports = ports + list(range(int(start_stop[0]), int(start_stop[1]) + 1))
        else:
            ports.append(int(port_range))
    return int(port_needed) in set(ports)


@pytest.mark.azure
@pytest.mark.infra
@pytest.mark.dependency(
    depends=[
        "azure_default_security_group_exists_validation",
    ]
)
def azure_subnets_accessable_by_default_security_group_validation(
    azure_vnet_info,
    azure_default_nsg_info,
) -> None:  # pragma: no cover
    """Default Security Group allows communication for subnets."""  # noqa: D401
    azure_subnets_accessable_by_default_security_group(
        azure_vnet_info, azure_default_nsg_info, "Default"
    )


@pytest.mark.azure
@pytest.mark.infra
@pytest.mark.dependency(
    depends=[
        "azure_knox_security_group_exists_validation",
    ]
)
def azure_subnets_accessable_by_knox_security_group_validation(
    azure_vnet_info,
    azure_knox_nsg_info,
) -> None:  # pragma: no cover
    """Knox Security Group allows communication for subnets."""  # noqa: D401
    azure_subnets_accessable_by_default_security_group(
        azure_vnet_info, azure_knox_nsg_info, "Knox"
    )


@validator
def azure_subnets_accessable_by_default_security_group(
    azure_vnet_info,
    azure_nsg_info,
    nsg_name,
) -> None:
    """Check that the Default Security Group allows communication for subnets."""  # noqa: D401,E501
    not_covered_subnets = []
    access_not_allowed = []

    for subnet in azure_vnet_info.subnets:  # pylint: disable=too-many-nested-blocks
        subnet_covered_by_nsg = False
        subnet_tcp_allowed = False
        subnet_udp_allowed = False
        subnet_network = ipaddress.ip_network(subnet.address_prefix)
        for security_rule in azure_nsg_info.security_rules:
            if security_rule.direction == "Inbound" and security_rule.access == "Allow":

                if security_rule.source_address_prefix:

                    source_addresses_prefixes = [
                        ipaddress.ip_network(
                            "0.0.0.0/0"
                            if security_rule.source_address_prefix == "*"
                            else security_rule.source_address_prefix
                        )
                    ]
                else:
                    source_addresses_prefixes = [
                        ipaddress.ip_network(prefix)
                        for prefix in security_rule.source_address_prefixes
                    ]

                for source_address_network in source_addresses_prefixes:
                    if source_address_network.overlaps(subnet_network):
                        subnet_covered_by_nsg = True
                        # dest ports open
                        dest_port_ranges = (
                            [security_rule.destination_port_range]
                            if security_rule.destination_port_range
                            else security_rule.destination_port_ranges
                        )

                        source_port_ranges = (
                            [security_rule.source_port_range]
                            if security_rule.source_port_range
                            else security_rule.source_port_ranges
                        )

                        if _do_ranges_cover_all(
                            dest_port_ranges
                        ) and _do_ranges_cover_all(source_port_ranges):
                            if security_rule.protocol == "TCP":
                                subnet_tcp_allowed = True
                            elif security_rule.protocol == "UDP":
                                subnet_udp_allowed = True
                            elif security_rule.protocol == "*":
                                subnet_tcp_allowed = True
                                subnet_udp_allowed = True

        if not subnet_covered_by_nsg:
            not_covered_subnets.append(
                f"Virtual Network: {azure_vnet_info.name} Subnet: {subnet.name}"
            )
        elif not subnet_tcp_allowed or not subnet_udp_allowed:
            access_not_allowed.append(
                f"Virtual Network: {azure_vnet_info.name} Subnet: {subnet.name}"
            )

    if not_covered_subnets:
        warn(
            AZURE_SUBNETS_NOT_COVERED_BY_NSG,
            [nsg_name, azure_nsg_info.name],
            not_covered_subnets,
        )

    if access_not_allowed:
        fail(
            AZURE_SUBNETS_NOT_VALID_NSG,
            [nsg_name, azure_nsg_info.name],
            access_not_allowed,
        )


@pytest.mark.azure
@pytest.mark.infra
@pytest.mark.config_value(path="env:tunnel", value=False)
def azure_default_security_group_allows_tcp_443_to_cdp_cidr_validation(
    azure_default_nsg_info,
    cdp_cidrs: List[str],
) -> None:  # pragma: no cover
    """Default security groups allows acccess to TCP port 443 for CDP CIDRs if CCM is not enabled."""  # noqa: D401,E501
    azure_security_group_allows_access_for_cdp_cidr_port(
        azure_default_nsg_info, cdp_cidrs, "Default", "TCP", 443
    )


@pytest.mark.azure
@pytest.mark.infra
@pytest.mark.config_value(path="env:tunnel", value=False)
def azure_knox_security_group_allows_tcp_443_to_cdp_cidr_validation(
    azure_knox_nsg_info,
    cdp_cidrs: List[str],
) -> None:  # pragma: no cover
    """Knox security groups allows acccess to TCP port 443 for CDP CIDRs if CCM is not enabled."""  # noqa: D401,E501
    azure_security_group_allows_access_for_cdp_cidr_port(
        azure_knox_nsg_info, cdp_cidrs, "Knox", "TCP", 443
    )


@pytest.mark.azure
@pytest.mark.infra
@pytest.mark.config_value(path="env:tunnel", value=False)
def azure_knox_security_group_allows_tcp_9443_to_cdp_cidr_validation(
    azure_knox_nsg_info,
    cdp_cidrs: List[str],
) -> None:  # pragma: no cover
    """Knox security groups allows acccess to TCP port 9443 for CDP CIDRs if CCM is not enabled."""  # noqa: D401,E501
    azure_security_group_allows_access_for_cdp_cidr_port(
        azure_knox_nsg_info, cdp_cidrs, "Knox", "TCP", 9443
    )


@validator
def azure_security_group_allows_access_for_cdp_cidr_port(
    azure_nsg_info: str,
    cdp_cidrs: List[str],
    nsg_type: str,
    protocol: str,
    port: int,
) -> None:
    """Check that the NSG allows a port to the CDP CIDRs."""
    access_not_allowed = []

    for cdp_cidr in cdp_cidrs:  # pylint: disable=too-many-nested-blocks
        port_allowed = False
        cdp_cidr_network = ipaddress.ip_network(cdp_cidr)
        for security_rule in azure_nsg_info.security_rules:
            if security_rule.direction == "Inbound" and security_rule.access == "Allow":
                if security_rule.source_address_prefix:
                    source_addresses_prefixes = [
                        ipaddress.ip_network(
                            "0.0.0.0/0"
                            if security_rule.source_address_prefix == "*"
                            else security_rule.source_address_prefix
                        )
                    ]
                else:
                    source_addresses_prefixes = [
                        ipaddress.ip_network(prefix)
                        for prefix in security_rule.source_address_prefixes
                    ]

                for source_address_network in source_addresses_prefixes:
                    if source_address_network.overlaps(cdp_cidr_network):

                        # dest ports open
                        dest_port_ranges = (
                            [security_rule.destination_port_range]
                            if security_rule.destination_port_range
                            else security_rule.destination_port_ranges
                        )

                        source_port_ranges = (
                            [security_rule.source_port_range]
                            if security_rule.source_port_range
                            else security_rule.source_port_ranges
                        )

                        if _do_ranges_cover_port(
                            dest_port_ranges, port
                        ) and _do_ranges_cover_all(source_port_ranges):
                            if (
                                security_rule.protocol == protocol
                                or security_rule.protocol == "*"
                            ):
                                port_allowed = True

        if not port_allowed:
            access_not_allowed.append(f"CDP CIDR: {cdp_cidr}")

    if access_not_allowed:
        fail(
            AZURE_CDP_CIDR_ACCESS_NOT_ALLOWED_FOR_PORT,
            [nsg_type, azure_nsg_info.name, protocol, port],
            access_not_allowed,
        )
