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
# Source File Name:  cli.py
###
"""CDP Control."""

import sys

import click

from cdpctl import SUPPORTED_TARGETS
from cdpctl.__version__ import __version__
from cdpctl.command.config import render_skeleton
from cdpctl.command.validate import run_validation

SUPPORTED_OUTPUT_TYPES = ["text", "json"]


@click.group(invoke_without_command=True)
@click.option("-q", "--quiet", is_flag=True, default=False)
@click.option("--debug/--no-debug", default=False)
@click.option("-v", "--version", is_flag=True, default=False)
@click.pass_context
def _cli(ctx, debug=False, version=False, quiet=False) -> None:
    """Run the cli."""
    ctx.ensure_object(dict)
    ctx.obj["DEBUG"] = debug
    ctx.obj["QUIET"] = quiet
    if version:
        print_version()
    if ctx.invoked_subcommand is None:
        click.echo(_cli.get_help(ctx))
        sys.exit(0)


@click.command()
@click.pass_context
@click.argument("target", type=click.Choice(SUPPORTED_TARGETS, case_sensitive=False))
@click.option(
    "-c",
    "--config_file",
    "config_file",
    default="config.yml",
    help="The config file to use. Defaults to config.yml.",
    type=click.Path(exists=False),
)
@click.option(
    "-o",
    "--output_file",
    default="-",
    help="The file to output the results to. Defaults to stdout.",
    type=click.Path(exists=False),
)
@click.option(
    "-f",
    "--output_format",
    default="text",
    help="The format to output the results as.",
    type=click.Choice(SUPPORTED_OUTPUT_TYPES, case_sensitive=False),
)
def validate(
    ctx, target: str, config_file, output_file, output_format
) -> None:  # pylint: disable=unused-argument
    """Run validation checks on provided section."""
    run_validation(
        target=target,
        config_file=config_file,
        debug=ctx.obj["DEBUG"],
        output_format=output_format,
        output_file=output_file,
    )


@click.group()
def config() -> None:
    """Works with the configuration."""
    pass


@click.command()
@click.option(
    "-o",
    "--output_file",
    default="-",
    help="The config file to output. Defaults to stdout.",
    type=click.Path(exists=False),
)
def skeleton(output_file) -> None:
    """Output the skeleton config."""
    render_skeleton(output_file=output_file)


def print_version() -> None:
    """Print the cdpctl version."""
    click.echo(__version__)
    sys.exit(0)


config.add_command(skeleton)
_cli.add_command(validate)
_cli.add_command(config)


def main() -> None:
    """Run main entry point for CLI."""
    _cli()  # pylint: disable=no-value-for-parameter


if __name__ == "__main__":
    main()
