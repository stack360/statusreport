import os

from flask import Flask, redirect

from flask_login import LoginManager
from flask_principal import Principal

from config import *

from ui.ui import ui_page
from ui.report import report_page
from ui.project import project_page
from api import api
from models.models import db, User, Token


login_manager = LoginManager()
login_manager.session_protection = 'basic'
login_manager.login_view = 'api.login'

principals = Principal()


@login_manager.user_loader
def load_user(username):
    print "USER LOADER"
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        user = None
    print "RETURN : ", user
    return user


@login_manager.request_loader
def load_user_from_request(request):
    print "REQUEST LOADER"
    token = request.headers.get('token')
    print "TOKEN", token
    if token:
        token_object = Token.objects.get(token=token)
        if not token_object or datetime.datetime.now() > token_object.expire_timestamp:
            print "RETURN : NONE"
            return None
        user = User.objects.get(token=token_object)
        print "RETURN : ", user
        return user
    print "RETURN : NONE"
    return None


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

app.register_blueprint(ui_page)
app.register_blueprint(report_page, url_prefix='/report')
app.register_blueprint(project_page, url_prefix='/project')
app.register_blueprint(api)


if __name__ == '__main__':
    app.run(threaded=True)
