from flask import Blueprint, redirect, url_for, session, jsonify, current_app, make_response, render_template, request, session
import sys
sys.path.append('..')
from models import models
from config import *
import simplejson as json
import api_client

from ui import ui_login_required

project_page = Blueprint('project', __name__, template_folder='templates')


@project_page.route('/index')
@ui_login_required
def index():
    response = api_client.project_index(session['token'])

    projects = response.json()
    return render_template('project/index.jade', projects=projects)

@project_page.route('/new')
@ui_login_required
def new():
    token = session['token']
    response = api_client.user_index(token)
    users = response.json()
    print users
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
    project_id = request.form['project_id']

    create_response = api_client.project_upsert(token, project_id, data)
    project = create_response.json()
    upload_response = api_client.upload_project_logo(token, project['id'], logo)

    return redirect(url_for('project.index'))

@project_page.route('/<string:id>/edit')
@ui_login_required
def edit(id):
    token = session['token']
    response = api_client.user_index(token)
    users = response.json()
    response = api_client.project_by_id(token, id)
    project = response.json()
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
    response = api_client.upload_project_logo(session['token'], project_id, logo_file)
    original_contents = response.json()

    return redirect(url_for('project.index'))

# deprecated
@project_page.route('/id/<string:name>')
@ui_login_required
def show(name):
    response = api_client.project_by_name(session['token'], name)
    projects = response.json()
    print projects
    return render_template('project/home.jade', data=projects)
