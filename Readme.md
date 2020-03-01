# Splunk-Export-Audit

A Scalable and Low Cost Splunk event exporter to publish OCI Audit Logs to Splunk The Components Used

```
    +-------------------+  +--------------------+  +----------------------+
    |                   |  |                    |  |                      |
    |  OCI API Gateway  |  |  OCI Fns           |  |                      |
    |                   |  |                    |  |                      |
    |                   |  |                    |  |                      |
    +-------------------+  +--------------------+  |   Splunk HTTP Event  |
                                                   |     Collector        |
    +-------------------------------------------+  |                      |
    |                                           |  |                      |
    |             OCI - Audit API               |  |                      |
    |                                           |  |                      |
    +-------------------------------------------+  +----------------------+

```
## A Deeper Dive into Architecture

![Flow of Fns calling each other](https://github.com/vamsiramakrishnan/splunk-export-audit/blob/master/media/DeepDiveL1.png)

## [](https://github.com/vamsiramakrishnan/splunk-export-audit#components)Components

-   The OCI Audit API is used to query for events every 2 minutes
-   The OCI Fns trigger a series of queries and publish events to the Splunk HTTP Event Collector End point.
-   The OCI API Gateway is used to Front-End the Functions. to allow for the fn invokation process through HTTP(S) Requests

## [](https://github.com/vamsiramakrishnan/splunk-export-audit#setup-fn-environment)Setup Fn Environment

[Preparing your tenancy for Functions](https://docs.cloud.oracle.com/en-us/iaas/Content/Functions/Tasks/functionsconfiguringtenancies.htm)

## [](https://github.com/vamsiramakrishnan/splunk-export-audit#setup-api-gateway)Setup API Gateway

[Preparing your tenancy for API Gateway](https://docs.cloud.oracle.com/en-us/iaas/Content/APIGateway/Concepts/apigatewayprerequisites.htm)

## [](https://github.com/vamsiramakrishnan/splunk-export-audit#setup-a-fn-development-environment)Setup a Fn Development Environment

[Install and Setup The Fn-CLI](https://fnproject.io/tutorials/install/#DownloadandInstalltheFnCLI)

## [](https://github.com/vamsiramakrishnan/splunk-export-audit#create--set-context)Create & Set Context

```
fn create context [CONTEXT-NAME] --provider oracle
fn use context [CONTEXT-NAME]`

```

## [](https://github.com/vamsiramakrishnan/splunk-export-audit#update-the-context)Update the Context

### [](https://github.com/vamsiramakrishnan/splunk-export-audit#compartment-id-api-url-container-registry)Compartment ID, API URL, Container Registry

```
fn update context oracle.compartment-id <compartment-ocid>
fn update context api-url https://functions.us-phoenix-1.oraclecloud.com
fn update context registry [YOUR-TENANCY-NAMESPACE]/[YOUR-OCIR-REPO]
```
