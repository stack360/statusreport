from flask import Blueprint, redirect, url_for, session, jsonify, current_app, make_response, render_template, request, session
import requests
import sys
sys.path.append('..')
from models import models
from config import *
import simplejson as json
import api_client
import utils

from ui import ui_login_required

meeting_page = Blueprint('meeting', __name__, template_folder='templates')

@meeting_page.route('/calendar')
@ui_login_required
def calendar():
  data = {}
  token = session['token']
  projects = api_client.project_index(token).json()
  users = api_client.user_index(token).json()
  return render_template('meeting/calendar.jade', projects=projects, users=users)


@meeting_page.route('/new')
@ui_login_required
def new():
  token = session['token']
  projects = api_client.project_index(token).json()
  users = api_client.user_index(token).json()
  return render_template('meeting/new.jade', projects=projects, users=users)

@meeting_page.route('/create', methods=['POST'])
@ui_login_required
def create():
  data = {}
  return redirect(url_for('meeting.calendar.jade'))

@meeting_page.route('/minutes')
@ui_login_required
def minutes():
  data = {}
  return render_template('meeting/minutes.jade', data=data)

@meeting_page.route('/source')
@ui_login_required
def source():
  data = [
      {
        'title': 'All Day Event',
        'start': '2017-05-01'
      },
      {
        'title': 'Long Event',
        'start': '2017-05-07',
        'end': '2017-05-10'
      },
      {
        'id': 999,
        'title': 'Repeating Event',
        'start': '2017-05-09T16:00:00'
      },
      {
        'id': 999,
        'title': 'Repeating Event',
        'start': '2017-05-16T16:00:00'
      }]
  return utils.make_json_response(200, data)
