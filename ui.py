from flask import Blueprint, redirect, url_for, session, jsonify, current_app, make_response, render_template, request, session
import requests
from config import *
from models import models
import utils
import simplejson as json

from flask_oauth import OAuth
from flask import jsonify

oauth = OAuth()
google = oauth.remote_app('google',
                          base_url='https://www.google.com/accounts/',
                          authorize_url='https://accounts.google.com/o/oauth2/auth',
                          request_token_url=None,
                          request_token_params={'scope': 'https://www.googleapis.com/auth/userinfo.email',
                                                'response_type': 'code'},
                          access_token_url='https://accounts.google.com/o/oauth2/token',
                          access_token_method='POST',
                          access_token_params={'grant_type': 'authorization_code'},
                          consumer_key=GOOGLE_CLIENT_ID,
                          consumer_secret=GOOGLE_CLIENT_SECRET)


ui_page = Blueprint('ui', __name__, template_folder='templates')

@ui_page.route('/test')
def show():
  return "test"

@ui_page.route('/login')
def login_page():
    error = request.args.get('error')
    return render_template('login.jade', error=error)


@ui_page.route('/google_get_token')
def login_google():
    callback=url_for('ui.google_authorized', _external=True)
    return google.authorize(callback=callback)


@ui_page.route('/google_authorized')
@google.authorized_handler
def google_authorized(resp):
    access_token = resp['access_token']

    # login with google failed
    if access_token is None:
        raise exception_handler.Unauthorized("failed login with google, please retry")
    data_dict = {'access_token':access_token}
    response = requests.post(API_SERVER + '/api/login', data=json.dumps(data_dict))
    data = response.json()
    if response.status_code == 302:
        return redirect("/ui/register?email=%s&first_name=%s&last_name=%s" % (data.get('email'), data.get('first_name'), data.get('last_name')))
    elif response.status_code != 200:
        return redirect("/ui/login?error=%s" % data.get('error'))

    session['username'] = data.get('username')
    session['is_superuser'] = data.get('is_superuser')
    session['role'] = data.get('role')
    session['token'] = data.get('token')
    session['first_name'] = data.get('first_name')
    session['last_name'] = data.get('last_name')
    session['gravatar_url'] = data.get('gravatar_url')
    return redirect("/ui/report/index", code=302)

@ui_page.route('/login_action', methods=['POST'])
def login_action():
    username  = request.form['username']
    password  = request.form['password']
    data_dict = {'username': username, 'password': password, 'remember_me':'true'}
    response = requests.post(API_SERVER + '/api/login', data=json.dumps(data_dict))
    data = response.json()
    if response.status_code != 200:
        return redirect("/ui/login?error=%s" % data.get('error'))
    session['username'] = username
    session['is_superuser'] = data.get('is_superuser')
    session['role'] = data.get('role')
    session['token'] = data.get('token')
    session['first_name'] = data.get('first_name')
    session['last_name'] = data.get('last_name')
    session['gravatar_url'] = data.get('gravatar_url')
    session['projects'] = data.get('projects')

    return redirect("/ui/report/index", code=302)

@ui_page.route('/register')
def register_page():
    data = {}
    data['email'] = request.args.get('email')
    data['first_name'] = request.args.get('first_name')
    data['last_name'] = request.args.get('last_name')
    return render_template('register.jade', data=data)

@ui_page.route('/register_action', methods=['POST'])
def register_action():
    username = request.form['username']
    password = request.form['password']
    email = request.form['email']
    first_name = request.form['first_name']
    last_name = request.form['last_name']

    data_dict = {
        'username': username,
        'password': password,
        'email': email,
        'first_name': first_name,
        'last_name': last_name
    }

    response = requests.post(API_SERVER + '/api/register', data=json.dumps(data_dict))
    data = response.json()
    session['username'] = username
    session['is_superuser'] = data.get('is_superuser')
    session['role'] = data.get('role')
    session['token'] = data.get('token')
    session['first_name'] = data.get('first_name')
    session['last_name'] = data.get('last_name')
    session['gravatar_url'] = data.get('gravatar_url')
    return redirect("/ui/report/index", code=302)


@ui_page.route('/report/new')
def report_new_page():
    owner = models.User.objects(username=session['username']).first()
    draft = models.Report.objects(
        owner = owner.id,
        is_draft = True
    )
    if draft:
        draft_todo = draft[0].content['todo']
        draft_done = draft[0].content['done']
    else:
        draft_todo = ""
        draft_done = ""

    data = {}
    data['todo'] = draft_todo
    data['done'] = draft_done
    return render_template('report/new.jade', data=data, projects=session['projects'])


