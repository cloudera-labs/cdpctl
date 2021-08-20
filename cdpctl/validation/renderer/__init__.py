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
"""Base Renderer Module."""
import json

from jinja2 import Environment, PackageLoader, select_autoescape

from cdpctl.utils import smart_open
from cdpctl.validation import UnrecoverableValidationError


class ValidationRenderer:
    """Base renderer class."""

    def render(self, issues, output_file):
        """Render the issues found."""
        pass


class TextValidationRenderer(ValidationRenderer):
    """Text renderer class."""

    def render(self, issues, output_file):
        """Render the issues found as a text format."""
        env = Environment(
            loader=PackageLoader(
                package_name="cdpctl.validation.renderer", package_path="templates"
            ),
            autoescape=select_autoescape(),
        )
        template = env.get_template("text.j2")
        with smart_open(output_file) as f:
            f.write(template.render(issues=issues))


class JsonValidationRenderer(ValidationRenderer):
    """Json renderer class."""

    def render(self, issues, output_file):
        """Render the issues found as a json format."""

        json_issues = []
        for key, value in issues.items():
            json_rep = {}
            json_rep["validation"] = key
            json_rep["problems"] = []
            json_rep["warnings"] = []
            for problem in value["problem"]:
                json_rep["problems"].append(
                    {"message": problem.message, "resources": problem.resources}
                )
            for warning in value["warning"]:
                json_rep["warnings"].append(
                    {"message": warning.message, "resources": warning.resources}
                )
            json_issues.append(json_rep)

        with smart_open(output_file) as f:
            f.write(
                json.dumps(
                    json_issues,
                    indent=4,
                )
            )


def get_renderer(output_format: str) -> ValidationRenderer:
    """Get the correct renderer for the output format."""
    if output_format == "text":
        return TextValidationRenderer()
    if output_format == "json":
        return JsonValidationRenderer()
    raise UnrecoverableValidationError(
        f"Unknown validation output format: {output_format}."
    )
