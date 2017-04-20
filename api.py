import functools
import simplejson as json
import ast
import exception_handler
import re

from datetime import datetime

from flask import Blueprint, Flask, redirect, url_for, session, jsonify, current_app, make_response, render_template, request, session

from flask_login import login_user, logout_user, login_required, current_user
from flask_principal import Identity, AnonymousIdentity, identity_changed

from models import models, user as user_handler
import utils
# import exception_handler
import random
import werkzeug
from config import *
import requests
from bson import ObjectId
from gmail_client import send_email
import urllib, hashlib


api = Blueprint('api', __name__, template_folder='templates')

def update_user_token(func):
    """decorator used to update user token expire time after api request."""
    @functools.wraps(func)
    def decorated_api(*args, **kwargs):
        response = func(*args, **kwargs)
        current_time = datetime.datetime.now()
        if current_time > current_user.token.expire_timestamp:
            return redirect(url_for('login'))
        user_handler.extend_token(current_user, REMEMBER_COOKIE_DURATION)
        return response
    return decorated_api

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


def _get_gravatar_url(email):
    default = "http://www.myweeklystatus.com/static/image/e.png"
    size = 40

    gravatar_url = "https://www.gravatar.com/avatar/" + hashlib.md5(email.lower()).hexdigest() + "?"
    gravatar_url += urllib.urlencode({'d':default, 's':str(size)})

    return gravatar_url


def _login_with_google_oauth(access_token):
    ### login with google failed
    if access_token is None:
        raise exception_handler.Unauthorized("failed login with google, please retry")

    session['access_token'] = access_token, ''

    headers = {'Authorization': 'OAuth '+access_token}
    res = requests.get('https://www.googleapis.com/oauth2/v1/userinfo?alt=json', headers=headers)

    current_user_email = res.json().get("email")
    first_name = res.json().get("given_name")
    last_name = res.json().get("family_name")
    user_info = {
        "email": current_user_email,
        "first_name": first_name,
        "last_name": last_name
    }
    try:
        google_user = models.User.objects.get(email=current_user_email)
    except models.User.DoesNotExist:
        google_user = None

    return (google_user, user_info)


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
        user, user_info = _login_with_google_oauth(data['access_token'])
        if not user:
            return utils.make_json_response(
                302,
                json.loads('{"error":"Register first", "email":"' + user_info['email'] + '", "first_name":"' + user_info['first_name'] + '", "last_name":"' + user_info['last_name'] + '"}')
            )
    else:
        return utils.make_json_response(
            401,
            json.loads('{"error": "Wrong login credentials"}')
        )

    expire_timestamp = (
        datetime.datetime.now() + REMEMBER_COOKIE_DURATION
    )
    if not user:
        return utils.make_json_response(
            401,
            json.loads('{"error": "Invalid Username and/or password."}')
        )

    success = login_user(user, True, True)
    user.last_login = datetime.datetime.now()
    identity_changed.send(current_app._get_current_object(), identity=Identity(user.username))

    user.token = user_handler.upsert_token(user, REMEMBER_COOKIE_DURATION)
    user.gravatar_url = _get_gravatar_url(user.email)
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

    user = models.User()
    user.username = data['username']
    user.email = data['email']
    user.password = data['password']
    user.first_name = data['first_name']
    user.last_name = data['last_name']
    user.token = user_handler.upsert_token(user, REMEMBER_COOKIE_DURATION)
    user.gravatar_url = _get_gravatar_url(data['email'])
    user.save()

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


@api.route('/api/reports/<string:filtered_time>', methods=['GET'])
@login_required
@update_user_token
def list_reports(filtered_time):
    report_owner = request.args.get('user')
    report_time = datetime.datetime.strptime(filtered_time, "%Y-%m-%d")
    owner = models.User.objects(username=report_owner).first()
    if owner:
        report_list = models.Report.objects(
            owner=owner.id,
            created__gt=report_time,
            created__lt=report_time + datetime.timedelta(10080),
            is_draft=False
        )
    elif not report_owner:
        report_list = models.Report.objects(
            created__gt=report_time,
            created__lt=report_time + datetime.timedelta(10080),
            is_draft=False
        )
    else:
        report_list = []
    print "report list is", report_list
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
        project = models.Project.objects.get(id=pid)
        report.projects.append(project)
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
        [user.to_dict for user in users]
        )


@api.route('/api/users/<string:username>', methods=['GET'])
@login_required
@update_user_token
def get_user(username):
    try:
        user = models.User.objects.get(username=username)
    except models.User.DoesNotExist:
        raise exception_handler.BadRequest(
            "user %s not exist" % username
            )

    return utils.make_json_response(
        200,
        user.to_dict()
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
                message = send_email(to_email, 'Invitation', 'Greetings, \n'+data['username'] +' Invite you to join myweeklystatus.com. Please follow the link below to complete registration. \nhttp://www.myweeklystatus.com/ui/register?email='+to_email)
                result[to_email] = 'sent'
            else:
                result[to_email] = 'ignore'
    return utils.make_json_response(200, result)
