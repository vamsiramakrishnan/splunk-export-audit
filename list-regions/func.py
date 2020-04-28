import io
import json
from oci import pagination
from oci import identity
from oci import auth
from oci import util
from oci import streaming
from oci import ons
from fdk import response
import requests
import os
import datetime
from base64 import b64encode, b64decode
from operator import itemgetter


def handler(ctx, data: io.BytesIO = None):
    audit_topic = os.environ['audit_topic']
    streaming_endpoint = os.environ['streaming_endpoint']
    stream_ocid = os.environ['stream_ocid']
    records_per_fn =  int(os.environ['records_per_fn'])
    signer = auth.signers.get_resource_principals_signer()
    regions = util.to_dict(get_regions(signer))
    compartments = util.to_dict(get_compartments(signer))
    activeCompartments = [compartment for compartment in compartments if compartment['lifecycle_state'] == 'ACTIVE']
    compartment_ocids = list(map(itemgetter('id'),activeCompartments))
    region_names = list(map(itemgetter('region_name'),regions))
    end_time_object = datetime.datetime.utcnow()
    start_time_object = end_time_object + datetime.timedelta(days=0, seconds=0, microseconds=0, milliseconds=0, minutes=-5, hours=0, weeks=0)
    start_time = start_time_object.strftime('%m/%d/%y %H:%M:%S')
    end_time = end_time_object.strftime('%m/%d/%y %H:%M:%S')
    stream_response = publish_to_stream(signer, streaming_endpoint, stream_ocid, region_names, compartment_ocids, start_time, end_time)
    offset = int(util.to_dict(stream_response)['entries'][0]['offset'])
    num_records = len(util.to_dict(stream_response)['entries'])
    publish_notifications(signer, audit_topic, offset, num_records, records_per_fn)
    return response.Response(ctx, 
                             response_data=json.dumps({
                                 "offset": offset,
                                 "num_records": num_records
                             }), 
                             headers={"Content-Type": "application/json"})

def get_regions(signer):
    """
    Identifies compartment ID by its name within the particular tenancy
    :param signer: OCI resource principal signer
    :param compartment_name: OCI tenancy compartment name
    :return: OCI tenancy compartment
    """
    identity_client = identity.IdentityClient(config={}, signer=signer)
    result = identity_client.list_region_subscriptions(tenancy_id=signer.tenancy_id).data
    return result

def get_compartments(signer):
    """
    Identifies compartment ID by its name within the particular tenancy
    :param signer: OCI resource principal signer
    :param compartment_name: OCI tenancy compartment name
    :return: OCI tenancy compartment
    """
    compartment_ocids = []
    identity_client = identity.IdentityClient(config={}, signer=signer)
    result = pagination.list_call_get_all_results(
        identity_client.list_compartments,
        compartment_id=signer.tenancy_id,
        compartment_id_in_subtree=True,
        access_level="ACCESSIBLE").data
    
    return result

def publish_to_stream(signer, streaming_endpoint, stream_ocid, region_names, compartment_ocids, start_time, end_time):
    streaming_client= streaming.StreamClient(config={}, signer=signer, service_endpoint = streaming_endpoint)
    msg_list = []
    identifier = "region_compartment"
    msg_details = streaming.models.PutMessagesDetails()
    for region_name in region_names:
        for compartment_ocid in compartment_ocids:
            message_json = json.dumps({"region":region_name, 
                                       "compartment":compartment_ocid, 
                                       "start_time": start_time, 
                                       "end_time":end_time})
            msg_key = b64encode(identifier.encode()).decode()
            msg_value = b64encode(message_json.encode()).decode()
            msg_list.append(streaming.models.PutMessagesDetailsEntry(key =  msg_key , value = msg_value))
    msg_details.messages = msg_list
    result  = streaming_client.put_messages(stream_ocid ,msg_details).data
    return result

def publish_notifications(signer, audit_topic, offset, num_records, records_per_fn):
    notification_client = ons.NotificationDataPlaneClient(config={}, signer=signer)
    if num_records > records_per_fn:
        for new_offset in range(offset, offset + num_records, records_per_fn):
            if new_offset + records_per_fn > offset +num_records: 
                new_num_records = offset + num_records - new_offset
            else:
                new_num_records = records_per_fn
            notification_message_details = ons.models.MessageDetails(title = "Trigger Fetch Audit events", 
                                                                     body = json.dumps({"offset": new_offset, 
                                                                                        "num_records":new_num_records}))
            notification_client.publish_message(topic_id= audit_topic , message_details=notification_message_details)
    else:
        notification_message_details = ons.models.MessageDetails(title = "Trigger Fetch Audit events", 
                                                                 body = json.dumps({"offset": offset, 
                                                                                    "num_records":num_records}))
        notification_client.publish_message(topic_id= audit_topic , 
                                            message_details=notification_message_details)
        
    return {"result": "Success"}
    
    