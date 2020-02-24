# Splunk-Export-Audit

A Scalable and Low Cost Splunk event exporter to publish OCI Audit Logs to Splunk

## Setup Fn Environment

[Preparing your tenancy for Functions]((https://docs.cloud.oracle.com/en-us/iaas/Content/Functions/Tasks/functionsconfiguringtenancies.htm))

## Setup API Gateway 
[Preparing your tenancy for API Gateway](https://docs.cloud.oracle.com/en-us/iaas/Content/APIGateway/Concepts/apigatewayprerequisites.htm)

## Create & Set Context

    fn create context [CONTEXT-NAME] --provider oracle
    fn use context [CONTEXT-NAME]`

## Update the Context

### Compartment ID, API URL, Container Registry

    fn update context oracle.compartment-id <compartment-ocid>
    fn update context api-url https://functions.us-phoenix-1.oraclecloud.com
    fn update context registry [YOUR-TENANCY-NAMESPACE]/[YOUR-OCIR-REPO]
