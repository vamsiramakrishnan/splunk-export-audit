# Splunk-Export-Audit

A Scalable and Low Cost Splunk event exporter to publish OCI Audit Logs to Splunk
The Components Used 

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

## Components 
* The OCI Audit API is used to query for events every 2 minutes
* The OCI Fns trigger a series of queries and publish events to the Splunk HTTP Event Collector End point.
* The OCI API Gateway is used to Front-End the Functions. to allow for the fn invokation process through HTTP(S) Requests 

## Setup Fn Environment

[Preparing your tenancy for Functions](https://docs.cloud.oracle.com/en-us/iaas/Content/Functions/Tasks/functionsconfiguringtenancies.htm)

## Setup API Gateway 
[Preparing your tenancy for API Gateway](https://docs.cloud.oracle.com/en-us/iaas/Content/APIGateway/Concepts/apigatewayprerequisites.htm)

## Setup a Fn Development Environment
[Install and Setup The Fn-CLI](https://fnproject.io/tutorials/install/#DownloadandInstalltheFnCLI)

## Create & Set Context

    fn create context [CONTEXT-NAME] --provider oracle
    fn use context [CONTEXT-NAME]`

## Update the Context

### Compartment ID, API URL, Container Registry

    fn update context oracle.compartment-id <compartment-ocid>
    fn update context api-url https://functions.us-phoenix-1.oraclecloud.com
    fn update context registry [YOUR-TENANCY-NAMESPACE]/[YOUR-OCIR-REPO]

