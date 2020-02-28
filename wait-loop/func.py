import io
import json
from time import sleep
from fdk import response


def handler(ctx, data: io.BytesIO=None):
    try:
        body = json.loads(data.getvalue())
        sleep_time = body.get("time")
        next_fn_url = body.get("url")
    except (Exception, ValueError) as ex:
        print(str(ex))
    sleep(sleep_time)
    try:
        x = session.get(next_fn_url, timeout=0.1)
    except:
        pass
    return response.Response(
        ctx, response_data=json.dumps(
            {"message": "success"}),
        headers={"Content-Type": "application/json"}
    )
