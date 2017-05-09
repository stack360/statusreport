from flask import Blueprint, redirect, url_for, session, jsonify, current_app, make_response, render_template, request, session
import requests

import sys
sys.path.append('..')
from config import *

import simplejson as json

from flask_oauth import OAuth
from flask import jsonify
from functools import wraps
import api_client

oauth = OAuth()
google = oauth.remote_app('google',
    base_url='https://www.google.com/accounts/',
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    request_token_url=None,
    request_token_params={'scope': 'https://www.googleapis.com/auth/userinfo.email',
                          'response_type': 'code'},
    access_token_url='https://accounts.google.com/o/oauth2/token',
    access_token_method='POST',
    access_token_params={'grant_type': 'authorization_code'},
    consumer_key=GOOGLE_CLIENT_ID,
    consumer_secret=GOOGLE_CLIENT_SECRET)

facebook = oauth.remote_app('facebook',
    base_url='https://graph.facebook.com/',
    request_token_url=None,
    access_token_url='/oauth/access_token',
    authorize_url='https://www.facebook.com/dialog/oauth',
    consumer_key=FACEBOOK_APP_ID,
    consumer_secret=FACEBOOK_APP_SECRET,
    request_token_params={'scope': 'email'}
)

def ui_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session or not session.has_key('token') or session['token'] is None or session['token'] == '':
            return redirect(url_for('ui.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

ui_page = Blueprint('ui', __name__, template_folder='templates')

@ui_page.route('/login')
def login():
    error = request.args.get('error')
    return render_template('login.jade', error=error)

# Google OAuth
@ui_page.route('/ui/google_get_token')
def google_oauth():
    callback=url_for('ui.google_authorized', _external=True)
    return google.authorize(callback=callback)

@ui_page.route('/ui/google_authorized')
@google.authorized_handler
def google_authorized(resp):
    access_token = resp['access_token']

    if access_token is None:
        raise exception_handler.Unauthorized("failed login with google, please retry")
    credential_dict = {'access_token':access_token, 'channel':'google'}
    return _login(credential_dict)

# Facebook OAuth
@ui_page.route('/facebook_get_token')
def facebook_oauth():
    callback=url_for('ui.facebook_authorized', _external=True)
    return facebook.authorize(callback=callback)

@ui_page.route('/facebook_authorized')
@facebook.authorized_handler
def facebook_authorized(res):
    access_token = res['access_token']

    if not access_token:
        raise exception_handler.Unauthorized("failed login with google, please retry")

    credential_dict = {'access_token':access_token, 'channel':'facebook'}
    return _login(credential_dict)

def _login(credential_dict):
    response = api_client.login(credential_dict)
    if response.status_code != 200:
        if response.status_code == 307 and response.get('message') == 'new oauth user':
            return redirect(url_for('ui.register', email=data.get('email')))
        else:
            return redirect(url_for("ui.login", error=data.get('message')))
    user = response
    session['username'] = user.get('username')
    session['is_superuser'] = user.get('is_superuser')
    session['role'] = user.get('role')
    session['token'] = user.get('token')
    session['first_name'] = user.get('first_name')
    session['last_name'] = user.get('last_name')
    session['gravatar_url'] = user.get('gravatar_url')

    return redirect(url_for("project.index"))

@ui_page.route('/login_action', methods=['POST'])
def login_action():
    credential_dict = {
        'username': request.form['username'],
        'password': request.form['password'],
        'remember_me':'true'
    }
    return _login(credential_dict)

@ui_page.route('/register')
def register():
    data = {}
    data['email'] = request.args.get('email')
    data['first_name'] = request.args.get('first_name')
    data['last_name'] = request.args.get('last_name')
    return render_template('register.jade', data=data)

@ui_page.route('/register_action', methods=['POST'])
def register_action():
    username = request.form['username']
    password = request.form['password']
    email = request.form['email']
    first_name = request.form['first_name']
    last_name = request.form['last_name']

    data_dict = {
        'username': username,
        'password': password,
        'email': email,
        'first_name': first_name,
        'last_name': last_name
    }

    data = requests.post(API_SERVER + '/api/register', data=json.dumps(data_dict))
    session['username'] = username
    session['is_superuser'] = data.get('is_superuser')
    session['role'] = data.get('role')
    session['token'] = data.get('token')
    session['first_name'] = data.get('first_name')
    session['last_name'] = data.get('last_name')
    session['gravatar_url'] = data.get('gravatar_url')
    return redirect(url_for("report.index"))

@ui_page.route('/logout')
def logout():
    if not session['username']:
        return redirect(url_for('ui.login'))

    response = requests.post(API_SERVER + '/api/logout')
    session.pop('username')
    session.pop('is_superuser')
    session.pop('role')
    session.pop('token')
    session.pop('gravatar_url')
    session.pop('first_name')
    session.pop('last_name')

    return redirect(url_for('ui.login'))

@ui_page.route('/invite', methods=['POST'])
def invite():
    emails = request.form['emails']
    headers = {'token': session['token']}
    data_dict = {'emails': emails, 'username':session['username'], 'fullname':session['first_name']+' '+session['last_name']}
    response = requests.post(API_SERVER + '/api/invite', data=json.dumps(data_dict), headers=headers)
    return jsonify(response)

@ui_page.route('/')
def home():
  return redirect(url_for("report.index"))

@ui_page.route('/favicon.ico')
def favicon():
    return redirect("/static/favicon.ico")
