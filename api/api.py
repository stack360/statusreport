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

from mongoengine.queryset.visitor import Q

statusreport_dir = os.path.dirname(os.path.realpath(__file__ + "/../../"))
sys.path.append(statusreport_dir)

from statusreport.models import models

import meeting as meeting_api
import project as project_api
import team as team_api
import user as user_api
import report as report_api
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
        if current_user.username == project.lead.username or current_user.is_superuser:
            return func(project_id)
        else:
            raise exception_handler.Forbidden("Only Manager or Project Lead can do this.")
    return decorated_api


def _digest_reports(report_list):
    digest = ''
    digest_dict = {'general': []}
    for report in report_list:
        if ',' in report['project_names']:
            for p in report['project_names'].split(','):
              if not p in digest_dict.keys():
                  digest_dict[p] = []
              digest_dict[p].append({'name':report['user']['full_name'], 'content': report['content']})
        elif report['project_names']:
            if not report['project_names'] in digest_dict.keys():
                digest_dict[report['project_names']] = []
            digest_dict[report['project_names']].append({'name':report['user']['full_name'], 'content': report['content']})
        else:
            digest_dict['general'].append({'name':report['user']['full_name'], 'content': report['content']})

    for k, v in digest_dict.iteritems():
        if k == 'general':
            digest += '<br /><h1>General Reports(No project specified)</h1>'
        else:
            digest += '<br /><h1>Project ' + k + '</h1>'
        for report in v:
            digest += '<h3>' + report['name'] + '</h3>'
            digest += '<h4>Done</h4><p>' + report['content']['done'] + '</p>'
            digest += '<h4>Todo</h4><p>' + report['content']['todo'] + '</p>'
    return digest


def _get_current_user_access_list():
    projects = models.Project.objects.filter(lead=current_user.id).values_list('id')

    if current_user.is_superuser:
        members = models.User.objects.all().values_list('id')
    else:
        members = [current_user.id]

    return (projects, members)


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


