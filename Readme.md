# Splunk-Export-Audit
A Scalable and Low Cost Splunk event exporter to publish OCI Audit Logs to Splunk


# Setup Fn Environment
## Create Context
``` fn create context [CONTEXT-NAME] --provider oracle ```

## Use the Created Context
``` fn use context [CONTEXT-NAME] ```

## Update the Context
   ### Compartment ID, API URL, Container Registry
   ``` fn update context oracle.compartment-id <compartment-ocid> ```
   
   ``` fn update context api-url https://functions.us-phoenix-1.oraclecloud.com ```
   
   ``` fn update context registry [YOUR-TENANCY-NAMESPACE]/[YOUR-OCIR-REPO] ```
   

