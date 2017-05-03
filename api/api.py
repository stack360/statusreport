import functools
import simplejson as json
import ast
import exception_handler
import re
import facebook

from datetime import datetime

from flask import g, Blueprint, Flask, redirect, url_for, session, jsonify, current_app, make_response, render_template, request, session

from flask_login import login_user, logout_user, login_required, current_user
from flask_principal import Identity, AnonymousIdentity, identity_changed

import os, sys

statusreport_dir = os.path.dirname(os.path.realpath(__file__ + "/../../"))
sys.path.append(statusreport_dir)

from statusreport.models import models

import project as project_api
import user as user_api
from statusreport import utils
import utils as api_utils
import random
import werkzeug
from werkzeug.utils import secure_filename

from statusreport.config import *
import requests
from bson import ObjectId
from statusreport.gmail_client import send_email


api = Blueprint('api', __name__, template_folder='templates')



def update_user_token(func):
    """decorator used to update user token expire time after api request."""
    @functools.wraps(func)
    def decorated_api(*args, **kwargs):
        response = func(*args, **kwargs)
        current_time = datetime.datetime.now()
        if current_time > current_user.token.expire_timestamp:
            raise exception_handler.TokenExpire("Please login again for token refresh")
        user_api.extend_token(current_user, REMEMBER_COOKIE_DURATION)
        return response
    return decorated_api


def manager_required(func):
    """decorator used to require manager role to certain view functions."""
    @functools.wraps(func)
    def decorated_api(*args, **kwargs):
        if not current_user.is_superuser:
            raise exception_handler.Forbidden("Only Manager can perform this.")
        return func(*args, **kwargs)
    return decorated_api


def lead_required(func):
    """decorator used to require project lead role to certain view functions."""
    @functools.wraps(func)
    def decorated_api(project_id):
        try:
            project = models.Project.objects.get(id=project_id)
        except IndexError:
            raise exception_handler.ItemNotFound("Project not found")
        if current_user.username == project.lead.username:
            return func(project_id)
        else:
            raise exception_handler.Forbidden("Only Manager or Project Lead can do this.")
    return decorated_api


def _upsert_project(project, data):
    for k, v in data.iteritems():
        if k == 'members':
            v = [models.User.objects.get(id=m_id) for m_id in v]
        if k == 'lead':
            v = models.User.objects.get(id=v)
        setattr(project, k, v)
    project.save()
    return project

def _get_request_args(**kwargs):
    args = dict(request.args)
    for key, value in args.items():
        if key in kwargs:
            converter = kwargs[key]
            if isinstance(value, list):
                args[key] = [converter(item) for item in value]
            else:
                args[key] = converter(value)
    return args


def _get_google_profile(access_token):
    headers = {'Authorization': 'OAuth '+access_token}
    res = requests.get('https://www.googleapis.com/oauth2/v1/userinfo?alt=json', headers=headers)

    current_user_email = res.json().get("email")
    first_name = res.json().get("given_name")
    last_name = res.json().get("family_name")
    return {
        "email": current_user_email,
        "first_name": first_name,
        "last_name": last_name
    }


def _get_facebook_profile(access_token):
    graph = facebook.GraphAPI(access_token)
    profile = graph.get_object('me')
    args = {'fields' : 'id,first_name,last_name,email', }
    profile = graph.get_object('me', **args)

    return profile

def _login(username, password, use_cookie):
    try:
        user = models.User.objects.get(username=username)
        if not user.verify_password(password):
            user = None
    except models.User.DoesNotExist:
        user = None
    return user


@api.route('/api/login', methods=['POST'])
def login():
    data = utils.get_request_data()
    if 'username' in data and 'password' in data:
        user = _login(data['username'], data['password'], True)
    elif 'access_token' in data:
        if data['channel'] == 'google':
            profile = _get_google_profile(data['access_token'])
        elif data['channel'] == 'facebook':
            profile = _get_facebook_profile(data['access_token'])
        else:
            profile = {'email':None }

        try:
            user = models.User.objects.get(email=profile['email'])
        except models.User.DoesNotExist:
            return utils.make_json_response(
                307,
                {'message':'new oauth user', 'email':profile['email']}
            )
    else:
        raise exception_handler.Unauthorized('No login credentials detected')

    expire_timestamp = (
        datetime.datetime.now() + REMEMBER_COOKIE_DURATION
    )
    if not user:
        raise exception_handler.Unauthorized('Invalide username and/or password')

    success = login_user(user, True, True)
    user.last_login = datetime.datetime.now()
    identity_changed.send(current_app._get_current_object(), identity=Identity(user.username))

    user.token = user_api.upsert_token(user, REMEMBER_COOKIE_DURATION)
    user.gravatar_url = api_utils._get_gravatar_url(user.email)
    user.save()
    return utils.make_json_response(200, user.to_dict())


