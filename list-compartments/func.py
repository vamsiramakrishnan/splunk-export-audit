import io
import json

from oci import pagination
from oci import identity
from oci import auth
from oci import util
from fdk import response
import requests
import os

def handler(ctx, data: io.BytesIO=None):
    signer = auth.signers.get_resource_principals_signer()
    audit_url= os.environ['fetch_audit_events_fn_url']
    compartments = get_compartments(signer)
    body = json.loads(data.getvalue())
    region = str(body["region"])
    session = requests.Session()
    for compartment in compartments:
        try:
            x = session.post(audit_url, json={"region": region , "compartment": compartment['id']}, timeout=0.2)
        except:
            pass
    return response.Response( ctx, response_data=json.dumps({"Status": compartments}), headers={"Content-Type": "application/json"})

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
        compartment_id= signer.tenancy_id,
        compartment_id_in_subtree=True,
        access_level="ACCESSIBLE"
    )
    compartment_ocids.extend(util.to_dict(result.data))
    return compartment_ocids

