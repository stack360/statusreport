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
    return render_template('project/new.jade', users=users, action='new')

@project_page.route('/create', methods=['POST'])
@ui_login_required
def create():
    token = session['token']
    name = request.form['name']
    intro = request.form['intro']
    members = request.form['members'].split(',')
    lead = session['username']
    image = request.files['image']
    data = {'lead':lead, 'name':name, 'intro':intro, 'members':members}

    create_response = api_client.project_create(token, data)
    project = create_response.json()
    upload_response = api_client.upload_project_logo(token, project['id'], image)

    return redirect(url_for('project.index'))

@project_page.route('/edit')
@ui_login_required
def edit():
    token = session['token']
    response = api_client.user_index(token)
    users = response.json()
    print 'USERS', users
    return render_template('project/new.jade', users=users, action='edit')

@project_page.route('/<string:project_id>/upload_logo', methods=['POST'])
@ui_login_required
def upload_logo(project_id):
    logo_file = request.files['file']
    response = api_client.upload_project_logo(session['token'], project_id, logo_file)
    original_contents = response.json()

    return redirect(url_for('project.index'))

# deprecated
@project_page.route('/id/<string:name>')
@ui_login_required
def show(name):
    response = api_client.project_show(session['token'], name)
    projects = response.json()
    print projects
    return render_template('project/home.jade', data=projects)
