import io
import json

from oci import audit
from oci import pagination
from oci import identity
from oci import auth
from oci import util
from fdk import response
import datetime
import requests
import os

def handler(ctx, data: io.BytesIO=None):
    signer = auth.signers.get_resource_principals_signer()
    compartment = ""
    region = ""
    try:
        body = json.loads(data.getvalue())
        compartment = str(body["compartment"])
        region = str(body["region"])
    except Exception as ex:
        print("Exception Hit Here")
    splunk_url= os.environ['publish_to_splunk_fn_url']
    audit_events = get_audit_events(region, compartment, signer)
    session = requests.Session()
    for audit_event in audit_events:
        try:
            x = session.post(splunk_url, json.dumps(audit_event),timeout=0.1)
        except:
            pass
    return response.Response(
        ctx, response_data=json.dumps({"status":"success"}),
        headers={"Content-Type": "application/json"}
    )

def get_audit_events(region, compartment, signer):
    audit_events=[]
    end_time = datetime.datetime.utcnow()
    start_time = end_time + datetime.timedelta(days=0, seconds=0, microseconds=0, milliseconds=0, minutes=-2, hours=0, weeks=0)
    audit_client = audit.audit_client.AuditClient(config={}, signer=signer)
    audit_client.base_client.set_region(region)
    result = pagination.list_call_get_all_results(audit_client.list_events,compartment_id=compartment,
            start_time=start_time,
            end_time=end_time)
    audit_events.extend(util.to_dict(result.data))
    return audit_events
