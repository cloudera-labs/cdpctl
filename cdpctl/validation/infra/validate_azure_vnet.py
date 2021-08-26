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
# Source File
"""Azure VNet Validations."""

import ipaddress
from typing import Any, Dict

import pytest
from azure.core.exceptions import ResourceNotFoundError
from azure.mgmt.network import NetworkManagementClient

from cdpctl.validation import fail, get_config_value, validator, warn
from cdpctl.validation.azure_utils import get_client
from cdpctl.validation.infra.issues import (
    AZURE_VNET_ADDRESS_SPACE_HAS_PUBLIC_CIDRS,
    AZURE_VNET_ADDRESS_SPACE_OVERLAPS_RESERVED,
    AZURE_VNET_AT_LEAST_ONE_SUBNET_NEEDED,
    AZURE_VNET_NO_SUBNET_WITH_NETAPP_DELEGATION_FOR_ML,
    AZURE_VNET_NOT_ENOUGH_DW_SIZED_SUBNETS,
    AZURE_VNET_NOT_ENOUGH_DW_SUBNETS,
    AZURE_VNET_NOT_FOUND,
    AZURE_VNET_SHOULD_HAVE_CLASS_B_TOTAL_ADDRESSES,
    AZURE_VNET_SUBNET_DOES_NOT_HAVE_SUBNETS_FOR_DE,
    AZURE_VNET_SUBNET_DOES_NOT_HAVE_SUBNETS_FOR_WORKSPACES_IN_ML,
    AZURE_VNET_SUBNET_NEEDS_CLASS_C_FOR_DLDH,
    AZURE_VNET_SUBNET_WITH_NETAPP_DELEGATION_NOT_SIZED_FOR_ML,
)

_vnet_info = {}


@pytest.fixture(name="vnet_info")
def vnet_info_fixture():
    """Get the Virtual Network info set."""
    return _vnet_info["vnet"]


vnet_reserved_ip_cidrs = [
    ipaddress.ip_network("10.0.0.0/16"),
    ipaddress.ip_network("10.244.0.0/16"),
    ipaddress.ip_network("172.17.0.0/16"),
    ipaddress.ip_network("10.20.0.0/16"),
    ipaddress.ip_network("10.244.0.0/16"),
]


@pytest.fixture(name="vnet_reserved_ip_networks")
def vnet_reserved_ip_networks_fixture():
    """Provide the reserved CIDRs."""
    return vnet_reserved_ip_cidrs


@pytest.fixture(autouse=True, name="azure_network_client")
def azure_network_client_fixture(config: Dict[str, Any]) -> NetworkManagementClient:
    """Return an Azure Client."""
    return get_client("network", config)


# @pytest.mark.dependency(
#     depends=[
#         "infra/validate_azure_region.py::azure_region_validation",
#     ],
#     scope="session",
# )
@pytest.mark.azure
@pytest.mark.infra
def azure_vnet_exists_validation(
    config: Dict[str, Any], azure_network_client: NetworkManagementClient
) -> None:  # pragma: no cover
    """Virtual Network exists."""  # noqa: D401
    azure_vnet_exists(config, azure_network_client)


@validator
def azure_vnet_exists(
    config: Dict[str, Any], azure_network_client: NetworkManagementClient
) -> None:  # pragma: no cover
    """Check that the VNet exists."""  # noqa: D401,E501
    vnet_name: str = get_config_value(config=config, key="infra:vpc:name")
    resource_group_name: str = get_config_value(
        config=config, key="infra:azure:metagroup:name"
    )
    try:
        _vnet_info["vnet"] = azure_network_client.virtual_networks.get(
            virtual_network_name=vnet_name, resource_group_name=resource_group_name
        )
    except ResourceNotFoundError:
        fail(AZURE_VNET_NOT_FOUND, [vnet_name, resource_group_name])


@pytest.mark.azure
@pytest.mark.infra
@pytest.mark.dependency(depends=["azure_vnet_exists_validation"])
def azure_vnet_cidr_range_validation(vnet_info) -> None:  # pragma: no cover
    """Virtual Network has enough IP addresses."""  # noqa: D401
    azure_vnet_cidr_range(vnet_info)


