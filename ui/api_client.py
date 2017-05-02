import sys
sys.path.append('..')
from config import *
import requests
import simplejson as json
from functools import wraps

def intercepted(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        response =  f(*args, **kwargs)
        if response.status_code != 200:
            print '='*80, '\nAPI RETURNED ERROR\n', response.text, '\n', '='*80
        else:
            print '-'*80, '\nAPI RESULT\n', response.text, '\n','-'*80
        return response
    return decorated_function

"""
  Project API
"""
def project_index(token):
    return requests.get(API_SERVER + '/api/projects', headers={'token':token})

def project_by_name(token, project_name):
    return requests.get(API_SERVER + '/api/projects/name/' + project_name, headers={'token': token})

def project_by_id(token, id):
    return requests.get(API_SERVER + '/api/projects/id/' + id, headers={'token': token})

@intercepted
def upload_project_logo(token, project_id, logo_file):
    files = {'file': (logo_file.filename, logo_file, logo_file.content_type)}
    return requests.post(API_SERVER + '/api/projects/id/' + project_id + '/logo_upload', headers={'token':token}, files=files)

@intercepted
def project_upsert(token, id, data):
    if id:
        return requests.put(API_SERVER + '/api/projects/id/' + id, data=json.dumps(data), headers={'token':token})
    else:
        return requests.post(API_SERVER+'/api/projects', data=json.dumps(data), headers={'token':token})
"""
  Report API
"""
def report_index(token, week_filter, user_filter):
    user_param = '' if not user_filter else '?user='+user_filter
    return requests.get(API_SERVER + '/api/reports/' + week_filter + user_param, headers={'token':token})

def report_delete(token, id):
    return requests.delete(API_SERVER + '/api/reports/id/' + id, headers={'token':token})

def report_upsert(token, id, data):
    if id:
        data['report_id'] = id
        return requests.put(API_SERVER + '/api/reports/id/' + id, data=json.dumps(data), headers={'token':token})
    else:
        return requests.post(API_SERVER + '/api/reports', data=json.dumps(data), headers={'token': token})

"""
  User API
"""
def user_index(token):
    return requests.get(API_SERVER + '/api/users', headers={'token':token})
