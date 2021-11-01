import os
from typing import Any, Dict, List

import boto3
import click
from boto3_type_annotations.ec2 import Client as Ec2Client
from boto3_type_annotations.ec2 import Vpc
from boto3_type_annotations.ec2.service_resource import (
    KeyPair,
    SecurityGroup,
    Subnet,
    security_groups,
)

import cdpctl
from cdpctl.utils import load_config


def prompt_for_aws_config(generation_info: Dict[str, Any]) -> Dict[str, Any]:
    aws_info = load_aws_supported_info()

    # get the Profile
    profile = click.prompt(
        "\nWhat Network type do you want to create?",
        type=click.Choice(cdpctl.SUPPPOTED_NETWORK_TYPES, case_sensitive=True),
    )
    generation_info["network_type"] = profile

    # get the Profile
    profile = click.prompt(
        "\nWhat AWS profile do you want to use?",
        type=click.Choice(
            boto3.session.Session().available_profiles, case_sensitive=True
        ),
    )
    generation_info["infra:aws:profile"] = profile

    # Get the Region
    generation_info["infra:aws:region"] = click.prompt(
        "\nWhat AWS region will be default?",
        type=click.Choice(aws_info["regions"], case_sensitive=True),
    )

    # Get the VPC Name
    vpc_list = get_vpcs(
        profile=profile, region_name=generation_info["infra:aws:region"]
    )
    vpc_entered = "__show__"
    while vpc_entered == "__show__":
        vpc_entered = click.prompt(
            "\nWhat is the name of the Network (VPC)?\n"
            + click.style(
                f"Enter l or list to see a list of current VPC in {generation_info['infra:aws:region']}",
                fg="green",
            ),
            type=str,
            default="__show__",
            show_default=False,
        )
        if vpc_entered == "__show__" or vpc_entered.lower() == "l":
            vpc_entered = "__show__"
            for vpc in vpc_list:
                click.secho(f"- {vpc['name']}", fg="blue")
        else:
            selected_vpc = [vpc for vpc in vpc_list if vpc["name"] == vpc_entered][0]

    generation_info["infra:aws:vpc:existing:vpc_id"] = selected_vpc["id"]
    generation_info["infra:aws:vpc:existing:vpc_name"] = selected_vpc["name"]

    existing_subnet_list = get_subets(
        profile=profile,
        region_name=generation_info["infra:aws:region"],
        vpc=selected_vpc["id"],
    )

    # Get the Private Subnets
    subnets = []
    while True:
        prompt_text = "\nWhats Private Subnets do you want to use?\n"
        if subnets:
            prompt_text += click.style("Currently selected subnets:\n", fg="red")
            for subnet in subnets:
                prompt_text += click.style(f"- {subnet['name']}\n", fg="red")
            prompt_text += click.style(
                "Hit enter to stop adding subnets.\n", fg="green"
            )
        prompt_text += click.style(
            f"Enter l or list to see a list of the current subnets for VPC {vpc_entered}",
            fg="green",
        )

        subnet_entered = click.prompt(
            prompt_text,
            type=str,
            default="__done__",
            show_default=False,
        )
        if subnet_entered == "list" or subnet_entered == "l":
            for subnet in existing_subnet_list:
                click.secho(f"- {subnet['name']}", fg="blue")
        elif subnet_entered == "__done__":
            if subnets:
                break
        else:
            to_add = [
                subnet
                for subnet in existing_subnet_list
                if subnet["name"] == subnet_entered
            ]
            if to_add:
                subnets.append(to_add[0])
            subnets = [dict(t) for t in {tuple(d.items()) for d in subnets}]
    generation_info["infra:aws:vpc:existing:private_subnet_ids"] = subnets

    # Get the Public Subnets
    subnets = []
    while True:
        prompt_text = "\nWhats Public Subnets do you want to use?\n"
        if subnets:
            prompt_text += click.style("Currently selected subnets:\n", fg="red")
            for subnet in subnets:
                prompt_text += click.style(f"- {subnet['name']}\n", fg="red")
            prompt_text += click.style(
                "Hit enter to stop adding subnets.\n", fg="green"
            )
        prompt_text += click.style(
            f"Enter l or list to see a list of the current subnets for VPC {vpc_entered}",
            fg="green",
        )

        subnet_entered = click.prompt(
            prompt_text,
            type=str,
            default="__done__",
            show_default=False,
        )
        if subnet_entered == "list" or subnet_entered == "l":
            for subnet in existing_subnet_list:
                click.secho(f"- {subnet['name']}", fg="blue")
        elif subnet_entered == "__done__":
            if subnets:
                break
        else:
            to_add = [
                subnet
                for subnet in existing_subnet_list
                if subnet["name"] == subnet_entered
            ]
            if to_add:
                subnets.append(to_add[0])
            subnets = [dict(t) for t in {tuple(d.items()) for d in subnets}]
    generation_info["infra:aws:vpc:existing:public_subnet_ids"] = subnets

    ## Roles and Buckets
    generation_info["env:aws:policy:role:name:cross_account"] = click.prompt(
        "\nWhat is the name of the Cross Account Role?", type=str
    )
    generation_info["env:aws:policy:role:name:datalake_admin"] = click.prompt(
        "\nWhat is the name of the Data Access Role?", type=str
    )
    generation_info["infra:storage:path:data"] = click.prompt(
        "\nWhat is the AWS S3 path to Storage Location Base?\n"
        + click.style("Please use s3a format: s3a://bucket-name/path", fg="green"),
        type=str,
    )
    generation_info["env:aws:policy:role:name:log"] = click.prompt(
        "\nWhat is the name of the Logger Instance Profile?", type=str
    )
    generation_info["infra:storage:path:logs"] = click.prompt(
        "\nWhat is the AWS S3 path for the Logs Location Base\n"
        + click.style("Please use s3a format: s3a://bucket-name/path", fg="green"),
        type=str,
    )
    generation_info["env:aws:policy:role:name:idbroker"] = click.prompt(
        "\nWhat is the name of the Assumer Instance Profile?", type=str
    )
    generation_info["env:aws:policy:role:name:ranger_audit"] = click.prompt(
        "\nWhat is the name of the Ranger Audit Role?", type=str
    )
    generation_info["infra:storage:path:ranger_audit"] = click.prompt(
        "\nWhat is the AWS S3 path to store the Ranger Audit information?\n"
        + click.style("Please use s3a format: s3a://bucket-name/path", fg="green"),
        type=str,
    )

    # Get the VPC Name
    security_group_list = get_security_groups(
        profile=profile,
        region_name=generation_info["infra:aws:region"],
        vpc=selected_vpc["id"],
    )

    keys = get_key_pairs(
        profile=profile,
        region_name=generation_info["infra:aws:region"],
    )

    generation_info["infra:aws:vpc:existing:vpc_id"] = selected_vpc["id"]
    generation_info["infra:aws:vpc:existing:vpc_name"] = selected_vpc["name"]

    generation_info["infra:aws:vpc:existing:security_groups:default_id"] = click.prompt(
        "\nWhat is the name of Default Security Group?", type=str
    )
    generation_info["infra:aws:vpc:existing:security_groups:knox_id"] = click.prompt(
        "\nWhat is the name of default Gateway Nodes Security Group?", type=str
    )

    return generation_info


