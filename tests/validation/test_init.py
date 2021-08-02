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
# Source File Name:  test_init.py
###
"""Tests for the Shared Validation Functions."""
import pytest
from _pytest.outcomes import Failed

from cdpctl.validation import get_config_value


def test_get_config_value() -> None:
    """Test getting the config value."""
    simple_nest = {"foo": "bar"}
    assert get_config_value(simple_nest, "foo") == "bar"


def test_get_deeper_config_value() -> None:
    """Test getting the nested config value."""
    simple_nest = {"foo": {"bar": "car"}}
    assert get_config_value(simple_nest, "foo:bar") == "car"


def test_get_missing_config_value() -> None:
    """Test getting a missing config value."""
    simple_nest = {"foo": {"bar": "car"}}
    with pytest.raises(Failed):
        get_config_value(simple_nest, "foo:bat")


def test_get_missing_parent_config_value() -> None:
    """Test getting with a missing parent config value."""
    simple_nest = {"foo": {"bar": "car"}}
    with pytest.raises(Failed):
        get_config_value(simple_nest, "foot:bar")


def test_get_of_empty_config_value() -> None:
    """Test getting an empty config value."""
    simple_nest = {"foo": {"bar": None}}
    with pytest.raises(Failed):
        get_config_value(simple_nest, "foo:bar")
