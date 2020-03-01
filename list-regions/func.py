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
    compartment_url= os.environ['list_compartments_fn_url']
    wait_loop_time= os.environ['wait_loop_time']
    region_url= os.environ['list_regions_fn_url']
    wait_loop_url=os.environ['wait_loop_fn_url']
    signer = auth.signers.get_resource_principals_signer()
    regions = get_regions(signer)
    session = requests.Session()
    for region in regions.data: 
        try:
            x = session.post(compartment_url, json= {"region": region.region_name}, timeout=1)
        except:
            pass

    try:
        x = session.post(wait_loop_url, json={"time": wait_loop_time, "url": region_url}, timeout=1)
    except:
        pass

    return response.Response(ctx, response_data=json.dumps({"Status": regions.data[0].region_name}), headers={"Content-Type": "application/json"})

def get_regions(signer):
    """
    Identifies compartment ID by its name within the particular tenancy
    :param signer: OCI resource principal signer
    :param compartment_name: OCI tenancy compartment name
    :return: OCI tenancy compartment
    """
    identity_client = identity.IdentityClient(config={}, signer=signer)
    result = identity_client.list_region_subscriptions(tenancy_id= signer.tenancy_id)
    return result

