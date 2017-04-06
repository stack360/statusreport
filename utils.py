import simplejson as json
import crypt

from flask import request, make_response

import exception_handler

def get_request_data():
    if request.data:
        try:
            data = json.loads(request.data)
        except Exception:
            raise exception_handler.BadRequest(
                'request data is not json formatted: %s' % request.data
            )
        if not isinstance(data, dict):
            raise exception_handler.BadRequest(
                'request data is not json formatted dict: %s' % request.data
            )
        return data
    else:
        return {}


def make_json_response(status_code, data):
    """Wrap json format to the reponse object."""
    #with open('/tmp/debug', 'w+') as f:
     #   f.write(str(data))
    result = json.dumps(data)
    resp = make_response(result, status_code)
    resp.headers['Content-type'] = 'application/json'

    return resp

def shifttimedelta(td):
    return td.days, td.seconds//3600, (td.seconds//60)%60