@validator
def azure_vnet_cidr_range(vnet_info) -> None:  # pragma: no cover
    """Check that the VNet has enough IPs."""  # noqa: D401,E501
    total_ips = 0

    for address_prefix in vnet_info.address_space.address_prefixes:
        ip_net = ipaddress.ip_network(address_prefix)
        total_ips += ip_net.num_addresses

    if total_ips < 65536:
        fail(
            AZURE_VNET_SHOULD_HAVE_CLASS_B_TOTAL_ADDRESSES, [vnet_info.name, total_ips]
        )


@pytest.mark.azure
@pytest.mark.infra
@pytest.mark.dependency(depends=["azure_vnet_exists_validation"])
def azure_vnet_cidr_range_private_validation(vnet_info) -> None:  # pragma: no cover
    """Virtual Network address space is not public IP address ranges."""  # noqa: D401
    azure_vnet_cidr_range_private(vnet_info)


@validator
def azure_vnet_cidr_range_private(vnet_info) -> None:  # pragma: no cover
    """Check that the VNet is only private ip space."""  # noqa: D401,E501

    public_cidrs = []
    for address_prefix in vnet_info.address_space.address_prefixes:
        ip_net = ipaddress.ip_network(address_prefix)
        if not ip_net.is_private:
            public_cidrs.append(ip_net.with_prefixlen)

    if public_cidrs:
        fail(AZURE_VNET_ADDRESS_SPACE_HAS_PUBLIC_CIDRS, [vnet_info.name], public_cidrs)


@pytest.mark.azure
@pytest.mark.infra
@pytest.mark.dependency(depends=["azure_vnet_exists_validation"])
def azure_vnet_cidr_ranges_not_reserved_validation(
    vnet_info, vnet_reserved_ip_networks
) -> None:  # pragma: no cover
    """Virtual Network address space is not reserved."""  # noqa: D401
    azure_vnet_cidr_ranges_not_reserved(vnet_info, vnet_reserved_ip_networks)


@validator
def azure_vnet_cidr_ranges_not_reserved(
    vnet_info, vnet_reserved_ip_networks
) -> None:  # pragma: no cover
    """Check that the VNet does not use reserved addresses."""  # noqa: D401,E501
    colliding_networks = []
    for address_prefix in vnet_info.address_space.address_prefixes:
        ip_net = ipaddress.ip_network(address_prefix)
        for reserved_net in vnet_reserved_ip_networks:
            if ip_net.overlaps(reserved_net):
                colliding_networks.append(reserved_net.with_prefixlen)

    if colliding_networks:
        fail(
            AZURE_VNET_ADDRESS_SPACE_OVERLAPS_RESERVED,
            [vnet_info.name],
            colliding_networks,
        )


@pytest.mark.azure
@pytest.mark.infra
@pytest.mark.dependency(depends=["azure_vnet_exists_validation"])
def azure_vnet_subnets_count_validation(vnet_info) -> None:  # pragma: no cover
    """Virtual Network has the needed number of Subnets."""  # noqa: D401
    azure_vnet_subnets_count(vnet_info)


@validator
def azure_vnet_subnets_count(vnet_info) -> None:  # pragma: no cover
    """Check that the VNet has the needed number of subnets."""  # noqa: D401,E501
    if not vnet_info.subnets:
        fail(AZURE_VNET_AT_LEAST_ONE_SUBNET_NEEDED, vnet_info.name)


@pytest.mark.azure
@pytest.mark.infra
@pytest.mark.dependency(depends=["azure_vnet_subnets_count_validation"])
def azure_vnet_subnets_range_for_dl_and_dh_validation(
    vnet_info,
) -> None:  # pragma: no cover
    """Virtual Network has a Subnet with an address range for Datalake and DataHub."""  # noqa: D401,E501
    azure_vnet_subnets_range_for_dl_and_dh(vnet_info)


@validator
def azure_vnet_subnets_range_for_dl_and_dh(vnet_info) -> None:  # pragma: no cover
    """Check that the VNet a /24 for the DL and DH."""  # noqa: D401,E501
    found_compatabile_subnet = False
    for subnet in vnet_info.subnets:
        if ipaddress.ip_network(subnet.address_prefix).prefixlen <= 24:
            found_compatabile_subnet = True

    if not found_compatabile_subnet:
        fail(AZURE_VNET_SUBNET_NEEDS_CLASS_C_FOR_DLDH, vnet_info.name)


