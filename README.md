
# Cloudera Data Platform Control - **cdpctl**


[![codecov](https://codecov.io/gh/cloudera-labs/cdpctl/branch/dev/graph/badge.svg?token=OXJGNI1P1C)](https://codecov.io/gh/cloudera-labs/cdpctl)
[![Continuous Integration](https://github.com/cloudera-labs/cdpctl/actions/workflows/ci.yml/badge.svg?branch=dev)](https://github.com/cloudera-labs/cdpctl/actions/workflows/ci.yml)
[![License: AGPL 3.0](https://img.shields.io/badge/license-AGPL%203.0-green)](https://www.gnu.org/licenses/agpl-3.0.txt)

## What is cdpctl

The cdpctl Command Line Interface (CLI) provides the ability to check your cloud provider configuration and verify if it is ready to be used with Cloudera Data Platform (CDP) Public Cloud to register a CDP environment. The cdpctl validation command runs a series of checks to indicate if your cloud resources are configured according to CDP requirements. The output is a listing of passing and failing validations such as those listed below:

    IdBroker role has the EC2 trust policy. ✔
    Public subnets have minimum two availability zones. ✔
    Public subnets have adequate IP range. ❌

## Supported public cloud providers 
Currently, **cdpctl** only supports the AWS and Azure cloud environments.

## Prerequisites

Prior to using **cdpctl**, you should meet the the following prerequisites:
* You must have Docker running locally. To download Docker, refer to [https://docs.docker.com/get-docker/](https://docs.docker.com/get-docker/).  
* (AWS) You must configure the ~/.aws directory and create your AWS CLI profile and credentials, or set the credentials via environment variables. This provides access to the specific AWS account where you are planning to register a CDP environment. If you need to set these up, refer to [AWS documentation](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html).  
* (Azure) You must configure the ~/.azure directory or have the Azure credentials set via environment variables. This provides access to the specific Azure account where you are planning to register a CDP environment.  

## Using cdpctl 

Once you have Docker running and your AWS or Azure CLI profile configured, you can start using cdpctl.  

1. Ensure that Docker is running in the background. 

2. Run the following command to download and execute the wrapper script:  
    
    `curl https://raw.githubusercontent.com/cloudera-labs/cdpctl/main/install/cdpctl -o cdpctl && chmod 755 cdpctl`
    
    When you execute this command, cdpctl downloads and executes the wrapper script. This launches a docker container, and you find yourself in that container ready to use cdpctl CLI commands. 

    > **_NOTE:_** You should run this command periodically to update the container to the latest version.
    
3. Create a configuration file by running the following command, specifying “aws” or “azure” in the `platform` parameter. For example:  
    
    `./cdpctl config skeleton --platform=aws -o config.yml`
    
    This creates you a basic configuration file in the location where the command was executed. You need to edit the file, entering your cloud provider configuration that you wish to validate for use with CDP. The comments in the file guide you through the configuration.  
    
4. Once the file has been populated, in order to validate the environment you can run the validation command as follows:  
    
    `./cdpctl validate infra -c config.yml`
    
    The tool prompts you if any parameters are missing. 
    
    The output is a listing of passing and failing validations such as those listed below:
  
        IdBroker role has the EC2 trust policy. ✔  
        Public subnets have minimum two availability zones. ✔  
        Public subnets have adequate IP range. ❌  
    
5. If you need to make any changes in the file, repeat the previous two steps. Once all of the items return "✔  ”, you can register your cloud provider environment in CDP.  


## Versioning

As CDP is constantly improving with new features and bug fixes, **cdpctl** is versioned with date compatibility in mind. The **cdpctl** script will always try to download the latest version of the source Docker image. The Docker images and the wrapping script are versioned with a timestamp in the form of **YYYY.MM.DD.Release**. This allows Cloudera to have a quick turnaround for any Cloudera CDP changes, and allows you to know when a version is out of date.
