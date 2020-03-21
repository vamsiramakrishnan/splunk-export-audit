import io
import json
from splunk_http_event_collector import http_event_collector
from fdk import response
import os


def handler(ctx, data: io.BytesIO = None):
    body = json.loads(data.getvalue())
    oci_audit_events_JSON = http_event_collector(
        token=os.environ["splunk_hec_token"],
        host=os.environ["source_host_name"],
        input_type="json",
        http_event_port="8088",
        http_event_server=os.environ["splunk_url"],
    )
    oci_audit_events_JSON.SSL_verify = False
    oci_audit_events_JSON.popNullFields = False
    oci_audit_events_JSON.index = "main"
    payload = {}
    payload.update({"index": os.environ["splunk_index_name"]})
    payload.update({"sourcetype": "_json"})
    payload.update({"source": os.environ["splunk_source_name"]})
    payload.update({"host": os.environ["source_host_name"]})
    payload.update({"event": body})
    oci_audit_events_JSON.sendEvent(payload)
    return response.Response(
        ctx,
        response_data=oci_audit_events_JSON.sendEvent(payload),
        headers={"Content-Type": "application/json"},
    )