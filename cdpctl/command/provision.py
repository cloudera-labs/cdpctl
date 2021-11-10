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
# Source File Name:  provision.py
###
"""Povision Command Implementation."""
import os
from typing import Any, Dict

import ansible_runner
import progressbar

from cdpctl.validation import get_issues
from cdpctl.validation.renderer import get_renderer


def run_provision(
    target: str, config_file: str, debug: bool, output_format: str, output_file: str
) -> None:
    """Run the povision."""
    print(f"provisioning {target} with {str(config_file)}")
    status_updater = EventHandler().status_updater
    t, _ = ansible_runner.run_async(
        private_data_dir=os.path.join(os.getcwd(), "example"),
        playbook="test.yaml",
        quiet=True,
        event_handler=status_updater,
        debug=debug,
        logfile=output_file,
    )
    t.join()
    renderer = get_renderer(output_format=output_format)
    renderer.render(get_issues(), output_file)


class EventHandler:
    def __init__(self) -> None:
        self.progress_bar = progressbar.ProgressBar(
            max_value=progressbar.UnknownLength, redirect_stdout=True
        )

    def status_updater(self, event: Dict[str, Any]) -> None:
        """Update the status of the provision."""
        if "event_data" in event and "name" in event["event_data"]:
            print(f"Task: {event['event_data']['name']}")
            self.progress_bar.update(event["counter"])
            progressbar.streams.flush()
