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
import os
from collections import namedtuple
from enum import Enum
from typing import Any, Dict, List

import pytest
import yaml
from marshmallow import Schema, fields, post_load

from cdpctl.validation.issues import (
    CONFIG_OPTION_DATA_NOT_DEFINED,
    CONFIG_OPTION_KEY_NOT_DEFINED,
    CONFIG_OPTION_PARENT_PATH_NOT_DEFINED,
)

ISSUE_TEMPLATES_FILE = "issue_templates.yml"


class ValidationError(Exception):
    """Base class for all Validation Exceptions."""

    pass


class UnrecoverableValidationError(ValidationError):
    """Unrecoverable Error during validation."""

    pass


class IssueTemplate:
    """Issue Templates."""

    def __init__(
        self,
        template_id: str,
        summary: str,
        docs_link: str = None,
        render_type: str = "inline",
    ) -> None:
        """Initialize the IssueTemplate."""
        self.id = template_id
        self.summary = summary
        self.docs_link = docs_link
        self.render_type = render_type


class IssueTemplateSchema(Schema):
    """Schema for Issue Templates."""

    template_id = fields.Str(required=True, data_key="id")
    summary = fields.Str(required=True)
    docs_link = fields.Str(required=False)
    render_type = fields.Str(default="list", required=False)

    @post_load
    def make_issue_template(
        self, data, **kwargs
    ):  # pylint: disable=unused-argument,no-self-use
        """Make the IssueTemplate based on the Schema."""
        return IssueTemplate(**data)


class Issue:
    """Issue representaiton."""

    def __init__(
        self,
        template: IssueTemplate,
        subjects: List[str] = None,
        resources: List[str] = None,
    ) -> None:
        """Initialize the Issue."""
        self.validation: str = None
        self._template: str = template
        self._subjects = subjects
        self._resources = resources

    @property
    def message(self):
        """Get the message."""
        return self._template.summary.format(*self._subjects)

    @property
    def resources(self) -> List[str]:
        """Get the resources."""
        if not self._resources:
            return []
        return self._resources

    @property
    def docs_link(self):
        """Get the document link."""
        return self._template.docs_link

    @property
    def render_type(self):
        """Get the render type."""
        return self._template.render_type


class IssueType(Enum):
    """Issue Types enum."""

    PROBLEM = "problem"
    WARNING = "warning"


def load_issue_templates(path):
    """Get the IssueTemplates found in a path."""
    templates = []
    schema = IssueTemplateSchema(many=True)
    with open(os.path.join(path)) as input_file:
        temp_gen = yaml.load_all(input_file, Loader=yaml.FullLoader)
        templates = schema.load(temp_gen)
    return templates


def load_all_issue_templates():
    """Get all of the IssueTemplates found."""
    issue_templates = {}
    for root, _, files in os.walk(os.path.dirname(__file__)):
        if ISSUE_TEMPLATES_FILE in files:
            loading_templates = load_issue_templates(
                os.path.join(root, ISSUE_TEMPLATES_FILE)
            )
            for template in loading_templates:
                issue_templates[template.id] = template
    return issue_templates


# List of issues found during the validation run
_issues: Dict[str, Dict[str, List[Issue]]] = {}


def get_issues() -> Dict[str, Dict[str, List[Issue]]]:
    """Get the Issues found during the validation run."""
    return _issues


_issue_templates: Dict[str, IssueTemplate] = load_all_issue_templates()


class Context:
    """Basic Validation Context."""

    def __init__(self) -> None:
        """Initialize the Context."""
        self.validation_name = None
        self.function = None
        self.nodeid = None
        self.state = None
        self.last_message = None

    def clear(self) -> None:
        """Clear all the context values."""
        self.validation_name = None
        self.function = None
        self.nodeid = None
        self.state = None
        self.last_message = None


current_context: Context = Context()


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


def _add_issue(issue_type: IssueType, issue: Issue):
    """Add an Issue to the selected type for the current validation."""
    context = current_context
    if not context.state:
        context.state = issue_type
    elif issue_type == IssueType.PROBLEM and context.state == IssueType.WARNING:
        context.state = IssueType.PROBLEM

    if context.validation_name not in get_issues():
        get_issues()[context.validation_name] = {
            IssueType.PROBLEM.value: [],
            IssueType.WARNING.value: [],
        }
    get_issues()[context.validation_name][issue_type.value].append(issue)
    context.last_message = issue.message


def fail(
    template: str, subjects: List[str] = None, resources: List[str] = None
) -> None:
    """Fail the validation."""
    if template not in _issue_templates:
        raise UnrecoverableValidationError(f"Unable to find issue template {template}")

    subjects = [subjects] if isinstance(subjects, str) else subjects
    resources = [resources] if isinstance(resources, str) else resources

    _add_issue(
        IssueType.PROBLEM,
        Issue(
            template=_issue_templates[template], subjects=subjects, resources=resources
        ),
    )
    raise pytest.fail(current_context.last_message, False)


def warn(
    template: str, subjects: List[str] = None, resources: List[str] = None
) -> None:
    """Issue a warning for the validation."""
    if template not in _issue_templates:
        raise UnrecoverableValidationError(f"Unable to find issue template {template}")

    subjects = [subjects] if isinstance(subjects, str) else subjects
    resources = [resources] if isinstance(resources, str) else resources
    _add_issue(
        IssueType.WARNING,
        Issue(
            template=_issue_templates[template], subjects=subjects, resources=resources
        ),
    )


def get_config_value(
    config: Dict[str, Any],
    key: str,
    key_value_expected: bool = True,
    path_delimiter: str = ":",
    key_not_found_issue: str = CONFIG_OPTION_KEY_NOT_DEFINED,
    data_expected_issue: str = CONFIG_OPTION_DATA_NOT_DEFINED,
    parent_key_missing_issue: str = CONFIG_OPTION_PARENT_PATH_NOT_DEFINED,
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
            fail(template=key_not_found_issue, subjects=path_found)
        else:
            fail(template=parent_key_missing_issue, subjects=path_found)

    if key_value_expected and data is None:
        fail(template=data_expected_issue, subjects=key)

    return data
