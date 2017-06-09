import sys
sys.path.append('..')
from config import *
import requests
import simplejson as json
from functools import wraps
import ui_exceptions
from flask import current_app as app

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

        if response.status_code in [401, 405]:
            raise ui_exceptions.UITokenExpire("Please login again to refresh token")
        if response.status_code in [400, 404, 500]:
            raise ui_exceptions.GeneralError(response.json()['message'])
        return response.json()
    return decorated_function

"""
  Project API
"""
@intercepted
def project_index(token):
    return requests.get(app.config['API_SERVER'] + '/api/projects', headers={'token':token})

@intercepted
def project_user_index(token, project_name):
    return requests.get(app.config['API_SERVER'] + '/api/projects/name/' + project_name + '/users', headers={'token':token})

@intercepted
def project_by_name(token, project_name):
    return requests.get(app.config['API_SERVER'] + '/api/projects/name/' + project_name, headers={'token': token})

@intercepted
def project_by_id(token, id):
    return requests.get(app.config['API_SERVER'] + '/api/projects/id/' + id, headers={'token': token})

@intercepted
def delete_project(token, id):
    return requests.delete(app.config['API_SERVER'] + '/api/projects/id/' + id + '/delete', headers={'token': token})

@intercepted
def upload_project_logo(token, project_id, logo_file):
    files = {'file': (logo_file.filename, logo_file, logo_file.content_type)}
    return requests.post(app.config['API_SERVER'] + '/api/projects/id/' + project_id + '/logo_upload', headers={'token':token}, files=files)

@intercepted
def project_upsert(token, id, data):
    if id:
        return requests.put(app.config['API_SERVER'] + '/api/projects/id/' + id, data=json.dumps(data), headers={'token':token})
    else:
        return requests.post(app.config['API_SERVER']+'/api/projects', data=json.dumps(data), headers={'token':token})


"""
  Report API
"""
@intercepted
def report_index(token, start_filter, end_filter, user_filter, project_filter):
    params = [
        '' if not user_filter else 'user='+user_filter,
        '' if not project_filter else 'project='+project_filter
    ]
    params = filter(lambda x: x, params)
    querystr = '?'+'&'.join(params)
    return requests.get(app.config['API_SERVER'] + '/api/reports/' + start_filter + '/' + end_filter + querystr, headers={'token':token})

@intercepted
def report_show(token, id):
    return requests.get(app.config['API_SERVER'] + '/api/reports/id/'+ id, headers={'token':token})

@intercepted
def report_delete(token, id):
    return requests.delete(app.config['API_SERVER'] + '/api/reports/id/' + id, headers={'token':token})

@intercepted
def report_upsert(token, id, data):
    if id:
        data['report_id'] = id
        return requests.put(app.config['API_SERVER'] + '/api/reports/id/' + id, data=json.dumps(data), headers={'token':token})
    else:
        return requests.post(app.config['API_SERVER'] + '/api/reports', data=json.dumps(data), headers={'token': token})

@intercepted
def report_update_comment(token, report_id, data):
    return requests.put(app.config['API_SERVER'] + '/api/reports/id/' + report_id + '/comment', data=json.dumps(data), headers={'token':token})


"""
  Comment API
"""
@intercepted
def comment_create(token, data):
    return requests.post(app.config['API_SERVER'] + '/api/comments', data=json.dumps(data), headers={'token': token})

"""
  User API
"""
@intercepted
def user_index(token, show_manager_lead='false'):
    return requests.get(app.config['API_SERVER'] + '/api/users' + '?show_manager_lead=' + show_manager_lead, headers={'token':token})

def login(data):
    return requests.post(app.config['API_SERVER'] + '/api/login', data=json.dumps(data))

@intercepted
def user_by_username(token, username):
    return requests.get(app.config['API_SERVER'] + '/api/users/username/' + username, headers={'token':token})

def get_user_view_list(token, project=None):
    if not project:
        return user_index(token, 'false')
    return project_user_index(token, project)

"""
  Meeting API
"""
@intercepted
def meeting_create(token, data):
    return requests.post(app.config['API_SERVER'] + '/api/meetings', headers={'token':token}, data=json.dumps(data))

@intercepted
def meeting_index(token):
    return requests.get(app.config['API_SERVER'] + '/api/meetings', headers={'token':token})

@intercepted
def meeting_show(token, id):
    return requests.get(app.config['API_SERVER'] + '/api/meetings/'+id, headers={'token':token})


"""
  Team API
"""
@intercepted
def team_index(token):
    return requests.get(app.config['API_SERVER'] + '/api/teams', headers={'token':token})

@intercepted
def team_show(token, id):
    return requests.get(app.config['API_SERVER'] + '/api/teams/id/'+ id, headers={'token':token})

@intercepted
def team_create(token, name):
    return requests.post(app.config['API_SERVER'] + '/api/teams', headers={'token':token}, data=json.dumps({'name':name}))

@intercepted
def team_invite(token, data):
    return requests.post(app.config['API_SERVER'] + '/api/teams/invite', headers={'token':token}, data=json.dumps(data))

@intercepted
def team_leave(token, id):
    return requests.get(app.config['API_SERVER'] + '/api/teams/leave/'+ id, headers={'token':token})
