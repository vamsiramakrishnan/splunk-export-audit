# Splunk-Export-Audit

## Introduction 
For Integrated SecOps , the SIEM plays an important component and Splunk is a very popular SIEM solution. The setup described below helps in near-realtime, zero-touch audit-log export to the Splunk Http event Collector for Indexing and Analysis.

![](https://github.com/vamsiramakrishnan/splunk-export-audit/blob/master/media/TheSimpleArchitecture.png)
A Scalable and Low Cost Splunk event exporter to publish OCI Audit Logs to Splunk.


## Components

-   The `OCI Audit API` is  queried for audit events every 2 minutes for all regions and all compartments relevant to the tenancy. 
-   The `OCI Functions` trigger a series of queries and publish events to the Splunk HTTP Event Collector End point.
-  `OCI Health Checks` are used to trigger a GET Request on to a public HTTPS Endpoint every `5-min` / `1-min` /  `30s`
-   The `OCI API Gateway` is used to Front-End the Functions. to allow for the fn invokation process through HTTP(S) Requests rather than using the `OCI Fn Invocation mechanism` or the `oci-curl`
- `OCI Streaming` as a scalable source of persistence that stores `state`, `audit events`, `most up-to-date compartment & region list` in the tenancy. 
- `OCI Notifications` are used to notify downstream functions for triggering along with information on  `stream-cursor, offset, partition` information to the next function. 
- The `Splunk HTTP event Collector` is a simplified mechanism that splunk provides to publish events 

![](https://github.com/vamsiramakrishnan/splunk-export-audit/blob/master/media/SimpleRepresentation.png)

## Design Goals 
``` 
Self Perpetuating
Event driven 
Scalable 
Low-Cost
Zero maintenance
```

## Quickstart For Setup On OCI Side

### Create Compartments and Groups
1. Create a Compartment `splunk-export-compartment`
2. Create a Group  `splunk-export-users`
3. Add `Required User` to group `splunk-export-users`
4. Create a Dynamic Group `splunk-export-dg`
5. Write appropriate IAM Policies at the tenancy level and compartment level.

### Create IAM Policies
 - Create an IAM Policy `splunk-export-policy` with the following policy statements in the `root` compartment 
```
Allow group splunk-export-users to manage repos in tenancy
Allow group splunk-export-users to read audit-events in tenancy
Allow group splunk-export-users to read tenancies in tenancy
Allow group splunk-export-users to read compartments in tenancy
Allow service FaaS to read repos in tenancy
```
### Create a Dynamic Group
 - Create a Dynamic Group `splunk-export-dg` Instances that meet the criteria defined by any of these rules will be included in the group.
```
ANY {instance.compartment.id = [splunk-export-compartment OCID]}
ANY {resource.type = 'ApiGateway', resource.compartment.id =[splunk-export-compartment OCID]}
ANY {resource.type = 'fnfunc', resource.compartment.id = [splunk-export-compartment OCID]}
```
### Create Dynamic Group IAM Policy
Create this Policy inside the compartment `splunk-export-compartment`
```
Allow service FaaS to use all-resources in compartment splunk-export-compartment
Allow group splunk-export-users to manage all-resources in compartment splunk-export-compartment
Allow group splunk-export-dg to use ons-topics in compartment splunk-export-compartment
Allow group splunk-export-dg to use stream-pull in compartment splunk-export-compartment
Allow group splunk-export-dg to use stream-push in compartment splunk-export-compartment
Allow group splunk-export-dg to use virtual-network-family in compartment splunk-export-compartment
Allow service FaaS to use all-resources in compartment splunk-export-compartment
```

### Create a VCN, Subnet & Security Lists

 - Use VCN Quick Start to Create a VCN `splunk-export-vcn` with Internet.
 - Connectivity Go to Security List and Create a `Stateful Ingress Rule` in the `Default Security list` to allow Ingress Traffic in  `TCP 443`
 - Go to Default Security List and verify if a `Stateful Egress Rule` is available in the `Default Security List` to allow egress traffic in  `all ports and all protocols`

### Create a Function Application

 - Create a Function Application `splunk-export-app` in the compartment `splunk-export-compartment` while selecting `splunk-export-vcn` and the `Public Subnet`

### Create a  OCIR Repo

 - Create a  `Private` Repository `splunk-export-repo`

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

cd fetch-audit-events
fn --verbose deploy splunk-export-app fetch-audit-events

cd publish-to-splunk
fn --verbose deploy splunk-export-app publish-to-splunk
```

### Create  an API Gateway 
11. Create an API Gateway `splunk-export-apigw` in the compartment `splunk-export-compartment`while selecting `splunk-export-vcn` and the `Public Subnet`

### Create Notification Channels 
12. Create two notification channels `splunk-fetch-audit-event`  `splunk-publish-to-splunk`. Create subscriptions to Trigger the Functions

### Create API Gateway Deployment Endpoints
Map the endpoint as follows 
 Deployment Name | Prefix| Method | Endpoint | Fn-Name
--|--|--|--|--|
 list-regions | regions | GET | /listregions |  list-regions|


### Set the Environment Variables for Each Function
These environment variables help call other functions. One after the other. 
| Fn-Name |Parameter Name  |  Description|  Example |
|--|--|--|--| 
|list-regions| records_per_fn | Batch Size of Number of Events to be processed in one go by the Next Fn | 25-50
|list-regions| audit_topic| OCID of Notifications topic used to trigger and notify the Fn fetch-audit-events  | ocid1.onstopic.oc1.phx.aaaaaaaa
|list-regions | stream_ocid| OCID of the Stream used to Publish the list of compartments and regions from where Audit events will be fetched | ocid1.stream.oc1.phx.amaaaaaa
|list-regions | streaming_endpoint| Endpoint of Streaming, depends on which region you provision Streaming | ocid1.stream.oc1.phx.amaaaaaa
|fetch-audit-events | records_per_fn| Batch Size of Number of Events to be processed in one go by the Next Fn | 25-50
|fetch-audit-events | splunk_topic| OCID of the Topic used to Notify& Trigger the publish-to-splunk Function| ocid1.onstopic.oc1.phx.aaaaaaaa
|fetch-audit-events | stream_ocid| OCID of the Stream used to Publish the actual Audit Event payload | ocid1.stream.oc1.phx.amaaaaaa
|fetch-audit-events | streaming_endpoint| Endpoint of Streaming, depends on which region you provision Streaming | ocid1.stream.oc1.phx.amaaaaaa
|publish-to-splunk| source_source_name| The Source Name that you would like Splunk to see | oci-hec-event-collector
| publish-to-splunk| source_host_name| The Source Hostname that you would like Splunk to see | oci-audit-logs
|publish-to-splunk| splunk_url| The Splunk Cloud URL ( Append input to the beginning of your splunk cloud url, do not add any http/https etc.  | input-prd-p-hh6835czm4rp.cloud.splunk.com
|publish-to-splunk| splunk_hec_token| The Token that is unqiue to that HEC  | TOKEN
|publish-to-splunk| splunk_index_name| The index into which you'd like these logs to get aggregated | main
|publish-to-splunk| stream_ocid| OCID of the Stream used to Publish the actual Audit Event payload | ocid1.stream.oc1.phx.amaaaaaa
|publish-to-splunk| streaming_endpoint| Endpoint of Streaming, depends on which region you provision Streaming | ocid1.stream.oc1.phx.amaaaaaa

## Invoke !
Invoke Once and the loop will stay active as long as the tenancy does continuously pushing events to Splunk . 
```
curl --location --request GET '[apigateway-url].us-phoenix-1.oci.customer-oci.com/regions/listregions'
```
