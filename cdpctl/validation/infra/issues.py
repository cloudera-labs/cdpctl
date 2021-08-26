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
# Source File Name: issues.py
###
# flake8: noqa
# pylint: skip-file

# THIS FILE IS GENERATED. DO NOT UPDATE BY HAND.
# Use the update_issue_templates.py script
"""Issue Templates."""

AWS_CROSS_ACCOUNT_ROLE_MISSING = "AWS_CROSS_ACCOUNT_ROLE_MISSING"

AWS_ACCOUNT_ID_NOT_IN_CROSS_ACCOUNT_ROLE = "AWS_ACCOUNT_ID_NOT_IN_CROSS_ACCOUNT_ROLE"

AWS_EXTERNAL_ID_NOT_IN_CROSS_ACCOUNT_ROLE = "AWS_EXTERNAL_ID_NOT_IN_CROSS_ACCOUNT_ROLE"

AWS_IDBROKER_INSTANCE_PROLFILE_NEEDS_ROLE = "AWS_IDBROKER_INSTANCE_PROLFILE_NEEDS_ROLE"

AWS_IDBROKER_ROLE_NEED_EC2_TRUST_POLICY = "AWS_IDBROKER_ROLE_NEED_EC2_TRUST_POLICY"

AWS_ROLE_FOR_DL_BUCKET_MISSING_ACTIONS = "AWS_ROLE_FOR_DL_BUCKET_MISSING_ACTIONS"

AWS_ROLE_REQUIRES_ACTIONS_FOR_ALL_S3_RESOURCES = "AWS_ROLE_REQUIRES_ACTIONS_FOR_ALL_S3_RESOURCES"

AWS_ROLE_FOR_DATA_BUCKET_MISSING_ACTIONS = "AWS_ROLE_FOR_DATA_BUCKET_MISSING_ACTIONS"

AWS_IDBROKER_ROLE_REQUIRES_ACTIONS_FOR_ALL_RESOURCES = "AWS_IDBROKER_ROLE_REQUIRES_ACTIONS_FOR_ALL_RESOURCES"

AWS_ROLE_REQUIRES_ACTIONS_FOR_ALL_EC2_RESOURCES = "AWS_ROLE_REQUIRES_ACTIONS_FOR_ALL_EC2_RESOURCES"

AWS_ROLE_REQUIRES_ACTIONS_FOR_ALL_RESOURCES = "AWS_ROLE_REQUIRES_ACTIONS_FOR_ALL_RESOURCES"

AWS_ROLE_REQUIRES_ACTIONS_FOR_SERVICE_ROLL_RESOURCES = "AWS_ROLE_REQUIRES_ACTIONS_FOR_SERVICE_ROLL_RESOURCES"

AWS_ROLE_REQUIRES_ACTIONS_FOR_LOG_PATH = "AWS_ROLE_REQUIRES_ACTIONS_FOR_LOG_PATH"

AWS_ROLE_REQUIRES_ACTIONS_FOR_LOG_BUCKET = "AWS_ROLE_REQUIRES_ACTIONS_FOR_LOG_BUCKET"

AWS_LOGGER_INSTANCE_PROFILE_SHOULD_CONTAIN_LOGGER_ROLE = "AWS_LOGGER_INSTANCE_PROFILE_SHOULD_CONTAIN_LOGGER_ROLE"

AWS_LOGGER_ROLE_SHOULD_HAVE_EC2_TRUST = "AWS_LOGGER_ROLE_SHOULD_HAVE_EC2_TRUST"

AWS_S3_BUCKET_INVALID = "AWS_S3_BUCKET_INVALID"

AWS_S3_BUCKET_DOES_NOT_EXIST = "AWS_S3_BUCKET_DOES_NOT_EXIST"

AWS_S3_BUCKET_FORBIDDEN_ACCESS = "AWS_S3_BUCKET_FORBIDDEN_ACCESS"

AWS_NON_CCM_DEFAULT_SG_NEEDS_TO_ALLOW_CDP_CIDRS = "AWS_NON_CCM_DEFAULT_SG_NEEDS_TO_ALLOW_CDP_CIDRS"

AWS_NON_CCM_GATEWAY_SG_MISSING_CIDRS = "AWS_NON_CCM_GATEWAY_SG_MISSING_CIDRS"

AWS_DEFAULT_SG_NEEDS_ALLOW_ACCESS_INTERNAL_TO_VPC = "AWS_DEFAULT_SG_NEEDS_ALLOW_ACCESS_INTERNAL_TO_VPC"

AWS_GATEWAY_SG_NEEDS_ALLOW_ACCESS_INTERNAL_TO_VPC = "AWS_GATEWAY_SG_NEEDS_ALLOW_ACCESS_INTERNAL_TO_VPC"

