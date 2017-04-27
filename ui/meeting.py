from flask import Blueprint, redirect, url_for, session, jsonify, current_app, make_response, render_template, request, session
import requests
import sys
sys.path.append('..')
from models import models
from config import *
import simplejson as json
import api_client

from ui import ui_login_required

meeting_page = Blueprint('meeting', __name__, template_folder='templates')

@meeting_page.route('/calendar')
@ui_login_required
def calendar():
  data = {}
  return render_template('meeting/calendar.jade', data=data)


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
