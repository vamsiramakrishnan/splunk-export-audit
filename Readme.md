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

## Quickstart For Setup On OCI Side
![](https://github.com/vamsiramakrishnan/splunk-export-audit/blob/master/media/QuickStart_Steps.png)
### Create Compartments and Groups
1. Create a Compartment `splunk-export-compartment`
2. Create a Group  `splunk-export-users`
3. Add `Required User` to group `splunk-export-users`

### Create IAM Policies
4. Create an IAM Policy `splunk-export-policy` with the following policy statements in the `root` compartment 
```
Allow group splunk-export-users to manage all-resources in compartment splunk-export-compartment
Allow group splunk-export-users to manage repos in tenancy
Allow group splunk-export-users to read audit-events in tenancy
Allow group splunk-export-users to read tenancies in tenancy
Allow group splunk-export-users to read compartments in tenancy
Allow service FaaS to use all-resources in compartment splunk-export-compartment
Allow service FaaS to read repos in tenancy
```
### Create a VCN, Subnet & Security Lists
5. Use VCN Quick Start to Create a VCN `splunk-export-vcn` with Internet Connectivity
6. Go to Security List and Create a `Stateful Ingress Rule` in the `Default Security list` to allow Ingress Traffic in  `TCP 443`
7. Go to Default Security List and verify if a `Stateful Egress Rule` is available in the `Default Security List` to allow egress traffic in `all ports and all protocols`

### Create a Function Application
9. Create a Function Application `splunk-export-app` in the compartment `splunk-export-compartment` while selecting `splunk-export-vcn` and the `Public Subnet`

### Create  an API Gateway 
11. Create an API Gateway `splunk-export-apigw` in the compartment `splunk-export-compartment`while selecting `splunk-export-vcn` and the `Public Subnet`
### Create a Dynamic Group
13. Create a Dynamic Group `splunk-export-dg`
Instances that meet the criteria defined by any of these rules will be included in the group.
```
ANY {instance.compartment.id = [splunk-export-compartment OCID]}
ANY {resource.type = 'ApiGateway', resource.compartment.id =[splunk-export-compartment OCID]}
ANY {resource.type = 'fnfunc', resource.compartment.id = [splunk-export-compartment OCID]}
```
### Create a  OCIR Repo
14. Create a  `Private` Repository `splunk-export-repo`

### Configure Cloud Shell
15. Setup Cloud Shell in your tenancy - [Link](https://docs.cloud.oracle.com/en-us/iaas/Content/API/Concepts/cloudshellgettingstarted.htm?TocPath=Developer%20Tools%20%7C%7CUsing%20Cloud%20Shell%7C_____0)
16. Clone the Repo in the cloud shell
    `git clone https://github.com/vamsiramakrishnan/splunk-export-audit.git`
17. Login to your region's docker login `iad.ocir.io` with appropriate credentials 
###  Create & Set Fn Context 
```
fn create context splunk-export-context --provider oracle
fn use context splunk-export-context`
```
### Update the Context 
```
fn update context oracle.compartment-id [splunk-export-compartment-ocid]
fn update context api-url https://functions.[region-name].oraclecloud.com
fn update context registry [YOUR-TENANCY-NAMESPACE]/[splunk-export-repo]
```
### Deploy the Functions
Each folder within the repo represents a function , go to each folder and deploy the function using the the `fn --verbose deploy `
```
cd splunk-export-audit
cd list-regions
fn --verbose deploy splunk-export-app list-regions

# Go into each Function and execute this command 
cd ../list-compartments
fn --verbose deploy splunk-export-app list-compartments
```
### Create API Gateway Deployment Endpoints
Map the endpoints 
| SNo| Deployment Name | Prefix| Method | Endpoint | Fn-Name
|--|--|--|--|--|--|
| 1 | list-regions | regions | GET | /listregions |  list-regions|
| 2 | list-compartments | compartments | POST| /getcompartments | list-compartments | 
|3 | fetch-audit-events | audit | POST | /auditlog | fetch-audit-events |
|4 | publish-to-splunk | splunk | POST | /splunk | publish-to-splunk |
|5 | wait-loop | wait | POST | /wait | wait-loop |

### Set the Environment Variables for Each Function
These environment variables help call other functions. One after the other. 
| Fn-Name |Parameter Name  |  Description|  Example |
|--|--|--|--| 
|list-regions| list_compartments_fn_url | API gateway Endpoint/Route to call next Fn, list compartments  | https://api-gw-url/compartments/getcompartments
|list-regions| list_regions_fn_url | Https Link to self , to call after delay for self perpetuation| https://api-gw-url/regions/listregions
|list-regions| wait_loop_fn_url | The url of the Fn that makes a delayed Fn Call |https://api-gw-url/wait/waitloop
|list-regions| wait_loop_time | Time until next time list-regions Fn is called again | 0-100 Seconds
| list-compartments| fetch_audit_events_fn_url| API gateway Endpoint/Route to call next function, fetch audit event | https://api-gw-url/audit/auditlog
|fetch-audit-events | publish_to_splunk_fn_url| API gateway Endpoint/Route to call next function, Publish to Splunk | https://api-gw-url/publishtosplunk/pushtosplunk
|publish-to-splunk| source_source_name| The Source Name that you would like Splunk to see | oci-hec-event-collector
| publish-to-splunk| source_host_name| The Source Hostname that you would like Splunk to see | oci-audit-logs
|publish-to-splunk| splunk_url| The Splunk Cloud URL ( Append input to the beginning of your splunk cloud url, do not add any http/https etc.  | input-prd-p-hh6835czm4rp.cloud.splunk.com
|publish-to-splunk| splunk_hec_token| The Token that is unqiue to that HEC  | TOKEN
|publish-to-splunk| splunk_index_name| The index into which you'd like these logs to get aggregated | main



## Why we did what we did !

### [](https://github.com/vamsiramakrishnan/splunk-export-audit#setup-fn-environment)Setup Fn Environment
#### Key Steps

 - Give your Functions-Users access to a Registry
 - Give your Functions-Users access to Network Resources
 - Create a Dynamic Group for Functions to access OCI API
 - Give your Functions dynamic group access to List Regions
 - Give your Functions dynamic group access to List Compartments
 - Give your Functions dynamic group access to List Fetch Audit events all over the tenancy. 
 
#### Links 
- [Preparing your tenancy for Functions](https://docs.cloud.oracle.com/en-us/iaas/Content/Functions/Tasks/functionsconfiguringtenancies.htm)
- [IAM Policy Reference for Functions ](https://docs.cloud.oracle.com/en-us/iaas/Content/Functions/Tasks/functionscreatingpolicies.htm)


### [](https://github.com/vamsiramakrishnan/splunk-export-audit#setup-api-gateway)Setup API Gateway
#### Key Steps

 - Give your API-Gateway users access to Functions 
 - Give your API-Gateway users access to Network Resources 
 - Create a Dynamic Group for API - Gateway to invoke functions.
 - Give your API-Gateway dynamic group access to manage / invoke Functions
#### Links 
 - [Preparing your tenancy for API Gateway](https://docs.cloud.oracle.com/en-us/iaas/Content/APIGateway/Concepts/apigatewayprerequisites.htm) .
- [Dynamic IAM Policy for API Gateway to manage
   Functions](https://docs.cloud.oracle.com/en-us/iaas/Content/APIGateway/Tasks/apigatewaycreatingpolicies.htm#dynamic-group-policy)

### [](https://github.com/vamsiramakrishnan/splunk-export-audit#setup-a-fn-development-environment)Setup a Fn Development Environment

[Install and Setup The Fn-CLI](https://fnproject.io/tutorials/install/#DownloadandInstalltheFnCLI)

## A Deeper Dive into Architecture

![Flow of Fns calling each other](https://github.com/vamsiramakrishnan/splunk-export-audit/blob/master/media/DeepDiveL1.png)


## Role of Each Fn
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

1. For each audit event, a publish to splunk 

|Parameter Name  |  Description|  Example |
|--|--|--| 
| source_source_name| The Source Name that you would like Splunk to see | oci-hec-event-collector
| source_host_name| The Source Hostname that you would like Splunk to see | oci-audit-logs
| splunk_url| The Splunk Cloud URL ( Append input to the beginning of your splunk cloud url, do not add any http/https etc.  | input-prd-p-hh6835czm4rp.cloud.splunk.com
| splunk_hec_token| The Token that is unqiue to that HEC  | TOKEN
| splunk_index_name| The index into which you'd like these logs to get aggregated | main
