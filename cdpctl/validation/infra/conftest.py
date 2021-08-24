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
# Source File Name:  conftest.py
###
"""Fixtures for the AWS CDP bucket access policy."""
from typing import Dict, List

import pytest

from cdpctl.validation.azure_utils import read_azure_supported_regions


@pytest.fixture
def logs_needed_actions() -> List[str]:
    """Needed actions for the log storage path."""
    return ["s3:PutObject", "s3:AbortMultipartUpload", "s3:ListMultipartUploadParts"]


@pytest.fixture
def log_bucket_needed_actions() -> List[str]:
    """Needed actions for the log storage bucket."""
    return ["s3:ListBucket"]


@pytest.fixture
def ranger_audit_bucket_needed_actions() -> List[str]:
    """S3 location needed actions for ranger audit role."""
    return [
        "s3:AbortMultipartUpload",
        "s3:ListBucket",
        "s3:ListBucketMultipartUploads",
    ]


@pytest.fixture
def data_location_needed_actions() -> List[str]:
    """S3 location needed actions for ranger audit role."""
    return [
        "s3:GetAccelerateConfiguration",
        "s3:GetAnalyticsConfiguration",
        "s3:GetBucketAcl",
        "s3:GetBucketCORS",
        "s3:GetBucketLocation",
        "s3:GetBucketLogging",
        "s3:GetBucketNotification",
        "s3:GetBucketPolicy",
        "s3:GetBucketPolicyStatus",
        "s3:GetBucketPublicAccessBlock",
        "s3:GetBucketRequestPayment",
        "s3:GetBucketTagging",
        "s3:GetBucketVersioning",
        "s3:GetBucketWebsite",
        "s3:GetEncryptionConfiguration",
        "s3:GetInventoryConfiguration",
        "s3:GetLifecycleConfiguration",
        "s3:GetMetricsConfiguration",
        "s3:GetObject",
        "s3:GetObjectAcl",
        "s3:GetObjectTagging",
        "s3:GetObjectVersion",
        "s3:GetObjectVersionAcl",
        "s3:GetObjectVersionTagging",
        "s3:GetReplicationConfiguration",
        "s3:ListBucket",
        "s3:ListBucketMultipartUploads",
        "s3:ListMultipartUploadParts",
    ]


@pytest.fixture
def s3_needed_actions_to_all() -> List[str]:
    """S3 needed actions for ranger audit role."""
    return [
        "s3:CreateJob",
        "s3:GetAccountPublicAccessBlock",
        "s3:ListJobs",
    ]


@pytest.fixture
def ranger_audit_location_needed_actions() -> List[str]:
    """s3 needed actions for ranger audit role."""
    return ["s3:GetObject", "s3:PutObject"]


@pytest.fixture
def ec2_needed_actions() -> List[str]:
    """EC2 needed actions for cross account role."""
    return [
        "ec2:DeleteTags",
        "ec2:AssociateAddress",
        "ec2:StartInstances",
        "ec2:StopInstances",
        "ec2:AttachVolume",
        "ec2:ReleaseAddress",
        "ec2:DescribeAddresses",
        "ec2:TerminateInstances",
        "ec2:DeleteSecurityGroup",
    ]


@pytest.fixture
def autoscaling_resources_needed_actions() -> List[str]:
    """Autoscaling resources needed actions for cross account role."""
    return [
        "cloudformation:DeleteStack",
        "autoscaling:SuspendProcesses",
        "autoscaling:UpdateAutoScalingGroup",
        "autoscaling:ResumeProcesses",
        "autoscaling:DetachInstances",
        "autoscaling:DeleteAutoScalingGroup",
        "rds:StopDBInstance",
        "rds:StartDBInstance",
    ]


@pytest.fixture
def cloud_formation_needed_actions() -> List[str]:
    """Cloud Formation needed actions for cross account role."""
    return [
        "cloudformation:CreateStack",
        "cloudformation:GetTemplate",
        "ec2:CreateTags",
    ]


