"""User Model Handler."""
import crypt
import datetime
import os, sys
import utils
import random

statusreport_dir = os.path.dirname(os.path.realpath(__file__ + "/../"))
sys.path.append(statusreport_dir)

from statusreport import exception_handler
from statusreport.config import *
from statusreport.models import models


def _encrypt(value, crypt_method=None):
    """Get encrypted value."""
    if not crypt_method:
        if hasattr(crypt, 'METHOD_MD5'):
            crypt_method = crypt.METHOD_MD5
        else:
            # for python2.7, copy python2.6 METHOD_MD5 logic here.
            from random import choice
            import string

            _saltchars = string.ascii_letters + string.digits + './'

            def _mksalt():
                """generate salt."""
                salt = '$1$'
                salt += ''.join(choice(_saltchars) for _ in range(8))
                return salt

            crypt_method = _mksalt()

    return crypt.crypt(value, crypt_method)


def upsert_token(user, duration):
    expire_timestamp = datetime.datetime.now() + duration
    token_str = _encrypt(user.username)
    if user.token:
        token_object = models.Token.objects.get(token=user.token.token)
    else:
        token_object = models.Token()
    token_object.token = token_str
    token_object.expire_timestamp = expire_timestamp
    token_object.save()

    return token_object

def extend_token(user, duration):
    expire_timestamp = user.token.expire_timestamp + duration
    token_object = models.Token.objects.get(token=user.token.token)
    token_object.expire_timestamp = expire_timestamp
    token_object.save()
    return token_object

def get_auth_token(username):
    return _encrypt(username)

@utils.supported_filters(
    optional_supported_keys=['first_name', 'last_name', 'email', 'role', 'bio'],
    ignored_supported_keys=['gravatar_url']
)
def update_user(username, **kwargs):
    try:
        user = models.User.objects.get(username=username)
    except models.User.DoesNotExist:
        raise exception_handler.BadRequest(
            "user %s does not exist" % username
        )
    for k, v in kwargs.iteritems():
        setattr(user, k, v)
    user.save()

    return user.to_dict()


@utils.supported_filters(
    supported_keys=[
        'username',
        'password',
        'first_name',
        'last_name',
        'email'
    ],
    optional_supported_keys=[
        'role',
        'is_superuser',
        'bio'
    ],
    ignored_supported_keys=[]
)
def create_user(**kwargs):
    user = models.User()
    for k, v in kwargs.iteritems():
        setattr(user, k, v)
    user.token = upsert_token(user, REMEMBER_COOKIE_DURATION)
    user.gravatar_url = utils._get_gravatar_url(kwargs['email'])

    colors = '#2ecc71,#3498db,#f39c12,#e74c3c'.split(',')
    random.seed(datetime.datetime.now())
    index = random.randint(0, len(colors)-1)
    user.avatar_color = colors[index]
    user.save()

    return user


def get_user_by_username(username):
    try:
        user = models.User.objects.get(username=username)
    except models.User.DoesNotExist:
        user = None

    return user

def list_viewable_users(user):
    team_user_set = set()
    teams = models.Team.objects(owner=user.id)
    for team in teams:
        team_user_set |= set([member.user for member in team.members])

    projects = models.Project.objects(lead=user.id)
    project_user_set = set()
    for project in projects:
        project_user_set |= set([member.user for member in project.members])

    self_user = models.User.objects.get(username=user.username)
    user_list = list(team_user_set | project_user_set | set([self_user]))
    return user_list

def list_all_users():
    users = models.User.objects.all()
    return users