@pytest.mark.azure
@pytest.mark.infra
@pytest.mark.dependency(depends=["azure_vnet_subnets_count_validation"])
def azure_vnet_subnets_range_for_dw_validation(
    vnet_info,
) -> None:  # pragma: no cover
    """Virtual Network has Subnets and address ranges for Data Warehouse."""  # noqa: D401,E501
    azure_vnet_subnets_range_for_dw(vnet_info)


@validator
def azure_vnet_subnets_range_for_dw(vnet_info) -> None:  # pragma: no cover
    """Check that the VNet has subnets for DW."""  # noqa: D401,E501
    dw_size_subnets = 0
    for subnet in vnet_info.subnets:
        if ipaddress.ip_network(subnet.address_prefix).prefixlen <= 20:
            dw_size_subnets += 1

    if dw_size_subnets < 3:
        warn(AZURE_VNET_NOT_ENOUGH_DW_SIZED_SUBNETS, vnet_info.name)

    if len(vnet_info.subnets) < 4:
        warn(AZURE_VNET_NOT_ENOUGH_DW_SUBNETS, vnet_info.name)


@pytest.mark.azure
@pytest.mark.infra
@pytest.mark.dependency(depends=["azure_vnet_subnets_count_validation"])
def azure_vnet_subnets_for_ml_validation(
    vnet_info,
) -> None:  # pragma: no cover
    """Virtual Network has Subnets and address ranges for Machine Learning."""  # noqa: D401,E501
    azure_vnet_subnets_for_ml(vnet_info)


@validator
def azure_vnet_subnets_for_ml(vnet_info) -> None:  # pragma: no cover
    """Check that the VNet has subnets and delegation for ML."""  # noqa: D401,E501

    netapp_delegation_subnets = []
    for subnet in vnet_info.subnets:
        for delegation in subnet.delegations:
            if delegation.service_name == "Microsoft.Netapp/volumes":
                netapp_delegation_subnets.append(subnet)
    if netapp_delegation_subnets:
        properly_sized_netapp_networks = False
        for subnet in netapp_delegation_subnets:
            if ipaddress.ip_network(subnet.address_prefix).prefixlen <= 28:
                properly_sized_netapp_networks = True
        if not properly_sized_netapp_networks:
            warn(
                AZURE_VNET_SUBNET_WITH_NETAPP_DELEGATION_NOT_SIZED_FOR_ML,
                vnet_info.name,
            )
    else:
        warn(AZURE_VNET_NO_SUBNET_WITH_NETAPP_DELEGATION_FOR_ML, vnet_info.name)

    compatable_subnets = 0
    for subnet in vnet_info.subnets:
        if ipaddress.ip_network(subnet.address_prefix).prefixlen <= 25:
            compatable_subnets += 1
    # must have at least a DLDH subnet and 1 more
    if not compatable_subnets > 2:
        warn(
            AZURE_VNET_SUBNET_DOES_NOT_HAVE_SUBNETS_FOR_WORKSPACES_IN_ML, vnet_info.name
        )


@pytest.mark.azure
@pytest.mark.infra
@pytest.mark.dependency(depends=["azure_vnet_subnets_count_validation"])
def azure_vnet_subnets_for_de_validation(
    vnet_info,
) -> None:  # pragma: no cover
    """Virtual Network has Subnets and address ranges for Data Engineering."""  # noqa: D401,E501
    azure_vnet_subnets_for_de(vnet_info)


@validator
def azure_vnet_subnets_for_de(vnet_info) -> None:  # pragma: no cover
    """Check that the VNet has enough /24 subnets for DE."""  # noqa: D401,E501
    compatable_subnets = 0
    for subnet in vnet_info.subnets:
        if ipaddress.ip_network(subnet.address_prefix).prefixlen <= 24:
            compatable_subnets += 1
    # must have at least a DLDH subnet and 1 more
    if not compatable_subnets >= 2:
        warn(AZURE_VNET_SUBNET_DOES_NOT_HAVE_SUBNETS_FOR_DE, vnet_info.name)