@ui_page.route('/report/edit')
def report_edit_page():
    report_id = request.args.get('id')
    if not session or not session.has_key('token'):
        return redirect('/ui/login', 302)

    report = models.Report.objects.get(id=report_id)
    data = {}
    data['todo'] = report.content['todo']
    data['done'] = report.content['done']
    data['action'] = 'edit'
    data['report_id'] = report_id

    return render_template('report/new.jade', data=data)


@ui_page.route('/report/delete')
def report_delete():
    report_id = request.args.get('id')
    if not session or not session.has_key('token'):
        return redirect('/ui/login', 302)

    headers = {'token': session['token']}
    response = requests.delete(API_SERVER + '/api/reports/id/' + report_id, headers=headers)

    return redirect('/ui/report/index', 302)



@ui_page.route('/report/create', methods=['POST'])
def report_create_action():
    print "CREATE REPORT"
    report_id = '' if not request.form.has_key('report_id') else request.form['report_id']
    todo  = request.form['todo']
    done  = request.form['done']
    projects = [] if not request.form.has_key('projects') else request.form['projects'].split(',')
    is_draft = request.form['is_draft']
    if is_draft == 'True':
        is_draft = True
    if not session['username']:
        return redirect('/ui/login', 302)

    print "token = ", session['token']
    headers = {'token': session['token']}
    data_dict = {'user': session['username'], 'content':{'todo': todo, 'done': done}, 'projects':projects, 'is_draft': is_draft}
    if report_id:
        data_dict['report_id'] = report_id
        response = requests.put(API_SERVER + '/api/reports/id/' + report_id, data=json.dumps(data_dict), headers=headers)
    else:
        response = requests.post(API_SERVER + '/api/reports', data=json.dumps(data_dict), headers=headers)
    print response
    if is_draft:
        return render_template('report/new.jade', data=data_dict['content'])

    return render_template('report/new.jade', data={})

@ui_page.route('/logout')
def logout_action():
    if not session['username']:
        return redirect('/ui/login', 302)

    response = requests.post(API_SERVER + '/api/logout')
    session.pop('username')
    session.pop('is_superuser')
    session.pop('role')
    session.pop('token')
    session.pop('gravatar_url')

    return redirect('/ui/login', 302)


@ui_page.route('/project/index')
def project_index_page():
    if not session or not session.has_key('token'):
        return redirect('/ui/login', 302)
    headers = {'token': session['token']}
    response = requests.get(API_SERVER + '/api/projects', headers=headers)

    original_contents = response.json()
    data = [{'project_name': c['name'], 'project_lead': c['lead'], 'project_intro': c['intro']} for c in original_contents]
    return render_template('project/index.jade', data=data)

@ui_page.route('/report/index')
def report_index_page():
    if not session or not session.has_key('token'):
        return redirect('/ui/login', 302)
    user = request.args.get('user')
    week = request.args.get('week')
    headers = {'token': session['token']}
    if not week:
        week = BEGINNING_OF_TIME.date().isoformat()
    if not user:
        response = requests.get(API_SERVER + '/api/reports/' + week, headers=headers)
    else:
        response = requests.get(API_SERVER + '/api/reports/' + week + '?user=' + user, headers=headers)

    original_contents = response.json()
    # filter user
    user = models.User.objects.get(username=session['username'])
    if user.is_superuser:
        user_objects = models.User.objects.all()
        contents = original_contents
    else:
        user_objects = [models.User.objects.get(username=user.username)]
        contents = [content for content in original_contents if content['user'] == user.username]
    users = [user_obj.to_dict()['username'] for user_obj in user_objects]
    # filter week
    today = datetime.date.today()
    date = today
    mondays = []
    i = 0
    while date >= BEGINNING_OF_TIME.date():
        monday = today - datetime.timedelta(days=date.weekday(), weeks=i)
        mondays.append(monday.isoformat())
        date -= datetime.timedelta(7)
        i += 1

    data = {'users': users, 'contents': contents, 'weeks': mondays}
    return render_template('report/index.jade', data=data)

@ui_page.route('/invite', methods=['POST'])
def invite_action():
    emails = request.form['emails']
    headers = {'token': session['token']}
    data_dict = {'emails': emails, 'username':session['username']}
    response = requests.post(API_SERVER + '/api/invite', data=json.dumps(data_dict), headers=headers)
    return jsonify(response.json())

@ui_page.route('/users')
def user_index_page():
    headers = {'token': session['token']}
    response = requests.get(API_SERVER + '/api/users', headers=headers)
    return render_template('user_index.jade', data=response.json())
