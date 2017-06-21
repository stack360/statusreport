from flask import Blueprint, redirect, url_for, session, jsonify, current_app, make_response, render_template, request, session
import simplejson as json
import api_client

from ui import ui_login_required

project_page = Blueprint('project', __name__, template_folder='templates')


@project_page.route('/index')
@ui_login_required
def index():
    projects = api_client.project_index(session['token'])
    return render_template('project/index.jade', projects=projects)

@project_page.route('/new')
@ui_login_required
def new():
    token = session['token']
    users = api_client.user_index(token)
    return render_template('project/new.jade', users=users, action='new', project={})

@project_page.route('/create', methods=['POST'])
@ui_login_required
def create():
    token = session['token']
    name = request.form['name']
    intro = request.form['intro']
    members = request.form['members'].split(',')
    lead = session['username']
    logo = request.files['logo']
    data = {'lead':lead, 'name':name, 'intro':intro, 'members':members}
    project_id = '' if not request.form.has_key('project_id') else request.form['project_id']

    project = api_client.project_upsert(token, project_id, data)
    if logo:
        api_client.upload_project_logo(token, project['id'], logo)

    return redirect(url_for('project.index'))

@project_page.route('/<string:id>/delete')
@ui_login_required
def delete(id):
    token = session['token']
    api_client.delete_project(token, id)
    return redirect(url_for('project.index'))


@project_page.route('/<string:id>/edit')
@ui_login_required
def edit(id):
    token = session['token']
    users = api_client.user_index(token)
    project = api_client.project_by_id(token, id)
    member_names = [m['username'] for m in project['members']]
    for user in users:
        if user['username'] in member_names:
            user['selected'] = True
    return render_template('project/new.jade', users=users, action='edit', project=project)

@project_page.route('/upload_logo', methods=['POST'])
@ui_login_required
def upload_logo():
    project_id = request.form['project_id']
    logo_file = request.files['logo']
    original_contents = api_client.upload_project_logo(session['token'], project_id, logo_file)

    return redirect(url_for('project.index'))

# deprecated
@project_page.route('/id/<string:name>')
@ui_login_required
def show(name):
    projects = api_client.project_by_name(session['token'], name)
    return render_template('project/home.jade', data=projects)
