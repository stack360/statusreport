from flask import Blueprint, redirect, url_for, session, jsonify, current_app, make_response, render_template, request, session
import sys
sys.path.append('..')
from config import *
import simplejson as json
from ui import ui_login_required
import api_client

team_page = Blueprint('team', __name__, template_folder='templates')

@team_page.route('/index')
@ui_login_required
def index():
  token = session['token']
  teams = api_client.team_index(token)
  if teams:
    return redirect(url_for('team.show', id=teams[0]['id']))
  else:
    users = api_client.user_index(token)
    users = filter(lambda u: u['username'] != session['username'], users)
    return render_template('team/index.jade', users=users)

@team_page.route('/show/<string:id>')
@ui_login_required
def show(id):
  token = session['token']
  teams = api_client.team_index(token)
  owned_teams = filter(lambda t: t['owner']['username'] == session['username'], teams)
  team = api_client.team_show(token, id)
  users = api_client.user_index(token, show_all='true')
  users = filter(lambda u: u['username'] != session['username'], users)
  members = team.setdefault('members', [])
  member_names = [m['username'] for m in members]
  remain_users = filter(lambda u:u['username'] not in member_names, users)

  return render_template('team/show.jade', own_this_team=(team['owner']['username']==session['username']), has_owned_teams=bool(owned_teams), teams=teams, team=team, users=users, remain_users=remain_users)

@team_page.route('/create', methods=['POST'])
@ui_login_required
def create():
  token = session['token']
  name = request.form['name']
  team = api_client.team_create(token, name)
  data = {
  'id':team['id'],
  'members':request.form['members'].split(','),
  'emails':request.form['emails'].split(',')
  }
  api_client.team_invite(token, data)
  return redirect(url_for('team.show', id=team['id']))

@team_page.route('/invite', methods=['POST'])
@ui_login_required
def invite():
  token = session['token']
  data = {
    'id': request.form['team_id'],
    'members':request.form['members'].split(',')
  }
  api_client.team_invite(token, data)
  return redirect(url_for('team.show', id=request.form['team_id']))

@team_page.route('/leave/<string:id>')
@ui_login_required
def leave(id):
  token = session['token']
  api_client.team_leave(token, id)
  return redirect(url_for('team.index'))
