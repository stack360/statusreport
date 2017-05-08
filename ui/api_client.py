import sys
sys.path.append('..')
from config import *
import requests
import simplejson as json
from functools import wraps
import ui_exceptions

def intercepted(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        print '-'*80, '\n', 'Inputs:\n'
        for arg in args:
            print arg
        response =  f(*args, **kwargs)
        if response.status_code != 200:
            print '='*80, '\nAPI RETURNED ERROR\n', response.text, '\n', '='*80
        else:
            print '-'*80, '\nAPI RESULT\n', response.text, '\n','-'*80

        if response.status_code == 401 or response.status_code == 405:
            raise ui_exceptions.UITokenExpire("Please login again to refresh token")
        return response
    return decorated_function

"""
  Project API
"""
@intercepted
def project_index(token):
    return requests.get(API_SERVER + '/api/projects', headers={'token':token})

@intercepted
def project_by_name(token, project_name):
    return requests.get(API_SERVER + '/api/projects/name/' + project_name, headers={'token': token})

@intercepted
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
@intercepted
def report_index(token, start_filter, end_filter, user_filter):
    user_param = '' if not user_filter else '?user='+user_filter
    return requests.get(API_SERVER + '/api/reports/' + start_filter + '/' + end_filter + user_param, headers={'token':token})

@intercepted
def report_delete(token, id):
    return requests.delete(API_SERVER + '/api/reports/id/' + id, headers={'token':token})

@intercepted
def report_upsert(token, id, data):
    if id:
        data['report_id'] = id
        return requests.put(API_SERVER + '/api/reports/id/' + id, data=json.dumps(data), headers={'token':token})
    else:
        return requests.post(API_SERVER + '/api/reports', data=json.dumps(data), headers={'token': token})

@intercepted
def report_update_comment(token, report_id, data):
    return requests.put(API_SERVER + '/api/reports/id/' + report_id + '/comment', data=json.dumps(data), headers={'token':token})


"""
  Comment API
"""
@intercepted
def comment_create(token, data):
    return requests.post(API_SERVER + '/api/comments', data=json.dumps(data), headers={'token': token})

"""
  User API
"""
@intercepted
def user_index(token):
    return requests.get(API_SERVER + '/api/users', headers={'token':token})

@intercepted
def login(data):
    return requests.post(API_SERVER + '/api/login', data=json.dumps(data))

"""
  Meeting API
"""
@intercepted
def meeting_create(token, data):
    return requests.post(API_SERVER + '/api/meetings', headers={'token':token}, data=json.dumps(data))

@intercepted
def meeting_index(token):
    return requests.get(API_SERVER + '/api/meetings', headers={'token':token})
