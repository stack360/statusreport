import os

from flask import Flask
from flask_mongoengine import MongoEngine
from flask_login import LoginManager
from flask_principal import Principal

from config import *

db = MongoEngine()

login_manager = LoginManager()
login_manager.session_protection = 'basic'
login_manager.login_view = 'api.login'

principals = Principal()

def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    config[config_name].init_app(app)

    db.init_app(app)
    login_manager.init_app(app)
    principals.init_app(app)

    return app

app = create_app(os.getenv('config') or 'default')

app.jinja_env.add_extension('pyjade.ext.jinja.PyJadeExtension')


if __name__ == '__main__':
    app.run(threaded=True)