@api.route('/api/projects/name/<string:project_name>/users', methods=['GET'])
@login_required
@update_user_token
def list_project_users(project_name):
    project = project_api.get_project_by_name(project_name)
    if not project:
        raise exception_handler.BadRequest(
            "project %s does not exist" % project_name
            )
    if current_user.username == project['lead']['username'] or current_user.is_superuser:
        return utils.make_json_response(
            200,
            project['members']
        )

    return utils.make_json_response(
        200,
        [current_user.to_dict()]
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


@api.route('/api/projects/id/<string:project_id>/delete', methods=['DELETE'])
@login_required
@update_user_token
def delete_project(project_id):
    project = project_api.delete_project(project_id)
    return utils.make_json_response(
        200,
        project
    )

@api.route('/api/reports/<string:filtered_start>/<string:filtered_end>', methods=['GET'])
@login_required
@update_user_token
def list_reports(filtered_start, filtered_end):
    report_owner = request.args.get('user')
    report_project = request.args.get('project')
    digest = False if request.args.get('digest') == 'False' else True
    filtered_start = datetime.datetime.strptime( filtered_start, '%Y-%m-%d')
    filtered_end = datetime.datetime.strptime( filtered_end, '%Y-%m-%d')
    owner = models.User.objects(username=report_owner).first()
    project = models.Project.objects(name=report_project).first()
    lead_project_list, team_member_list = _get_current_user_access_list()

    params = {
        'created__gt': filtered_start,
        'created__lt': filtered_end,
        'is_draft': False
    }
    if owner:
        params['owner'] = owner
    if project:
        params['projects__in'] = [project]

    lead_criteria = Q(projects__in=lead_project_list) | Q(owner__in=team_member_list)
    join_criteria = Q(**params)
    params['is_draft'] = True
    params['owner'] = current_user.id
    draft_criteria = Q(**params)
    report_list = models.Report.objects(
        draft_criteria | (lead_criteria & join_criteria)
    ).order_by('-created')
    return_report_list = [r.to_dict() for r in report_list]
    print "==============report list============== ", return_report_list
    if digest:
        return utils.make_json_response(
           200,
           _digest_reports(return_report_list)
        )
    return utils.make_json_response(
        200,
        return_report_list
    )


@api.route('/api/reports/id/<string:report_id>', methods=['GET'])
@login_required
@update_user_token
def get_report(report_id):
    report = report_api.get_report_by_id(report_id)
    if not report:
        raise exception_handler.BadRequest(
            'report %s does not exist' % report_id
            )
    return utils.make_json_response(
        200,
        report
    )


@api.route('/api/reports', methods=['POST'])
@login_required
@update_user_token
def add_report():
    data = utils.get_request_data()
    is_draft = False
    if data['is_draft']:
        is_draft = True

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
    report.is_draft = data['is_draft']
    report.save()
    return utils.make_json_response(
        200,
        report.to_dict()
    )


@api.route('/api/reports/id/<string:report_id>/comment', methods=['PUT'])
@login_required
@update_user_token
def update_report_comment(report_id):
    data = utils.get_request_data()
    report = models.Report.objects.get(id=ObjectId(report_id))
    comment = models.Comment.objects.get(id=ObjectId(data['comment_id']))
    report.comments.append(comment)
    report.save()
    send_email(
        report.owner.email,
        'New Comments',
        'comment.html',
        {'fullname': current_user.first_name + ' ' + current_user.last_name, 'report_id': report.to_dict()['id']}
    )
    try:
        at_username = re.search('@(.+?):', comment.content).group(1)
    except AttributeError:
        at_username = ''
    try:
        at_user = models.User.objects.get(username=at_username)
    except models.User.DoesNotExist:
        at_user = None

    if at_user and at_username is not report.owner.username:
        send_email(
            at_user.email,
            'Someone mentioned you in their comment',
            'mention.html',
            {'fullname': current_user.first_name + ' ' + current_user.last_name, 'report_id': report.to_dict()['id']}
        )

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
    return utils.make_json_response(
        200,
        {}
    )


@api.route('/api/comments', methods=['POST'])
@login_required
@update_user_token
def create_comment():
    data=utils.get_request_data()
    comment_author = models.User.objects.get(username=data['comment_author'])
    comment = models.Comment()
    comment.author = comment_author
    comment.content = data['comment_content']
    comment.save()
    return utils.make_json_response(
        200,
        comment.to_dict()
    )

@api.route('/api/users', methods=['GET'])
@login_required
@update_user_token
def get_all_viewable_users():
    data = _get_request_args()
    show_all = False if data['show_all'][0] == 'false' else True

    if show_all:
        users = user_api.list_all_users()
    else:
        users = user_api.list_viewable_users(current_user)
    return utils.make_json_response(
        200,
        [user.to_dict() for user in users]
        )


@api.route('/api/users/all', methods=['GET'])
@login_required
@manager_required
@update_user_token
def list_all_users():
    users = user_api.list_all_users()
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
                message = send_email(to_email, 'Welcome to myweeklystatus.com', 'invitation.html', {'email':to_email, 'fullname':data['fullname']} )
                result[to_email] = 'sent'
            else:
                result[to_email] = 'ignore'
    return utils.make_json_response(200, result)


@api.route('/api/meetings')
@login_required
@update_user_token
def list_meeting():
    data = utils.get_request_data()
    user = models.User.objects.get(username=current_user.username)
    meetings = models.Meeting.objects(
        ( Q(attendees__in=[user.id]) | Q(owner = user.id) )
    )
    result = []
    for m in meetings:
        md = m.to_dict()
        print md
        md['title'] = md['topic']
        md['start'] = md['start_time']
        md['end'] = md['end_time']
        result.append(md)
    return utils.make_json_response(200, result)


@api.route('/api/meetings/id/<string:meeting_id>', methods=['POST'])
@login_required
@update_user_token
def update_meeting(meeting_id):
    data = utils.get_request_data()
    current_meeting = meeting_api.get_meeting_by_id(meeting_id)
    author_list = current_meeting.minutes_authors
    author_list = [] if not author_list else author_list
    author_list = set(author_list)
    author_list.add(models.User.objects.get(username=current_user.username))
    author_list = list(author_list)
    data['minutes_authors'] = author_list
    meeting = meeting_api.update_meeting_by_id(meeting_id, **data)
    return utils.make_json_response(
        200,
        meeting
    )


@api.route('/api/meetings', methods=['POST'])
@login_required
@update_user_token
def add_meeting():
    data = utils.get_request_data()
    project = models.Project.objects.get(name=data['project_name'])

    # eliminate owner from attendee names
    if current_user.username in data['attendee_names']:
        data['attendee_names'].remove(current_user.username)
    attendees = [models.User.objects.get(username=u) for u in data['attendee_names']]
    owner = models.User.objects.get(username=current_user.username)

    meeting = models.Meeting()
    meeting.created = datetime.datetime.now()
    meeting.project = project
    meeting.attendees = attendees
    meeting.topic = data['topic']
    meeting.owner = owner
    meeting.start_time = datetime.datetime.strptime(data['start_time'], '%m/%d/%Y %H:%M')
    meeting.end_time = datetime.datetime.strptime(data['end_time'], '%m/%d/%Y %H:%M')

    meeting.save()
    for u in attendees:
        send_email(
            u.email,
            '%s Meeting' % meeting.project,
            'meeting.html',
            {
                'owner_fullname':owner.first_name + ' ' + owner.last_name,
                'first_name':u.first_name,
                'start_time': datetime.datetime.strftime(meeting.start_time, '%m/%d/%Y %H:%M'),
                'topic': meeting.topic
            }
        )
    return utils.make_json_response(
        200,
        meeting.to_dict()
    )

@api.route('/api/meetings/<string:id>')
@login_required
def get_meeting(id):
    meeting = models.Meeting.objects.get(id=ObjectId(id))

    return utils.make_json_response(
        200,
        meeting.to_dict()
    )


@api.route('/api/teams', methods=['POST'])
@login_required
def add_team():
    data = utils.get_request_data()
    data['owner'] = current_user.username
    team = team_api.create_team(**data)
    return utils.make_json_response(200, team)

@api.route('/api/teams/invite', methods=['POST'])
@login_required
def invite_members():
    data = utils.get_request_data()
    team = team_api.invite_members(**data)
    return utils.make_json_response(200, team)

@api.route('/api/teams')
@login_required
def list_team():
    teams = team_api.get_my_teams(current_user.username)
    return utils.make_json_response(200, teams)

@api.route('/api/teams/id/<string:id>')
@login_required
def show_team(id):
    team = team_api.get_team_by_id(id)
    return utils.make_json_response(200, team)

@api.route('/api/teams/leave/<string:id>')
@login_required
def leave_team(id):
    username = current_user.username
    team = team_api.leave_team(id, username)
    return utils.make_json_response(200, team)
