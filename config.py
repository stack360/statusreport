#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, sys, datetime

GOOGLE_CLIENT_ID = '988981253248-na81nhb4ui27j6mlij3644bbsfbfps0l.apps.googleusercontent.com'
GOOGLE_CLIENT_SECRET = 'U4UVeiCRZTlI7DIfSnNG1xHK'
REDIRECT_URI = '/ui/google_get_token'
BEGINNING_OF_TIME = datetime.datetime.strptime("2017-3-26", "%Y-%m-%d")
REMEMBER_COOKIE_DURATION = datetime.timedelta(hours=3)
GMAIL_ACCOUNT = 'stack360test@gmail.com'
PROJECT_LOGO_DIR = os.path.dirname(os.path.realpath(__file__)) + '/static/image/project_logos/'
DIGEST_DIR = os.path.dirname(os.path.realpath(__file__)) + '/static/digests/'
ALLOWED_LOGO_EXTENSIONS = set(['png', 'jpg', 'jpeg'])

FACEBOOK_APP_ID='120754155152551'
FACEBOOK_APP_SECRET='1e9424340f2aacfa90893f1627c36357'


class Config(object):
    DEBUG = False
    TESTING = False

    BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

    SECRET_KEY = os.environ.get('SECRET_KEY') or 'fjdljLJDL08_80jflKzcznv*c'
    MONGODB_SETTINGS = {
        'DB': 'statusreport',
        'HOST': '127.0.0.1',
        'PORT': 27017
    }
    API_SERVER = 'http://127.0.0.1:9999'

    @staticmethod
    def init_app(app):
        pass

class DevConfig(Config):
    DEBUG = True
    SEND_FILE_MAX_AGE_DEFAULT = 0

class ProdConfig(Config):
    DEBUG = os.environ.get('DEBUG', 'false').lower() == 'true'
    MONGODB_SETTINGS = {
        'DB': os.environ.get('DB_NAME') or 'statusreport',
        'HOST': os.environ.get('MONGO_HOST') or 'www.myweeklystatus.com',
        'PORT': 27017
    }
    API_SERVER = 'http://127.0.0.1'

class TestConfig(Config):
    TESTING = True
    DEBUG = True
    MONGODB_SETTINGS = {
        'DB': 'statusreport_test',
        'HOST': '127.0.0.1',
        'PORT': 27017
    }
    WTF_CSRF_ENABLED = False

config = {
    'dev': DevConfig,
    'prod': ProdConfig,
    'test': TestConfig,
    'default': DevConfig,
}

current_config = config[os.getenv('STATUSREPORT_MODE') or 'default']
