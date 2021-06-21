# Cloudera Data Platform Control - cdpctl

![GitHub Workflow Status](https://img.shields.io/github/workflow/status/cloudera-labs/cdpctl/Continuous%20Integration)
![Codecov](https://img.shields.io/codecov/c/github/cloudera-labs/cdpctl/)
[![License: AGPL 3.0](https://img.shields.io/badge/license-AGPL%203.0-green)](https://www.gnu.org/licenses/agpl-3.0.txt)

## What is cdpctl

The cdpctl Command Line Interface (CLI) provides the ability to check your cloud network environment and see if its ready to be used with CDP to create a CDP environment in.

## Versioning

Cloudera CDP is constantly improving, adding freatures, and fixing issues. So cdpctl is versioned with a date compatability in mind. The cdpctl script will always try to download the latest version of the applocations Docker image. These images and the wrapping script are verioing with a timestamp in the form of YYYY.MM.DD.Release. This allows us to have a quick turn around with supporting Cloudera CDP changes and you can always know when a version getting out of date.

## Development

Prereqs for VSCode:
Get Python and remote-containers plugins for VSCode.