def load_aws_supported_info() -> Dict[str, Any]:
    return load_config(
        os.path.join(os.path.dirname(cdpctl.__file__), "resources", "aws_supported.yml")
    )


def get_vpcs(profile: str, region_name: str):
    session = boto3.Session(profile_name=profile)
    client: Ec2Client = session.client("ec2", region_name=region_name)
    response = client.describe_vpcs()
    resp: List[Vpc] = response["Vpcs"]
    vpcs: List[Dict[str, Any]] = []
    if resp:
        for vpc in resp:
            if "Tags" in vpc:
                for tag in vpc["Tags"]:
                    if tag["Key"] == "Name":
                        vpcs.append({"id": vpc["VpcId"], "name": tag["Value"]})
                        break
            else:
                vpcs.append({"id": vpc["VpcId"], "name": vpc["VpcId"]})
    vpcs = sorted(vpcs, key=lambda i: i["name"])
    return vpcs


def get_subets(profile: str, region_name: str, vpc: str):
    session = boto3.Session(profile_name=profile)
    client: Ec2Client = session.client("ec2", region_name=region_name)
    response = client.describe_subnets(Filters=[{"Name": "vpc-id", "Values": [vpc]}])
    resp: List[Subnet] = response["Subnets"]
    subnets: List[str] = []
    if resp:
        for subnet in resp:
            if "Tags" in subnet:
                for tag in subnet["Tags"]:
                    if tag["Key"] == "Name":
                        subnets.append({"id": subnet["SubnetId"], "name": tag["Value"]})
                        break
            else:
                subnets.append({"id": subnet["SubnetId"], "name": subnet["SubnetId"]})
    return sorted(subnets, key=lambda i: i["name"])


def get_security_groups(profile: str, region_name: str, vpc: str):
    session = boto3.Session(profile_name=profile)
    client: Ec2Client = session.client("ec2", region_name=region_name)
    response = client.describe_security_groups(
        Filters=[{"Name": "vpc-id", "Values": [vpc]}]
    )
    resp: List[SecurityGroup] = response["SecurityGroups"]
    subnets: List[str] = []
    if resp:
        for group in resp:
            subnets.append({"id": group["GroupId"], "name": group["GroupName"]})
    return sorted(subnets, key=lambda i: i["name"])


def get_key_pairs(profile: str, region_name: str):
    session = boto3.Session(profile_name=profile)
    client: Ec2Client = session.client("ec2", region_name=region_name)
    response = client.describe_key_pairs()
    resp: List[str] = response["KeyPairs"]
    keys: List[str] = []
    if resp:
        for key in resp:
            keys.append(key["KeyName"])
    return sorted(keys)
