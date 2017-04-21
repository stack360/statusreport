from flask import Blueprint, redirect, url_for, session, jsonify, current_app, make_response, render_template, request, session
import requests
import sys
sys.path.append('..')
from models import models
from config import *
import simplejson as json

from flask_oauth import OAuth
from flask import jsonify


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


ui_page = Blueprint('ui', __name__, template_folder='templates')

@ui_page.route('/login')
def login():
    error = request.args.get('error')
    return render_template('login.jade', error=error)


@ui_page.route('/login_google')
def login_google():
    callback=url_for('ui.google_authorized', _external=True)
    return google.authorize(callback=callback)


@ui_page.route('/google_authorized')
@google.authorized_handler
def google_authorized(resp):
    access_token = resp['access_token']

    # login with google failed
    if access_token is None:
        raise exception_handler.Unauthorized("failed login with google, please retry")
    data_dict = {'access_token':access_token}
    response = requests.post(API_SERVER + '/api/login', data=json.dumps(data_dict))
    data = response.json()
    if response.status_code == 302:
        return redirect(url_for("ui.register", email=data.get('email'), first_name=data.get('first_name'), last_name=data.get('last_name')))
    elif response.status_code != 200:
        return redirect(url_for("ui.login", error=data.get('error')))

    session['username'] = data.get('username')
    session['is_superuser'] = data.get('is_superuser')
    session['role'] = data.get('role')
    session['token'] = data.get('token')
    session['first_name'] = data.get('first_name')
    session['last_name'] = data.get('last_name')
    session['gravatar_url'] = data.get('gravatar_url')
    return redirect(url_for("report.index"), code=302)

@ui_page.route('/login_action', methods=['POST'])
def login_action():
    username  = request.form['username']
    password  = request.form['password']
    data_dict = {'username': username, 'password': password, 'remember_me':'true'}
    response = requests.post(API_SERVER + '/api/login', data=json.dumps(data_dict))
    data = response.json()
    if response.status_code != 200:
        return redirect(url_for("/ui/login", error=data.get('error')))
    session['username'] = username
    session['is_superuser'] = data.get('is_superuser')
    session['role'] = data.get('role')
    session['token'] = data.get('token')
    session['first_name'] = data.get('first_name')
    session['last_name'] = data.get('last_name')
    session['gravatar_url'] = data.get('gravatar_url')
    session['projects'] = data.get('projects')

    return redirect(url_for("report.index"), code=302)

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

    response = requests.post(API_SERVER + '/api/register', data=json.dumps(data_dict))
    data = response.json()
    session['username'] = username
    session['is_superuser'] = data.get('is_superuser')
    session['role'] = data.get('role')
    session['token'] = data.get('token')
    session['first_name'] = data.get('first_name')
    session['last_name'] = data.get('last_name')
    session['gravatar_url'] = data.get('gravatar_url')
    return redirect(url_for("report.index"), code=302)

@ui_page.route('/logout')
def logout():
    if not session['username']:
        return redirect(url_for('ui.login'), 302)

    response = requests.post(API_SERVER + '/api/logout')
    session.pop('username')
    session.pop('is_superuser')
    session.pop('role')
    session.pop('token')
    session.pop('gravatar_url')

    return redirect(url_for('ui.login'), 302)

@ui_page.route('/invite', methods=['POST'])
def invite():
    emails = request.form['emails']
    headers = {'token': session['token']}
    data_dict = {'emails': emails, 'username':session['username']}
    response = requests.post(API_SERVER + '/api/invite', data=json.dumps(data_dict), headers=headers)
    return jsonify(response.json())

@ui_page.route('/')
def home():
  return redirect(url_for("report.index"), code=302)

@ui_page.route('/favicon.ico')
def favicon():
    return redirect("/static/favicon.ico")
