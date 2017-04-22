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
    data = [{'project_name': c['name'], 'project_lead': c['lead'], 'project_intro': c['intro']} for c in original_contents]
    return render_template('project/index.jade', data=data)
