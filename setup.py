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
# Source File Name:  setup.py
###
"""The setup script."""
import os
import re
import sys
from typing import Any

from setuptools import find_packages, setup

install_requires = []
dependency_links = []
package_data = {}


def get_version() -> Any:
    """Get current version from code."""
    regex = r"__version__\s=\s\"(?P<version>(\d+!)?(\d+)(\.\d+)+([\.\-\_])?((a(lpha)?|b(eta)?|c|r(c|ev)?|pre(view)?)\d*)?(\.?(post|dev)\d*)?)\""
    path = ("cdpctl", "__version__.py")
    return re.search(regex, read(*path)).group("version")


# determine requirements
with open("requirements.txt") as f:
    requirements = f.read()
for line in re.split("\n", requirements):
    if line and line[0] == "#" and "#egg=" in line:
        line = re.search(r"#\s*(.*)", line).group(1)
    if line and line[0] != "#":
        lib_stripped = line.split(" #")[0].strip()
        install_requires.append(lib_stripped)


def read(*parts):
    """Read file."""
    filename = os.path.join(os.path.abspath(os.path.dirname(__file__)), *parts)
    sys.stdout.write(filename)
    with open(filename, encoding="utf-8", mode="rt") as fp:
        return fp.read()


with open("README.md") as readme_file:
    readme = readme_file.read()

package_data = {
    "": ["Makefile", "*.md", "bin"],
    "cdpctl": [
        "requirements*.txt",
        "validation/validation.ini",
        "templates/config.yml.j2",
    ],
}

if __name__ == "__main__":

    setup(
        author="Cloudera Labs",
        author_email="cloudera-labs@cloudera.com",
        classifiers=[
            "Development Status :: 4 - Beta",
            "Framework :: AsyncIO",
            "Intended Audience :: Developers",
            "License :: OSI Approved :: License",
            "Natural Language :: English",
            "Programming Language :: Python :: 3.8",
            "Programming Language :: Python :: 3",
            "Topic :: Software Development :: Libraries :: Python Modules",
        ],
        description="Cloudera CDP Cloud Resources Automation and Validation",
        include_package_data=True,
        install_requires=install_requires,
        keywords=["cdpctl"],
        license="license",
        long_description_content_type="text/markdown",
        long_description=readme,
        name="cdpctl",
        packages=find_packages(exclude=("tests", "tests.*")),
        package_data=package_data,
        scripts=["bin/cdpctl", "bin/cdpctl.bat"],
        dependency_links=dependency_links,
        test_suite="tests",
        url="",
        version=get_version(),
        zip_safe=False,
    )