@api.route('/api/logout', methods=['POST'])
@login_required
def logout():
    user = models.User.objects.get(username=current_user.username)
    token_object = models.Token.objects.get(token=user.token.token)
    user.token.delete()
    token_object.delete()
    logout_user()

    for key in ('identity.name', 'identity.auth_type'):
        session.pop(key, None)

    identity_changed.send(current_app._get_current_object(), identity=AnonymousIdentity())
    return utils.make_json_response(
        200,
        user.to_dict()
        )


@api.route('/api/register', methods=['POST'])
def register():
    data = utils.get_request_data()

    if (models.User.objects.filter(username=data["username"]).count() > 0 or
    models.User.objects.filter(email=data["email"]).count() > 0):
        raise exception_handler.BadRequest("user already exist")

    user = user_api.create_user(**data)
    return utils.make_json_response(
        200,
        user.to_dict()
        )

@api.route('/api/listtasks/<string:status>', methods=['GET'])
@login_required
def list_tasks(status):
    if status == "all":
        tasks = models.Task.objects.order_by('-due_time')
    else:
        tasks = models.Task.objects.filter(status=status)

    tasks_dict = {}
    for task in tasks:
        tasks_dict.update({task.title: task.to_dict()})

    return utils.make_json_response(
        200,
        tasks_dict
        )


@api.route('/api/tasks/<string:tasktitle>', methods=['GET'])
@login_required
def get_task(tasktitle):
    try:
        task = models.Task.objects.get(title=tasktitle)
    except models.Task.DoesNotExist:
        raise exception_handler.ItemNotFound(
            "task %s not exist" % tasktitle
            )
    return utils.make_json_response(
        200,
        task.to_dict()
        )

@api.route('/api/tasks', methods=['POST'])
@login_required
def create_task():
    data = utils.get_request_data()

    task = models.Task()

    task.title = data['title']
    task.content = data['content']
    task.manager = models.User.objects.get(username=data['manager'])

    for assign in data['assignee']:
        task.assignee.append(models.User.objects.get(username=assign))

    task.status = data['status']
    task.tags = data['tags']
    task.due_time = datetime.datetime.strptime(data['due_time'], '%b %d %Y %I:%M%p')
    task.pub_time = datetime.datetime.now()
    task.update_time = datetime.datetime.now()

    if task.pub_time < task.due_time:
        task.save()
        return utils.make_json_response(
            200,
            task.to_dict()
            )
    else:
        raise exception_handler.BadRequest(
            'due time %s is earlier than pub time %s' % (
                    data['due_time'], datetime.datetime.now()
                )
            )


@api.route('/api/tasks/<string:tasktitle>', methods=['PUT'])
@login_required
def update_task(tasktitle):
    data = utils.get_request_data()

    try:
        task = models.Task.objects.get(title=tasktitle)
    except models.Task.DoesNotExist:
        raise exception_handler.BadRequest(
            'task %s not exist' % tasktitle
            )
    if data.get('title'):
        task.title = data['title']

    if data.get('content'):
        task.content = data['content']
    if data.get('status') and data['status'] in ['todo', 'ongoing'] and datetime.datetime.now() > task.due_time:
        raise exception_handler.BadRequest(
            'due time %s already passed' % task.due_time
            )
    if data.get('status') and data['status'] == 'overdue' and datetime.datetime.now() < task.due_time:
        left_days, left_hours, left_minutes = utils.shifttimedelta(task.due_time - datetime.datetime.now())
        raise exception_handler.BadRequest(
            'still %s days %s hours %s minutes left' % (
                    left_days, left_hours, left_minutes
                )
            )
    if data.get('status'):
        task.status = data['status']
    if data.get('tags'):
        task.tags = data['tags']
    if data.get('due_time'):
        task.due_time = datetime.datetime.strptime(data['due_time'], '%b %d %Y %I:%M%p')
    task.update_time = datetime.datetime.now()
    task.save()
    return utils.make_json_response(
        200,
        task.to_dict()
        )


@api.route('/api/usertasks/<string:username>/<string:status>', methods=['GET'])
@login_required
def get_user_tasks(username, status):
    if status == "all":
        tasks = models.Task.objects.order_by('-due_time')
    else:
        tasks = models.Task.objects.filter(status=status).order_by('-due_time')

    user_task_dict = {}
    for task in tasks:
        if username in [user.username for user in task.assignee] or username == task.manager.username:
            user_task_dict.update({task.title: task.to_dict()})

    return utils.make_json_response(
        200,
        user_task_dict
        )


@api.route('/api/projects', methods=['GET'])
@login_required
@update_user_token
def list_projects():
    projects = project_api.get_projects_by_username(current_user)
    return utils.make_json_response(
        200,
        projects
    )


@api.route('/api/projects/name/<string:project_name>', methods=['GET'])
@login_required
@update_user_token
def get_project(project_name):
    project = project_api.get_project_by_name(project_name)
    if not project:
        raise exception_handler.BadRequest(
            "project %s does not exist" % project_name
            )
    return utils.make_json_response(
        200,
        project
    )

