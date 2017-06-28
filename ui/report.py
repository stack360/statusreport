from flask import Blueprint, redirect, url_for, session, jsonify, current_app, make_response, render_template, request, session, send_from_directory
import sys
sys.path.append('..')
from models import models
from config import *
import simplejson as json
from ui import ui_login_required
import api_client
import pdfkit

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


@report_page.route('/weeklydigest/<string:time_filter>')
@ui_login_required
def digest(time_filter):
    start_time, end_time = time_filter.split('--')
    digest = api_client.report_index(session['token'], start_time, end_time, None, None, digest='True')
    data = {}
    data['week'] = time_filter
    data['digest'] = digest
    return render_template('report/digest.jade', data=data)

@report_page.route('/weeklydigest/download', methods=['POST'])
@ui_login_required
def download_digest():
    digest = request.form['digest']
    week = request.form['week']
    filename = week + '.pdf'
    output_file = DIGEST_DIR + filename
    options = {
        'dpi': 300
    }
    pdfkit.from_string(digest, output_file, options=options)
    return send_from_directory(DIGEST_DIR, filename)

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
    user = request.args.get('user', '')
    time_range = request.args.get('time', '')
    (start, end) = time_range.split('--') if time_range else ("", "")
    project = request.args.get('project', '')
    if not start:
        start = BEGINNING_OF_TIME.date().strftime('%Y-%m-%d')
    if not end:
        end = datetime.date.today() + datetime.timedelta(days=1)
        end = end.strftime('%Y-%m-%d')

    reports = api_client.report_index(session['token'], start, end, user, project)
    current_user = api_client.user_by_username(session['token'], session['username'])
    user_list = api_client.get_user_view_list(session['token'], project)
    # filter user
    """
    if project and project != '':
        project = api_client.project_by_name(session['token'], project)
        users = [u for u in project['members'] if u['role'] == 'employee'] if session['is_superuser'] or session['username'] == project['lead']['username'] else []
    else:
        users = api_client.user_index(session['token'])
        users = [u for u in users if u['role'] == 'employee'] if session['su']
    """
    projects = api_client.project_index(session['token'])
    full_names = {}
    for u in user_list:
        full_names[u['username']] = u['full_name']

    # filter week
    today = datetime.date.today()
    date = today
    date_range = []
    i = 0
    while date >= BEGINNING_OF_TIME.date():
        prev_sunday = today - datetime.timedelta(days=date.weekday()+1, weeks=i)
        next_saturday = today - datetime.timedelta(days=date.weekday()-5, weeks=i)
        date_range.append({'start': prev_sunday, 'end':next_saturday})
        date -= datetime.timedelta(7)
        i += 1
        if i == 5:
            break

    data = {'contents': reports, 'weeks': date_range, 'full_names': full_names}
    return render_template('report/index.jade', data=data, users=user_list, projects=projects, user_filter=user, project_filter=project, time_filter=time_range)
