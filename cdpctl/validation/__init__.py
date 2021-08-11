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
"""Shared validation functions."""
from typing import Any, Dict

import pytest


class ValidationError(Exception):
    """Base class for all Validation Exceptions."""

    pass


class UnrecoverableValidationError(ValidationError):
    """Unrecoverable Error during validation."""

    pass


def get_config_value(
    config: Dict[str, Any],
    key: str,
    key_value_expected: bool = True,
    path_delimiter: str = ":",
    key_missing_message: str = "Unable to find key in config {0}",
    data_expected_error_message: str = "No entry was provided for config option {0}",
    parent_key_missing_message: str = "Unable to find key path {0}",
) -> Any:
    """Get the value of a config key or have the proper error handling."""
    paths = key.split(path_delimiter)
    path_found = ""
    key_found = False
    data: Any = config
    try:
        for i in range(0, len(paths)):  # pylint: disable=C0200
            path_found += paths[i]
            if i < len(paths) - 1:
                path_found += path_delimiter
            else:
                key_found = True
            data = data[paths[i]]
    except KeyError:
        if key_found:
            pytest.fail(key_missing_message.format(path_found), False)
        else:
            pytest.fail(parent_key_missing_message.format(path_found), False)

    if key_value_expected and data is None:
        pytest.fail(data_expected_error_message.format(key), False)

    return data


def validator(func):
    """Wrap a validator function to handle errors better."""

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if isinstance(e, UnrecoverableValidationError):
                raise e
            raise UnrecoverableValidationError("Unhandled exception:", e) from e

    return wrapper