@pytest.fixture
def cdp_environment_resources_needed_actions() -> List[str]:
    """Environment needed actions for cross account role."""
    return [
        "ec2:DeleteVolume",
        "ec2:DeleteKeyPair",
        "ec2:DescribeKeyPairs",
        "ec2:DescribeAvailabilityZones",
        "ec2:DescribeImages",
        "ec2:DeleteLaunchTemplate",
        "ec2:DescribeVolumes",
        "ec2:CreateVolume",
        "ec2:DescribeInstances",
        "ec2:DescribeRegions",
        "ec2:DescribeInstanceTypeOfferings",
        "ec2:DescribeInstanceTypes",
        "ec2:DescribeRouteTables",
        "ec2:DescribeSecurityGroups",
        "ec2:DescribeSubnets",
        "ec2:DescribeVpcAttribute",
        "ec2:DescribeVpcs",
        "ec2:DescribeInternetGateways",
        "ec2:DescribeVpcEndpoints",
        "ec2:describeAddresses",
        "ec2:DescribeNatGateways",
        "ec2:DescribeVpcEndpointServices",
        "ec2:ModifySubnetAttribute",
        "ec2:ModifyVpcAttribute",
        "ec2:CreateVpc",
        "ec2:CreateNatGateway",
        "ec2:CreateRouteTable",
        "ec2:CreateSubnet",
        "ec2:CreateVpcEndpoint",
        "ec2:CreateInternetGateway",
        "ec2:DeleteSubnet",
        "ec2:DeleteInternetGateway",
        "ec2:AttachInternetGateway",
        "ec2:DetachInternetGateway",
        "ec2:DescribePrefixLists",
        "ec2:AllocateAddress",
        "ec2:AssociateRouteTable",
        "ec2:CreateRoute",
        "ec2:DeleteRouteTable",
        "ec2:DeleteVpcEndpoints",
        "ec2:DisassociateRouteTable",
        "ec2:ReleaseAddress",
        "ec2:DeleteRoute",
        "ec2:DeleteNatGateway",
        "ec2:DeleteVpc",
        "ec2:ImportKeyPair",
        "ec2:DescribeLaunchTemplates",
        "ec2:CreateSecurityGroup",
        "ec2:CreateLaunchTemplate",
        "ec2:RunInstances",
        "ec2:AuthorizeSecurityGroupIngress",
        "ec2:RevokeSecurityGroupEgress",
        "ec2:AuthorizeSecurityGroupEgress",
        "ec2:DescribeAccountAttributes",
        "sts:DecodeAuthorizationMessage",
        "cloudformation:DescribeStacks",
        "dynamodb:DeleteTable",
        "dynamodb:DescribeTable",
        "iam:ListInstanceProfiles",
        "iam:ListRoles",
        "dynamodb:ListTables",
        "autoscaling:DescribeAutoScalingGroups",
        "autoscaling:DescribeScalingActivities",
        "autoscaling:CreateAutoScalingGroup",
        "autoscaling:TerminateInstanceInAutoScalingGroup",
        "cloudwatch:DeleteAlarms",
        "cloudwatch:PutMetricAlarm",
        "cloudwatch:DescribeAlarms",
        "elasticloadbalancing:CreateLoadBalancer",
        "elasticloadbalancing:CreateTargetGroup",
        "elasticloadbalancing:DescribeLoadBalancers",
        "elasticloadbalancing:DescribeTargetGroups",
        "elasticloadbalancing:AddTags",
        "elasticloadbalancing:RegisterTargets",
        "elasticloadbalancing:DescribeTargetHealth",
        "elasticloadbalancing:DescribeListeners",
        "elasticloadbalancing:CreateListener",
        "elasticloadbalancing:DeleteListener",
        "elasticloadbalancing:DeleteTargetGroup",
        "elasticloadbalancing:DeleteLoadBalancer",
        "elasticloadbalancing:DeregisterTargets",
        "s3:GetBucketLocation",
        "cloudformation:DescribeStackEvents",
        "cloudformation:DescribeStackResources",
        "cloudformation:DescribeStackResource",
        "cloudformation:ListStackResources",
        "cloudformation:UpdateStack",
        "cloudformation:GetTemplate",
        "iam:GetInstanceProfile",
        "iam:SimulatePrincipalPolicy",
        "iam:GetRole",
        "rds:AddTagsToResource",
        "rds:CreateDBInstance",
        "rds:CreateDBSubnetGroup",
        "rds:DeleteDBInstance",
        "rds:DeleteDBSubnetGroup",
        "rds:ListTagsForResource",
        "rds:RemoveTagsFromResource",
        "rds:CreateDBParameterGroup",
        "rds:DeleteDBParameterGroup",
        "rds:DescribeEngineDefaultParameters",
        "rds:ModifyDBParameterGroup",
        "rds:DescribeDBParameters",
        "rds:DescribeDBParameterGroups",
        "rds:DescribeDBSubnetGroups",
        "rds:DescribeDBInstances",
        "rds:ModifyDBInstance",
        "rds:DescribeCertificates",
        "kms:ListKeys",
        "kms:ListAliases",
        "ec2:ModifyInstanceAttribute",
        "ec2:CreateLaunchTemplateVersion",
    ]


@pytest.fixture
def pass_role_needed_actions() -> List[str]:
    """Pass role needed actions for cross account role."""
    return ["iam:PassRole"]


@pytest.fixture
def identity_management_needed_actions() -> List[str]:
    """Indentity management needed actions for cross account role."""
    return ["iam:CreateServiceLinkedRole"]


@pytest.fixture
def cdp_cidrs() -> List[str]:
    """Get the CDP control plane CIDRs."""
    return ["52.36.110.208/32", "52.40.165.49/32", "35.166.86.177/32"]


@pytest.fixture
def azure_supported_regions() -> List[str]:
    """Get the Azure regions supported by CDP."""
    base_regions, _ = read_azure_supported_regions()
    return base_regions


@pytest.fixture
def azure_supported_region_experiences() -> Dict[str, bool]:
    """Get the Azure regions supported by CDP."""
    _, region_features = read_azure_supported_regions()
    return region_features
