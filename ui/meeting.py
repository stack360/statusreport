from flask import Blueprint, redirect, url_for, session, jsonify, current_app, make_response, render_template, request, session, jsonify
import requests
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
    projects = api_client.project_index(token)
    users = api_client.user_index(token)
    return render_template('meeting/calendar.jade', projects=projects, users=users)


@meeting_page.route('/new')
@ui_login_required
def new():
    token = session['token']
    projects = api_client.project_index(token)
    users = api_client.user_index(token)
    return render_template('meeting/new.jade', projects=projects, users=users)

@meeting_page.route('/<string:id>')
def show(id):
    token = session['token']
    meeting = api_client.meeting_show(token, id)
    return jsonify(meeting)

@meeting_page.route('/create', methods=['POST'])
@ui_login_required
def create():
    data = request.form.to_dict()
    data['attendee_names'] = data['attendee_names'].split(',') if data['attendee_names'] and ',' in data['attendee_names'] else []
    data['start_time'] = '%s %s' % (data['date'], data['start_time'])
    data['end_time'] = '%s %s' % (data['date'], data['end_time'])
    token = session['token']
    response = api_client.meeting_create(token, data)
    return redirect(url_for('meeting.calendar'))


@meeting_page.route('/<string:id>/minutes')
@ui_login_required
def minutes(id):
    token = session['token']
    meeting = api_client.meeting_show(token, id)
    data = {}
    data['minutes'] = meeting['minutes']
    data['meeting_id'] = meeting['id']
    data['meeting_topic'] = meeting['topic']
    data['authors'] = [api_client.user_by_username(token, user) for user in meeting['minutes_authors']]
    return render_template('meeting/minutes.jade', data=data)

@meeting_page.route('/<string:id>/update_minutes')
@ui_login_required
def update_minutes(id):
    token = session['token']
    meeting = api_client.meeting_show(token, id)
    data = {}
    data['minutes'] = meeting['minutes']
    data['id'] = id
    return render_template('meeting/new_minutes.jade', data=data)

@meeting_page.route('/<string:id>/submit_minutes', methods=['POST'])
@ui_login_required
def submit_minutes(id):
    token = session['token']
    minutes = request.form['minutes']
    meeting = api_client.meeting_update(token, id, {'minutes': minutes})
    return redirect(url_for('meeting.minutes', id=id))

@meeting_page.route('/source')
@ui_login_required
def source():
    token = session['token']
    data = api_client.meeting_index(token)
    return utils.make_json_response(200, data)
