from flask import Blueprint, redirect, url_for, session, jsonify, current_app, make_response, render_template, request, session
import requests
from config import *
import models
import utils
import simplejson as json

ui_page = Blueprint('ui', __name__, template_folder='templates')

@ui_page.route('/test')
def show():
  return "test"

@ui_page.route('/login')
def login_page():
    error = request.args.get('error')
    print "error = ",error
    return render_template('login.jade', error=error)

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
    return redirect("/ui/report/index", code=302)

@ui_page.route('/register')
def register_page():
    arg = request.args.get('email')
    data = {}
    data['email'] = arg
    return render_template('register.jade', data=data)

@ui_page.route('/register_action', methods=['POST'])
def register_action():
    username = request.form['username']
    password = request.form['password']
    email = request.form['email']

    data_dict = {'username': username, 'password': password, 'email': email}
    response = requests.post(API_SERVER + '/api/register', data=json.dumps(data_dict))
    data = response.json()
    session['username'] = username
    session['is_superuser'] = data.get('is_superuser')
    session['role'] = data.get('role')
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
    return render_template('report_new.jade', data=data)

@ui_page.route('/report/create', methods=['POST'])
def report_create_action():
    todo  = request.form['todo']
    done  = request.form['done']
    is_draft = request.form['is_draft']
    if is_draft == 'True':
        is_draft = True
    if not session['username']:
        return redirect('/ui/login', 302)
    print 'username = ', session['username']

    data_dict = {'user': session['username'], 'content':{'todo': todo, 'done': done}, 'is_draft': is_draft}

    response = requests.post(API_SERVER + '/api/reports', data=json.dumps(data_dict))
    if is_draft:
        return render_template('report_new.jade', data=data_dict['content'])

    return render_template('report_new.jade', data={})

@ui_page.route('/logout')
def logout_action():
    if not session['username']:
        return redirect('/ui/login', 302)

    response = requests.post(API_SERVER + '/api/logout')
    return redirect('/ui/login', 302)

@ui_page.route('/report/index')
def report_index_page():
    print 'session ', session
    if not session or not session.has_key('username'):
        return redirect('/ui/login', 302)
    print 'username = ', session['username']
    user = request.args.get('user')
    week = request.args.get('week')
    if not week:
        week = BEGINNING_OF_TIME.date().isoformat()
    if not user:
        response = requests.get(API_SERVER + '/api/reports/' + week)
    else:
        response = requests.get(API_SERVER + '/api/reports/' + week + '?user=' + user)

    print "CODE = ",response.status_code, response
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
    print data
    return render_template('report_index.jade', data=data)