AWS_SSH_KEY_ID_DOES_NOT_EXIST = "AWS_SSH_KEY_ID_DOES_NOT_EXIST"

AWS_SSH_IS_INVALID = "AWS_SSH_IS_INVALID"

AWS_NOT_ENOUGH_SUBNETS_PROVIDED = "AWS_NOT_ENOUGH_SUBNETS_PROVIDED"

AWS_INVALID_SUBNET_ID = "AWS_INVALID_SUBNET_ID"

AWS_REQUIRED_DATA_MISSING = "AWS_REQUIRED_DATA_MISSING"

AWS_INVALID_DATA = "AWS_INVALID_DATA"

AWS_SUBNETS_DO_NOT_EXIST = "AWS_SUBNETS_DO_NOT_EXIST"

AWS_NOT_ENOUGH_AZ_FOR_SUBNETS = "AWS_NOT_ENOUGH_AZ_FOR_SUBNETS"

AWS_SUBNETS_WITHOUT_INTERNET_GATEWAY = "AWS_SUBNETS_WITHOUT_INTERNET_GATEWAY"

AWS_SUBNETS_OR_VPC_WITHOUT_INTERNET_GATEWAY = "AWS_SUBNETS_OR_VPC_WITHOUT_INTERNET_GATEWAY"

AWS_SUBNETS_WITHOUT_VALID_RANGE = "AWS_SUBNETS_WITHOUT_VALID_RANGE"

AWS_SUBNETS_MISSING_K8S_LB_TAG = "AWS_SUBNETS_MISSING_K8S_LB_TAG"

AWS_SUBNETS_NOT_PART_OF_VPC = "AWS_SUBNETS_NOT_PART_OF_VPC"

AWS_DNS_SUPPORT_NOT_ENABLED_FOR_VPC = "AWS_DNS_SUPPORT_NOT_ENABLED_FOR_VPC"

AWS_VPC_NOT_FOUND_IN_ACCOUNT = "AWS_VPC_NOT_FOUND_IN_ACCOUNT"

AZURE_REGION_NOT_SUPPORTED = "AZURE_REGION_NOT_SUPPORTED"

AZURE_REGION_FEATURES_NOT_SUPPORTED = "AZURE_REGION_FEATURES_NOT_SUPPORTED"

AZURE_VNET_NOT_FOUND = "AZURE_VNET_NOT_FOUND"

AZURE_VNET_AT_LEAST_ONE_SUBNET_NEEDED = "AZURE_VNET_AT_LEAST_ONE_SUBNET_NEEDED"

AZURE_VNET_SHOULD_HAVE_CLASS_B_TOTAL_ADDRESSES = "AZURE_VNET_SHOULD_HAVE_CLASS_B_TOTAL_ADDRESSES"

AZURE_VNET_ADDRESS_SPACE_OVERLAPS_RESERVED = "AZURE_VNET_ADDRESS_SPACE_OVERLAPS_RESERVED"

AZURE_VNET_ADDRESS_SPACE_HAS_PUBLIC_CIDRS = "AZURE_VNET_ADDRESS_SPACE_HAS_PUBLIC_CIDRS"

AZURE_VNET_SUBNET_NEEDS_CLASS_C_FOR_DLDH = "AZURE_VNET_SUBNET_NEEDS_CLASS_C_FOR_DLDH"

AZURE_VNET_SUBNET_NEEDS_CLASS_C_FOR_DLDH = "AZURE_VNET_SUBNET_NEEDS_CLASS_C_FOR_DLDH"

AZURE_VNET_NOT_ENOUGH_DW_SIZED_SUBNETS = "AZURE_VNET_NOT_ENOUGH_DW_SIZED_SUBNETS"

AZURE_VNET_NOT_ENOUGH_DW_SUBNETS = "AZURE_VNET_NOT_ENOUGH_DW_SUBNETS"

AZURE_VNET_NO_SUBNET_WITH_NETAPP_DELEGATION_FOR_ML = "AZURE_VNET_NO_SUBNET_WITH_NETAPP_DELEGATION_FOR_ML"

AZURE_VNET_SUBNET_WITH_NETAPP_DELEGATION_NOT_SIZED_FOR_ML = "AZURE_VNET_SUBNET_WITH_NETAPP_DELEGATION_NOT_SIZED_FOR_ML"

AZURE_VNET_SUBNET_DOES_NOT_HAVE_SUBNETS_FOR_WORKSPACES_IN_ML = "AZURE_VNET_SUBNET_DOES_NOT_HAVE_SUBNETS_FOR_WORKSPACES_IN_ML"

AZURE_VNET_SUBNET_DOES_NOT_HAVE_SUBNETS_FOR_DE = "AZURE_VNET_SUBNET_DOES_NOT_HAVE_SUBNETS_FOR_DE"
