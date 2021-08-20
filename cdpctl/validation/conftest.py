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
# type: ignore[attr-defined]
"""Provide validation configs."""
import sys
from typing import Any, Dict, Mapping, Optional, Tuple, Union

import click
import emoji
import pytest
from _pytest._code.code import ExceptionInfo, ExceptionRepr
from _pytest.config import Config
from _pytest.reports import CollectReport, TestReport
from _pytest.runner import CallInfo
from pytest import Collector, ExitCode, Item, Session

from cdpctl.utils import load_config

from . import UnrecoverableValidationError, current_context, get_config_value

this = sys.modules[__name__]
this.config_file = "config.yaml"
this.run_validations = 0


def pytest_runtestloop(
    session: Session,  # pylint: disable=unused-argument
) -> Optional[object]:
    """Catches the running of test."""
    pass


def pytest_sessionstart(session: Session) -> None:
    """Start a validation capture session."""
    session.issues = dict()
    session.errors = dict()


@pytest.hookimpl(tryfirst=True, hookwrapper=True)  # type: ignore[misc]
def pytest_runtest_makereport(item: Item, call: CallInfo[None]) -> TestReport:
    """Catch the report on results."""
    outcome = yield
    result = outcome.get_result()

    node = item.obj

    if call.when == "setup":  # Validation is starting
        current_context.clear()
        suf = node.__doc__.strip() if node.__doc__ else node.__name__
        if result.failed:
            click.echo(f"Unable to setup validation '{suf}'", err=True)
        if result.passed:
            current_context.validation_name = suf
            current_context.function = item.name
            current_context.nodeid = item.nodeid
            click.echo(suf, nl=False, err=True)
    elif call.when == "call":  # Validation was called
        if result.passed:
            # All good
            click.echo(f" {emoji.emojize(':check_mark:')}", err=True)
        elif result.failed:
            # Catch any issues
            click.echo(f" {emoji.emojize(':cross_mark:')}", err=True)
            # item.session.issues[item] = str(result.longrepr.chain[-1][0])
    elif call.when == "teardown":
        this.run_validations += 1
    sys.stdout.flush()


def pytest_exception_interact(
    node: Union[Item, Collector],
    call: CallInfo[Any],
    report: Union[CollectReport, TestReport],  # pylint: disable=unused-argument
) -> None:
    """Catch exceptions and fail out on Unrecoverable ones."""
    if isinstance(call.excinfo.value, UnrecoverableValidationError):
        click.echo("", err=True)
        suf = node.obj.__doc__.strip() if node.obj.__doc__ else node.obj.__name__
        click.secho("\n--- An Error Occured ---", fg="red", err=True)
        click.echo(
            f'An Error occured while running the "{suf}" validation.\n'
            + "It has the following information:\n",
            err=True,
        )
        click.echo(f"{str(call.excinfo.value)}\n", err=True)
        click.echo(f"({node.nodeid})", err=True)
        click.secho("-------------", fg="red", err=True)
        pytest.exit(1)


def pytest_sessionfinish(
    session: Session,
    exitstatus: Union[int, ExitCode],  # pylint: disable=unused-argument
) -> None:
    """Finish the validation session."""
    if session.exitstatus != ExitCode.INTERRUPTED:
        click.echo("")
        # env = Environment(
        #     loader=PackageLoader(package_name="cdpctl", package_path="templates"),
        #     autoescape=select_autoescape(),
        # )
        # template = env.get_template("console.j2")
        # click.echo(template.render(issues=get_issues()))


def pytest_report_teststatus(
    report: Union[CollectReport, TestReport],
    config: Config,  # pylint: disable=redefined-outer-name,unused-argument
) -> Tuple[str, str, Union[str, Mapping[str, bool]]]:
    """Grabs the tests status."""
    if report.when == "call":
        return report.outcome, "", report.outcome.upper()
    return "", "", ""


def pytest_internalerror(
    excrepr: ExceptionRepr,  # pylint: disable=unused-argument
    excinfo: ExceptionInfo[BaseException],  # pylint: disable=unused-argument
) -> Optional[bool]:
    """Catch pytest internal errors and sink them."""
    return False


@pytest.fixture
def config() -> Dict[str, Any]:
    """Provide the configuration as a test fixture."""
    return load_config(this.config_file)


def pytest_runtest_setup(item):
    """Check for the dynamic markers."""
    configuration = load_config(this.config_file)

    # Handle Network Types
    network_types_marker = item.get_closest_marker("network_types")
    if network_types_marker is not None:
        network_types = network_types_marker.kwargs.get("types")
        config_type = configuration["network_type"]
        if config_type not in network_types:
            pytest.skip(f"not supported for network type {config_type}")

    # Handle config_value
    config_value_marker = item.get_closest_marker("config_value")
    if config_value_marker is not None:
        requested_config_value_path = config_value_marker.kwargs.get("path")
        requested_config_value = config_value_marker.kwargs.get("value")
        if (
            requested_config_value_path is not None
            and requested_config_value is not None
        ):
            config_value = get_config_value(
                config=configuration,
                key=requested_config_value_path,
                key_value_expected=False,
            )
            if config_value is not None and config_value != requested_config_value:
                pytest.skip(
                    "the value set in the config for "
                    f"{requested_config_value_path} of {config_value} does not match "
                    f"the required value of {requested_config_value}"
                )


def pytest_configure(config):  # pylint: disable=redefined-outer-name
    """Add the markers to the ini config."""
    config.addinivalue_line(
        "markers",
        "network_types(types=[]): mark the network type a validation is target for.",
    )
    config.addinivalue_line(
        "markers",
        "config_value(path=None, value=None): "
        "mark the network type a validation is target for.",
    )
