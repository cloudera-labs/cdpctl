
# Cloudera Data Platform Control - **cdpctl**

[![License: AGPL 3.0](https://img.shields.io/badge/license-AGPL%203.0-green)](https://www.gnu.org/licenses/agpl-3.0.txt)

## What is cdpctl

The cdpctl Command Line Interface (CLI) provides the ability to check your cloud network environment and see if it is ready to be used with Cloudera Data Platform (CDP) to create a CDP environment in. The validation command will run a series of checks to indicate if your cloud resources are configured according to CDP requirements. The output will be a listing of passing and failing validations such as below:

    IdBroker role has the EC2 trust policy. ✔ 
    Public subnets have minimum two availability zones. ✔
    Public subnets have adequate IP range. ❌

## Supported Public Clouds
Currently, **cdpctl** only supports AWS.

## Requirements

**cdpctl** has the following requirements
* Docker running locally.
* Access to your ~/.aws directory for your AWS profile and credentials, or have the credenitals set via environment variables.

## Using

The simplest way of using **cdpctl** is to download the wrapper script:
 
`curl https://raw.githubusercontent.com/cloudera-labs/cdpctl/main/install/cdpctl -o cdpctl && chmod 755 cdpctl`

From there you can create a configuration file by running the following command:
 
`./cdpctl config skeleton -o config.yml`  


This will give you a basic configuration file to be able to edit and fill with your cloud config you wish to validate for use with CDP.

In order to validate the environment you can run the validation command as follows:

`./cdpctl validate infra -c config.yml`


## Versioning

CDP is constantly improving with new features and bug fixes, so **cdpctl** is versioned with a 
date compatability in mind. The **cdpctl** script will always try to download the latest version of 
the source Docker image. These images and the wrapping script are versioned with a timestamp
in the form of **YYYY.MM.DD.Release**. This allows us to have a quick turn around for any 
Cloudera CDP changes, and you can always know when a version is out of date.  
  
