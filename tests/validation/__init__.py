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
# Source File Name:  __init__.py
###
"""Functions to test Validations."""
import functools
from typing import Any, Callable

import pytest
from _pytest.outcomes import Failed

from cdpctl.validation import IssueType, current_context


def expect_validation_failure(func: Callable) -> Callable:
    """Check that the validation fails."""

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> None:
        current_context.clear()
        fail_caught = False
        try:
            func(*args, **kwargs)
        except Failed:
            fail_caught = True
        if not fail_caught:
            pytest.fail(f"Expected {func.__name__!r} to fail.")

    return wrapper


def expect_validation_warning(func: Callable) -> Callable:
    """Check that the validation succeeds."""

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> None:
        current_context.clear()
        try:
            func(*args, **kwargs)
        except Failed as e:
            pytest.fail(
                f"Expected {func.__name__!r} to have only a warning, not a problem. Failed with message: {e.msg}"
            )
        if current_context.state != IssueType.WARNING:
            pytest.fail(f"Expected {func.__name__!r} to have a warning.")

    return wrapper


def expect_validation_success(func: Callable) -> Callable:
    """Check that the validation succeeds."""

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> None:
        current_context.clear()
        try:
            func(*args, **kwargs)
            if current_context.state == IssueType.WARNING:
                raise Failed("A warning was issued.")
        except Failed as e:
            pytest.fail(
                f"Expected {func.__name__!r} to succeed. Failed with message: {e.msg}"
            )

    return wrapper
