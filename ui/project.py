from flask import Blueprint, redirect, url_for, session, jsonify, current_app, make_response, render_template, request, session
import requests
import sys
sys.path.append('..')
from models import models
from config import *
import simplejson as json

project_page = Blueprint('project', __name__, template_folder='templates')

@project_page.route('/index')
def index():
    if not session or not session.has_key('token'):
        return redirect(url_for('ui.login'), 302)
    headers = {'token': session['token']}
    response = requests.get(API_SERVER + '/api/projects', headers=headers)

    original_contents = response.json()
    data = [{'project_name': c['name'], 'project_lead': c['lead'], 'project_intro': c['intro']} for c in original_contents]
    return render_template('project/index.jade', data=data)
