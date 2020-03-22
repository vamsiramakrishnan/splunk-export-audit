import io
import json
from oci import pagination
from oci import identity
from oci import auth
from oci import util
from oci import streaming
from oci import audit
from oci import ons
from fdk import response
import requests
import os
import datetime
from base64 import b64encode, b64decode
from operator import itemgetter

def handler(ctx, data: io.BytesIO=None):
    
    streaming_endpoint = os.environ['streaming_endpoint']
    stream_ocid = os.environ['stream_ocid']
    records_per_fn =  int(os.environ['records_per_fn'])
    splunk_topic = os.environ['splunk_topic']
    signer = auth.signers.get_resource_principals_signer()
    body = json.loads(data.getvalue())
    offset = body['offset']
    num_records = body['num_records']
    records = read_from_stream(signer, streaming_endpoint, stream_ocid, offset, num_records)
    audit_events=[]
    for record in records:
        audit_events.extend(get_audit_events(region = record['region'], 
                                        compartment = record['compartment'], 
                                        start_time= datetime.datetime.strptime(record['start_time'],'%m/%d/%y %H:%M:%S'), 
                                        end_time = datetime.datetime.strptime(record['end_time'],'%m/%d/%y %H:%M:%S'), 
                                        signer = signer))
    if len(audit_events)>records_per_fn:
        for i in range(0, len(audit_events), records_per_fn):
            stream_response = publish_to_stream(signer, streaming_endpoint, stream_ocid, audit_events[i:i+records_per_fn])
            offset = int(util.to_dict(stream_response)['entries'][0]['offset'])
            num_records = len(util.to_dict(stream_response)['entries'])
            publish_notifications(signer, splunk_topic, offset, num_records, records_per_fn=records_per_fn)
    else:
        stream_response = publish_to_stream(signer, streaming_endpoint, stream_ocid, audit_events)
        offset = int(util.to_dict(stream_response)['entries'][0]['offset'])
        num_records = len(util.to_dict(stream_response)['entries'])
        publish_notifications(signer, splunk_topic, offset, num_records, records_per_fn)
    
    return response.Response(
        ctx, response_data=json.dumps({"status":"success"}),
        headers={"Content-Type": "application/json"}
    )

def get_audit_events(region, compartment, start_time, end_time, signer):
    audit_events=[]
    audit_client = audit.audit_client.AuditClient(config={}, signer=signer)
    audit_client.base_client.set_region(region)
    result = util.to_dict(pagination.list_call_get_all_results(audit_client.list_events, compartment_id=compartment,
            start_time=start_time,
            end_time=end_time).data)
    return result


def read_from_stream(signer, streaming_endpoint, stream_ocid, offset, num_records):
    streaming_client= streaming.StreamClient(config={}, signer=signer, service_endpoint = streaming_endpoint)
    cursor_details = streaming.models.CreateCursorDetails(partition = '0', type = 'AFTER_OFFSET', offset = offset)
    cursor_response = streaming_client.create_cursor(stream_id= stream_ocid, create_cursor_details = cursor_details)
    message_response = streaming_client.get_messages(stream_id= stream_ocid, cursor=cursor_response.data.value, limit = num_records).data
    b64_region_compartment_list = list(map(itemgetter('value'),util.to_dict(message_response)))
    result = list(map(lambda x: json.loads(b64decode(x).decode()), b64_region_compartment_list))
    return result


def publish_to_stream(signer, streaming_endpoint, stream_ocid, audit_events):
    streaming_client= streaming.StreamClient(config={}, signer=signer, service_endpoint = streaming_endpoint)
    msg_list = []
    identifier = "audit_events"
    msg_details = streaming.models.PutMessagesDetails()
    for audit_event in audit_events:
        message_json = json.dumps(audit_event)
        msg_key = b64encode(identifier.encode()).decode()
        msg_value = b64encode(message_json.encode()).decode()
        msg_list.append(streaming.models.PutMessagesDetailsEntry(key =  msg_key , value = msg_value))
    msg_details.messages = msg_list
    result  = streaming_client.put_messages(stream_ocid ,msg_details).data
    return result


def publish_notifications(signer, splunk_topic, offset, num_records, records_per_fn):
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
            notification_client.publish_message(topic_id= splunk_topic , message_details=notification_message_details)
    else:
        notification_message_details = ons.models.MessageDetails(title = "Trigger Fetch Audit events", 
                                                                 body = json.dumps({"offset": offset, 
                                                                                    "num_records":num_records}))
        notification_client.publish_message(topic_id= splunk_topic , 
                                            message_details=notification_message_details)
        
    return {"result": "Success"}