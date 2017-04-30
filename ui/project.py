from flask import Blueprint, redirect, url_for, session, jsonify, current_app, make_response, render_template, request, session
import requests
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

    original_contents = response.json()
    print "====contents are ", original_contents

    data = [{'project_name': c['name'], 'project_lead': c['lead'], 'project_intro': c['intro'], 'logo_file': c['logo_file'] if c['logo_file'] else ''} for c in original_contents]
    return render_template('project/index.jade', data=data)


@project_page.route('/id/<string:project_id>/upload_logo', methods=['POST'])
@ui_login_required
def upload_logo(project_id):
    logo_file = request.files['file']
    response = api_client.upload_project_logo(session['token'], project_id, logo_file)
    original_contents = response.json()

    return redirect(url_for('project.index'))

@project_page.route('/index/<string:project_name>')
@ui_login_required
def project_homepage(project_name):
    response = api_client.project_home(project_name, session['token'])

    original_contents = response.json()
    original_contents['members'] = [m['first_name'] + ' ' + m['last_name'] for m in original_contents['members']]
    return render_template('project/home.jade', data=original_contents)
