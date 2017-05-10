from flask import Blueprint, redirect, url_for, session, jsonify, current_app, make_response, render_template, request, session
import sys
sys.path.append('..')
from models import models
from config import *
import simplejson as json
from ui import ui_login_required
import api_client

report_page = Blueprint('report', __name__, template_folder='templates')

@report_page.route('/new')
@ui_login_required
def new():
    data = {}
    data['todo'] = ""
    data['done'] = ""

    projects = api_client.project_index(session['token'])
    return render_template('report/new.jade', data=data, projects=projects)


@report_page.route('/edit')
@ui_login_required
def edit():
    report_id = request.args.get('id')
    token = session['token']

    report = api_client.report_show(token, report_id)

    data = {}
    data['todo'] = report['content']['todo']
    data['done'] = report['content']['done']
    data['report_id'] = report['id']

    projects = api_client.project_index(session['token'])

    return render_template('report/new.jade', data=data, action='edit', projects=projects)


@report_page.route('/<string:id>')
@ui_login_required
def show(id):
    token = session['token']
    report = api_client.report_show(token, id)
    return render_template('report/comment.jade', report=report, report_id=id)

@report_page.route('/comment', methods=['POST'])
@ui_login_required
def comment():
    author = request.form['author']
    comment = request.form['comment']
    report_id = request.args.get('report_id')
    data = {}
    data['comment_author'] = author
    data['comment_content'] = comment
    response = api_client.comment_create(session['token'], data)

    comment_id = response['comment_id']
    report_data = {'comment_id': comment_id}
    response = api_client.report_update_comment(session['token'], report_id, data=report_data)
    return redirect(url_for('report.show', id=report_id))

@report_page.route('/delete')
@ui_login_required
def delete():
    report_id = request.args.get('id')
    response = api_client.report_delete(session['token'], report_id)
    return redirect(url_for('report.index'), 302)


@report_page.route('/create', methods=['POST'])
@ui_login_required
def create():
    report_id = '' if not request.form.has_key('report_id') else request.form['report_id']
    todo  = request.form['todo']
    done  = request.form['done']
    projects = [] if not request.form.has_key('projects') else request.form['projects'].split(',')
    is_draft = request.form['is_draft']
    if is_draft == 'True':
        is_draft = True
    else:
        is_draft = False

    data_dict = {'user': session['username'], 'content':{'todo': todo, 'done': done}, 'projects':projects, 'is_draft': is_draft}
    response = api_client.report_upsert(session['token'], report_id, data_dict)

    return redirect(url_for('report.index'))

@report_page.route('/index')
@ui_login_required
def index():
    user = request.args.get('user')
    start = request.args.get('start')
    end = request.args.get('end')
    if not start:
        start = BEGINNING_OF_TIME.date().isoformat()
    if not end:
        end = datetime.date.today() + datetime.timedelta(days=1)
        end = end.isoformat()
    reports = api_client.report_index(session['token'], start, end, user)
    # filter user
    '''
    user = models.User.objects.get(username=session['username'])
    if user.is_superuser:
        user_objects = models.User.objects.all()
        contents = [content for content in original_contents if content['is_draft'] == False]
    else:
        user_objects = [models.User.objects.get(username=user.username)]
        contents = [content for content in original_contents if content['user'] == user.username]
    '''
    #users = [user_obj.to_dict()['username'] for user_obj in user_objects]
    users = [report['user'] for report in reports]
    full_names = {}
    for report in reports:
        full_names[report['user']] = report['user_fullname']

    # filter week
    today = datetime.date.today()
    date = today
    date_range = []
    i = 0
    while date >= BEGINNING_OF_TIME.date():
        prev_sunday = today - datetime.timedelta(days=date.weekday()+1, weeks=i)
        next_saturday = today - datetime.timedelta(days=date.weekday()-5, weeks=i)
        date_range.append({'start': prev_sunday.strftime('%m/%d/%y %H:%M'), 'end':next_saturday.strftime('%m/%d/%y %H:%M')})
        date -= datetime.timedelta(7)
        i += 1
        if i == 5:
            break

    data = {'users': users, 'contents': reports, 'weeks': date_range, 'full_names': full_names}
    return render_template('report/index.jade', data=data)
