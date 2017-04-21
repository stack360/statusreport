from flask import Blueprint, redirect, url_for, session, jsonify, current_app, make_response, render_template, request, session
import requests
import sys
sys.path.append('..')
from models import models
from config import *
import simplejson as json

report_page = Blueprint('report', __name__, template_folder='templates')


@report_page.route('/new')
def new():
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


@report_page.route('/edit')
def edit():
    report_id = request.args.get('id')
    if not session or not session.has_key('token'):
        return redirect(url_for('ui.login'), 302)

    report = models.Report.objects.get(id=report_id)
    data = {}
    data['todo'] = report.content['todo']
    data['done'] = report.content['done']
    data['action'] = 'edit'
    data['report_id'] = report_id

    return render_template('report/new.jade', data=data)


@report_page.route('/delete')
def delete():
    report_id = request.args.get('id')
    if not session or not session.has_key('token'):
        return redirect(url_for('ui.login'), 302)

    headers = {'token': session['token']}
    response = requests.delete(API_SERVER + '/api/reports/id/' + report_id, headers=headers)

    return redirect(url_for('report.index'), 302)



@report_page.route('/create', methods=['POST'])
def create():
    print "CREATE REPORT"
    report_id = '' if not request.form.has_key('report_id') else request.form['report_id']
    todo  = request.form['todo']
    done  = request.form['done']
    projects = [] if not request.form.has_key('projects') else request.form['projects'].split(',')
    is_draft = request.form['is_draft']
    if is_draft == 'True':
        is_draft = True
    if not session['username']:
        return redirect(url_for('ui.login'), 302)

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

@report_page.route('/index')
def index():
    if not session or not session.has_key('token'):
        return redirect(url_for('ui.login'), 302)
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
