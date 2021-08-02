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
# Source File Name:  validate.py
###
"""Validate Command Implementation."""

import os
import sys

import click
import pytest

import cdpctl.validation as validation
from cdpctl import SUPPORTED_PLATFORMS, Command
from cdpctl.utils import load_config
from cdpctl.validation import UnrecoverableValidationError, conftest
from cdpctl.validation.aws_utils import validate_aws_config


class ValidateCommand(Command):
    """The Validate command."""

    def run(self, target: str, config_file: str) -> None:
        """Run the validate command."""
        click.echo(
            f"Targeting {click.style(target, fg='blue')} section with config file "
            f"{click.style(click.format_filename(config_file), fg='green')}\n"
        )

        conftest.config_file = config_file  # type: ignore[attr-defined]
        try:
            config = load_config(config_file=config_file)
        except FileExistsError:
            click.secho(
                f"Error: the config file {click.format_filename(config_file)} "
                "does not exist.",
                fg="red",
            )
            sys.exit(1)

        infra_type = config["infra_type"]
        if not infra_type or infra_type not in SUPPORTED_PLATFORMS:
            click.secho(
                "No supported platform defined for "
                f"{click.style('infra_type', fg='green')}",
                fg="red",
            )
            click.secho(
                "The following platforms are supported: "
                f"{click.style(', '.join(SUPPORTED_PLATFORMS), fg='blue')}",
                fg="red",
            )
            sys.exit(1)

        try:
            if infra_type == "aws":
                validate_aws_config(config=config)
        except UnrecoverableValidationError as e:
            click.secho(e, fg="red")
            sys.exit(1)

        click.secho("Validating:", fg="blue")

        validation_root_path = os.path.dirname(validation.__file__)
        validation_ini_path = os.path.join(validation_root_path, "validation.ini")
        pytest.main(
            [
                f"{validation_root_path}",
                "--no-header",
                "--no-summary",
                "-qq",
                "-s",
                "-m",
                f"{infra_type} and {target}",
                "-c",
                f"{validation_ini_path}",
                "--order-dependencies",
            ]
        )
