import os

from flask import Flask, redirect, request, url_for, render_template

from flask_login import LoginManager
from flask_principal import Principal

from config import *

from api.api import api
from ui.ui import ui_page
from ui.report import report_page
from ui.project import project_page
from ui.meeting import meeting_page
from ui.team import team_page
from models.models import db, User, Token
import traceback
import utils
from api import exception_handler
from ui import ui_exceptions


login_manager = LoginManager()
login_manager.session_protection = 'basic'
login_manager.login_view = 'api.login'

principals = Principal()


@login_manager.user_loader
def load_user(username):
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        user = None
        raise exception_handler.Unauthorized("Please login to continue")
    return user


@login_manager.request_loader
def load_user_from_request(request):
    token = request.headers.get('token')
    if token:
        token_object = None
        try:
            token_object = Token.objects.get(token=token)
        except:
            pass
        if not token_object or datetime.datetime.now() > token_object.expire_timestamp:
            # if token is found but expired
            # raise exception for unauthorized access for API ONLY
            if request.path.startswith('/api'):
                raise exception_handler.TokenExpire("Please provide valid token for API usage")
            else:
                raise ui_exceptions.UITokenExpire("Please login again to refresh token")


        user = User.objects.get(token=token_object)
        return user

    # if token or user is not found in db
    # raise exception for unauthorized access for API ONLY
    if request.path.startswith('/api'):
        raise exception_handler.TokenExpire("Please provide valid token for API usage")
    else:
        return None


def create_app():
    app = Flask(__name__)
    app.config.from_object(current_config)

    current_config.init_app(app)
    print current_config

    db.init_app(app)
    login_manager.init_app(app)
    principals.init_app(app)

    return app

app = create_app()

app.jinja_env.add_extension('pyjade.ext.jinja.PyJadeExtension')

app.register_blueprint(ui_page)
app.register_blueprint(report_page, url_prefix='/report')
app.register_blueprint(project_page, url_prefix='/project')
app.register_blueprint(meeting_page, url_prefix='/meeting')
app.register_blueprint(team_page, url_prefix='/team')
app.register_blueprint(api)

@app.context_processor
def inject_dict_for_all_templates():
    active_module = request.path.split('/')[1] if '/' in request.path else ''
    return {'_active_module':active_module}

@app.errorhandler(Exception)
def handle_exception(error):
    traceback.print_exc()
    error_type = type(error).__name__
    if error_type == 'UITokenExpire':
        return redirect(url_for('ui.login'))
    elif error_type == 'GeneralError':
        return render_template('error.jade', error=error.message)
    else:
        # adding message
        if hasattr(error, 'to_dict'):
            response = error.to_dict()
        else:
            response = {'message': str(error)}
        # adding traceback
        if app.debug and hasattr(error, 'traceback'):
            response['traceback'] = error.traceback

        # adding status code
        status_code = 400
        if hasattr(error, 'status_code'):
            status_code = error.status_code

        return utils.make_json_response(status_code, response)

if __name__ == '__main__':
    app.run(threaded=True)
