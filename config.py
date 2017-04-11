#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, sys, datetime

GOOGLE_CLIENT_ID = '988981253248-na81nhb4ui27j6mlij3644bbsfbfps0l.apps.googleusercontent.com'
GOOGLE_CLIENT_SECRET = 'U4UVeiCRZTlI7DIfSnNG1xHK'
REDIRECT_URI = '/ui/google_get_token'
API_SERVER = 'http://127.0.0.1:9999'
BEGINNING_OF_TIME = datetime.datetime.strptime("2017-3-26", "%Y-%m-%d")
REMEMBER_COOKIE_DURATION = datetime.timedelta(hours=3)

class Config(object):
    DEBUG = False
    TESTING = False

    BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

    SECRET_KEY = os.environ.get('SECRET_KEY') or 'fjdljLJDL08_80jflKzcznv*c'
    MONGODB_SETTINGS = {'DB': 'statusreport',
                        'HOST': '127.0.0.1',
                        'PORT': 27017
        }

    @staticmethod
    def init_app(app):
        pass

class DevConfig(Config):
    DEBUG = True

class PrdConfig(Config):
    DEBUG = os.environ.get('DEBUG', 'false').lower() == 'true'
    MONGODB_SETTINGS = {
            'DB': os.environ.get('DB_NAME') or 'statusreport',
            'HOST': os.environ.get('MONGO_HOST') or '127.0.0.1',
            'PORT': 27017
        }

class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    MONGODB_SETTINGS = {'DB': 'OctBlogTest'}
    WTF_CSRF_ENABLED = False

config = {
    'dev': DevConfig,
    'prd': PrdConfig,
    'testing': TestingConfig,
    'default': DevConfig,
}
