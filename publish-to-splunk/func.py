import io
import json
from splunk_http_event_collector import http_event_collector
from fdk import response
from oci import streaming
from oci import util
from oci import auth
from base64 import b64encode, b64decode
from operator import itemgetter
import os


def handler(ctx, data: io.BytesIO = None):
    body = json.loads(data.getvalue())
    signer = auth.signers.get_resource_principals_signer()
    streaming_endpoint = os.environ['streaming_endpoint']
    stream_ocid = os.environ['stream_ocid']
    body = json.loads(data.getvalue())
    offset = body['offset']
    num_records = body['num_records']
    oci_audit_events_payload = read_from_stream(signer, streaming_endpoint, stream_ocid, offset, num_records)
    oci_audit_events_JSON = http_event_collector(
        token=os.environ["splunk_hec_token"],
        host=os.environ["source_host_name"],
        input_type="json",
        http_event_port=os.environ["splunk_hec_port"],
        http_event_server=os.environ["splunk_url"],
    )
    oci_audit_events_JSON.SSL_verify = False
    oci_audit_events_JSON.popNullFields = False
    oci_audit_events_JSON.index = "main"
    for i in oci_audit_events_payload:
        payload = {}
        payload.update({"index": os.environ["splunk_index_name"]})
        payload.update({"sourcetype": "_json"})
        payload.update({"source": os.environ["splunk_source_name"]})
        payload.update({"host": os.environ["source_host_name"]})
        payload.update({"event": i})
        oci_audit_events_JSON.batchEvent(payload)
    oci_audit_events_JSON.flushBatch()
    return response.Response(
        ctx,
        response_data=json.dumps({"event":"success"}),
        headers={"Content-Type": "application/json"},
    )

def read_from_stream(signer, streaming_endpoint, stream_ocid, offset, num_records):
    streaming_client= streaming.StreamClient(config={}, signer=signer, service_endpoint = streaming_endpoint)
    cursor_details = streaming.models.CreateCursorDetails(partition = '0', type = 'AFTER_OFFSET', offset = offset)
    cursor_response = streaming_client.create_cursor(stream_id= stream_ocid, create_cursor_details = cursor_details)
    message_response = streaming_client.get_messages(stream_id= stream_ocid, cursor=cursor_response.data.value, limit = num_records).data
    b64_region_compartment_list = list(map(itemgetter('value'),util.to_dict(message_response)))
    result = list(map(lambda x: json.loads(b64decode(x).decode()), b64_region_compartment_list))
    return result