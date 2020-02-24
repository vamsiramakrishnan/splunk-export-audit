# Splunk-Export-Audit
A Scalable and Low Cost Splunk event exporter to publish OCI Audit Logs to Splunk


# Setup Fn Environment
## Create Context
fn create context <context_name> --provider oracle

## Use the Created Context
fn use context <context_name>

## Update the Context
   ### Compartment ID Setting
   fn update context oracle.compartment-id <compartment-ocid>

   ### 
   fn update context api-url https://functions.us-phoenix-1.oraclecloud.com

