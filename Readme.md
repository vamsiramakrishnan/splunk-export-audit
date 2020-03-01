# Splunk-Export-Audit

A Scalable and Low Cost Splunk event exporter to publish OCI Audit Logs to Splunk.
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
## [](https://github.com/vamsiramakrishnan/splunk-export-audit#components)Components

-   The `OCI Audit API` is  queried for audit events every 2 minutes for all regions and all compartments relevant to the tenancy. 
-   The `OCI Functions` trigger a series of queries and publish events to the Splunk HTTP Event Collector End point.
-   The `OCI API Gateway` is used to Front-End the Functions. to allow for the fn invokation process through HTTP(S) Requests rather than using the `OCI Fn Invocation mechanism` or the `oci-curl`
- The `Splunk HTTP event Collector` is a simplified mechanism that splunk provides to publish events 

## Design Goals 
``` 
Self Perpetuating
Event driven 
Scalable 
Low-Cost
Zero maintenance
```
## Pre-requisites
Working understanding of Functions | OCI- API Gateway and Splunk. These are some of the broad permissions that the Solution would require from an IAM Perspective

 - The Dynamic Group in which the Fn is Placed must be able to read Audit Logs of the entire Tenancy
 - The Dynamic Group in which the Fn is placed must be able to list all regions and list all compartments. 
 - The Dynamic Group in which the API gateway is placed must be capable of invoking and managing functions as the API Gateway invokes functions. 
 - The Dynamic Group in which both the Fn(s) and the API Gateway are placed must be able to use network resources.

### [](https://github.com/vamsiramakrishnan/splunk-export-audit#setup-fn-environment)Setup Fn Environment

[Preparing your tenancy for Functions](https://docs.cloud.oracle.com/en-us/iaas/Content/Functions/Tasks/functionsconfiguringtenancies.htm)

### [](https://github.com/vamsiramakrishnan/splunk-export-audit#setup-api-gateway)Setup API Gateway

[Preparing your tenancy for API Gateway](https://docs.cloud.oracle.com/en-us/iaas/Content/APIGateway/Concepts/apigatewayprerequisites.htm)

### [](https://github.com/vamsiramakrishnan/splunk-export-audit#setup-a-fn-development-environment)Setup a Fn Development Environment

[Install and Setup The Fn-CLI](https://fnproject.io/tutorials/install/#DownloadandInstalltheFnCLI)

####  [](https://github.com/vamsiramakrishnan/splunk-export-audit#create--set-context)Create & Set Context

```
fn create context [CONTEXT-NAME] --provider oracle
fn use context [CONTEXT-NAME]`

```

### [](https://github.com/vamsiramakrishnan/splunk-export-audit#update-the-context)Update the Context

### [](https://github.com/vamsiramakrishnan/splunk-export-audit#compartment-id-api-url-container-registry)Compartment ID, API URL, Container Registry

```
fn update context oracle.compartment-id <compartment-ocid>
fn update context api-url https://functions.us-phoenix-1.oraclecloud.com
fn update context registry [YOUR-TENANCY-NAMESPACE]/[YOUR-OCIR-REPO]
```



## A Deeper Dive into Architecture

![Flow of Fns calling each other](https://github.com/vamsiramakrishnan/splunk-export-audit/blob/master/media/DeepDiveL1.png)


## Role of Each Component
### 1. Wait Loop 

#### Description 
--------------

 1. Reduce the number of function calls , by running a function that stays idle for a configurable amount of time.
 2. Accept a Wait Time and Accept a Url to call after waiting and execute.

### 2. List Regions

#### Description
---------------

1. Every tenancy can be subscribed to a certain number of regions and this function lists those regions.

|Parameter Name  |  Description|  Example |
|--|--|--| 
| list_compartments_fn_url | API gateway Endpoint/Route to call next Fn, list compartments  | https://api-gw-url/compartments/getcompartments
| list_regions_fn_url | Https Link to self , to call after delay for self perpetuation| https://api-gw-url/regions/listregions
| wait_loop_fn_url | The url of the Fn that makes a delayed Fn Call |https://api-gw-url/wait/waitloop
| wait_loop_time | Time until next time list-regions Fn is called again | 0-100 Seconds

### 3. List Compartments

#### Description
---------------

1. IAM Policies are global and all regions have the same set of compartments within an OCI tenancy , yet audit events for each of these compartments occur region wise and hence the need to fetch individual compartments on a per region basis.

|Parameter Name  |  Description|  Example |
|--|--|--| 
| fetch_audit_events_fn_url| API gateway Endpoint/Route to call next function, fetch audit event | https://api-gw-url/audit/auditlog

### 4. Fetch Audit Events

#### Description
---------------

1. In a given compartment and given region , fetch all audit events that occured in the last two minutes

|Parameter Name  |  Description|  Example |
|--|--|--| 
| publish_to_splunk_fn_url| API gateway Endpoint/Route to call next function, Publish to Splunk | https://api-gw-url/publishtosplunk/pushtosplunk

### 5. Publish to Splunk 
#### Description
---------------

1. In a given compartment and given region , fetch all audit events that occured in the last two minutes

|Parameter Name  |  Description|  Example |
|--|--|--| 
| list_compartments_fn_url | API gateway Endpoint/Route to call next Fn, list compartments  | https://api-gw-url/compartments/getcompartments
| list_regions_fn_url | Https Link to self , to call after delay for self perpetuation| https://api-gw-url/regions/listregions
| wait_loop_fn_url | The url of the Fn that makes a delayed Fn Call |https://api-gw-url/wait/waitloop
| wait_loop_time | Time until next time list-regions Fn is called again | 0-100 Seconds
