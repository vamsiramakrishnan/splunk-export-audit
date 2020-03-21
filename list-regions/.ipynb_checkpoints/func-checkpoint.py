import io
import json
from oci import pagination
from oci import identity
from oci import auth
from oci import util
from fdk import response
import requests
import os
import datetime


def handler(ctx, data: io.BytesIO = None):
    compartment_url = os.environ["list_compartments_fn_url"]
    signer = auth.signers.get_resource_principals_signer()
    regions = get_regions(signer)
    session = requests.Session()
    end_time = datetime.datetime.utcnow()
    start_time = end_time + datetime.timedelta(
        days=0, seconds=0, microseconds=0, milliseconds=0, minutes=-2, hours=0, weeks=0
    )
    for region in regions.data:
        try:
            x = session.post(
                compartment_url,
                json=json.dumps(
                    {
                        "region": region.region_name,
                        "start_time": start_time,
                        "end_time": end_time,
                    }
                ),
                timeout=1,
            )
        except:
            pass
    return response.Response(
        ctx,
        response_data=json.dumps({"Status": regions.data[0].region_name}),
        headers={"Content-Type": "application/json"},
    )


def get_regions(signer):
    """
    Identifies compartment ID by its name within the particular tenancy
    :param signer: OCI resource principal signer
    :param compartment_name: OCI tenancy compartment name
    :return: OCI tenancy compartment
    """
    identity_client = identity.IdentityClient(config={}, signer=signer)
    result = identity_client.list_region_subscriptions(tenancy_id=signer.tenancy_id)
    return result