@api.route('/api/projects/id/<string:project_id>', methods=['GET'])
@login_required
@update_user_token
def get_project_by_id(project_id):
    project = project_api.get_project_by_id(project_id)
    if not project:
        raise exception_handler.BadRequest(
            "project %s does not exist" % project_name
            )
    return utils.make_json_response(
        200,
        project
    )


@api.route('/api/projects', methods=['POST'])
@login_required
@manager_required
@update_user_token
def add_project():
    data = utils.get_request_data()
    project = project_api.create_project(**data)

    return utils.make_json_response(
        200,
        project
    )

@api.route('/api/projects/id/<string:project_id>/logo_upload', methods=['POST'])
@login_required
@lead_required
@update_user_token
def upload_project_logo(project_id):
    logo_file = request.files['file']
    if logo_file and api_utils.filetype_allowed(logo_file.filename):
        filename = secure_filename(logo_file.filename)
        logo_file.save(os.path.join(PROJECT_LOGO_DIR, filename))
        project = project_api.update_project(project_id, logo_file=filename)

    return utils.make_json_response(
        200,
        json.loads('{"message": "Logo uploaded."}')
    )



@api.route('/api/projects/id/<string:project_id>', methods=['put'])
@login_required
@lead_required
@update_user_token
def update_project(project_id):
    data = utils.get_request_data()
    project = project_api.update_project(project_id, **data)
    return utils.make_json_response(
        200,
        project
    )


@api.route('/api/reports/<string:filtered_start>/<string:filtered_end>', methods=['GET'])
@login_required
@update_user_token
def list_reports(filtered_start, filtered_end):
    report_owner = request.args.get('user')
    # report_time = datetime.datetime.strptime(filtered_time, "%Y-%m-%d")
    owner = models.User.objects(username=report_owner).first()
    if owner:
        report_list = models.Report.objects(
            owner=owner.id,
            created__gt=filtered_start,
            created__lt=filtered_end,
            is_draft=False
        ).order_by('-created')
    elif not report_owner:
        report_list = models.Report.objects(
            created__gt=filtered_start,
            created__lt=filtered_end,
            is_draft=False
        ).order_by('-created')
    else:
        report_list = []
    return_report_list = [r.to_dict() for r in report_list]
    return utils.make_json_response(
        200,
        return_report_list
    )


@api.route('/api/reports', methods=['POST'])
@login_required
@update_user_token
def add_report():
    data = utils.get_request_data()
    is_draft = False
    if data['is_draft']:
        is_draft = True

    try:
        report = models.Report.objects(is_draft=True)[0]
    except IndexError:
        report = models.Report()

    for pid in data['projects']:
        try:
            project = models.Project.objects.get(id=pid)
            report.projects.append(project)
        except Exception:
            pass
    report.owner = models.User.objects.get(username=data['user'])
    report.created = datetime.datetime.now()
    report.content = data['content']
    report.is_draft = is_draft
    report.save()
    return utils.make_json_response(
        200,
        report.to_dict()
    )

@api.route('/api/reports/id/<string:report_id>', methods=['PUT'])
@login_required
@update_user_token
def update_report(report_id):
    data = utils.get_request_data()
    report = models.Report.objects.get(id=ObjectId(report_id))

    report.content = data['content']
    report.save()
    return utils.make_json_response(
        200,
        report.to_dict()
    )

@api.route('/api/reports/id/<string:report_id>', methods=['DELETE'])
@login_required
@update_user_token
def delete_report(report_id):
    report = models.Report.objects.get(id=ObjectId(report_id))
    report.delete()
    print "delete: ", report.to_dict()
    return utils.make_json_response(
        200,
        {}
    )


@api.route('/api/users', methods=['GET'])
@login_required
@update_user_token
def get_all_users():
    users = models.User.objects.all()
    return utils.make_json_response(
        200,
        [user.to_dict() for user in users]
        )


@api.route('/api/users/username/<string:username>', methods=['GET'])
@login_required
@update_user_token
def get_user(username):
    user = user_api.get_user_by_username(username)
    if not user:
        raise exception_handler.BadRequest(
            "user %s not exist" % username
            )

    return utils.make_json_response(
        200,
        user.to_dict()
        )


@api.route('/api/users/username/<string:username>', methods=['PUT'])
@login_required
@update_user_token
def update_user(username):
    data = utils.get_request_data()
    result = user_api.update_user(username, **data)

    return utils.make_json_response(
        200,
        result
        )


@api.route('/')
def dashboard_url():
  return redirect("/ui/report/index", code=302)


@api.route('/api/invite', methods=['POST'])
@login_required
@update_user_token
def send_invitation():
    data = utils.get_request_data()
    result = {}
    if data.has_key('emails'):
        for to_email in data['emails'].split(','):

            if re.match(r"[^@]+@[^@]+\.[^@]+", to_email):
                message = send_email(to_email, 'Invitation', 'invitation.html', {'email':to_email, 'fullname':data['fullname']} )
                result[to_email] = 'sent'
            else:
                result[to_email] = 'ignore'
    return utils.make_json_response(200, result)
