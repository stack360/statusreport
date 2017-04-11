import os

from flask import Flask

from flask_login import LoginManager
from flask_principal import Principal

from config import *

from ui import ui_page
from api import api
from models.models import db, User, Token


login_manager = LoginManager()
login_manager.session_protection = 'basic'
login_manager.login_view = 'api.login'

principals = Principal()

'''
@login_manager.user_loader
def load_user(session_token):
    try:
        user = User.objects.get(token=session_token)
    except User.DoesNotExist:
        user = None
    return user
'''

@login_manager.request_loader
def load_user_from_request(request):

    token = request.headers.get('token')
    if token:
        token_object = Token.objects.get(token=token)
        if not token_object or datetime.datetime.now() > token_object.expire_timestamp:
            return None
        user = User.objects.get(token=token_object)
        return user
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

app.register_blueprint(ui_page, url_prefix='/ui')
app.register_blueprint(api)

if __name__ == '__main__':
    app.run(threaded=True)
