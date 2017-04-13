from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

import db_exceptions
import binascii
import os

from bson.json_util import dumps
from flask_mongoengine import MongoEngine


db = MongoEngine()

ROLES = (('admin', 'admin'),
            ('manager', 'manager'),
            ('employee', 'employee'))


class User(UserMixin, db.Document):
    username = db.StringField(max_length=255, required=True)
    email = db.EmailField(max_length=255)
    password_hash = db.StringField(required=True)
    create_time = db.DateTimeField(default=datetime.now, required=True)
    last_login = db.DateTimeField(default=datetime.now, required=True)
    is_superuser = db.BooleanField(default=False)
    role = db.StringField(max_length=32, default='employee', choices=ROLES)
    token = db.ReferenceField('Token')

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        try:
            return self.username
        except AttributeError:
            raise NotImplementedError('No `username` attribute - override `get_id`')

    def update_token(self, token):
        self.token = token

    def to_dict(self):
        user_dict = {}
        user_dict['username'] = self.username
        user_dict['email'] = self.email
        user_dict['create_time'] = self.create_time.isoformat()
        user_dict['last_login'] = self.last_login.isoformat()
        user_dict['is_superuser'] = self.is_superuser
        user_dict['role'] = self.role
        if self.token:
            user_dict['token'] = self.token.token

        return user_dict

    def __unicode__(self):
        return self.username

class Token(db.Document):
    user = db.ReferenceField(User)
    token = db.StringField(max_length=255)
    expire_timestamp = db.DateTimeField(default=datetime.now, required=True)

    def __init__(self, *args, **values):
        super(Token, self).__init__(*args, **values)
        if not self.token:
            self.token = self.generate_token()

    def save(self, *args, **kwargs):
        kwargs['validate'] = False
        return super(Token, self).save(*args, **kwargs)

    def generate_token(self):
        return binascii.hexlify(os.urandom(22)).decode()

    def validate(self):
        columns = self.__mapper__.columns
        for key, column in columns.items():
            value = getattr(self, key)
            if not self.type_compatible(value, column.type):
                raise db_exceptions.InvalidParameter(
                    'user is not set in token: %s' % self.token
                )


STATUS_CHOICES = ('todo', 'ongoing', 'completed', 'overdue')

class Task(db.Document):
    title = db.StringField(max_length=255, required=True)
    abstract = db.StringField()
    pub_time = db.DateTimeField()
    update_time = db.DateTimeField()
    due_time = db.DateTimeField()
    content = db.StringField(required=True)
    manager = db.ReferenceField(User)
    assignee = db.ListField(db.ReferenceField(User))
    status = db.StringField(max_length=64, default='todo', choices=STATUS_CHOICES)
    tags = db.ListField(db.StringField(max_length=30))

    '''
    def save(self, allow_set_time=False, *args, **kwargs):
        if not allow_set_time:
            now = datetime.datetime.now()
            if not self.pub_time:
                self.pub_time = now
            self.update_time = now
        return super(Post, self).save(*args, **kwargs)

    def set_task_date(self, pub_time, update_time):
        self.pub_time = pub_time
        self.update_time = update_time
        return self.save(allow_set_time=True)
    '''

    def to_dict(self):
        task_dict = {}
        task_dict['title'] = self.title
        task_dict['abstract'] = self.abstract
        task_dict['pub_time'] = self.pub_time.isoformat()
        task_dict['update_time'] = self.update_time.isoformat()
        task_dict['due_time'] = self.due_time.isoformat()
        task_dict['content'] = self.content
        task_dict['manager'] = self.manager.username
        task_dict['assignee'] = [assign_user.username for assign_user in self.assignee]
        task_dict['status'] = self.status
        task_dict['tags'] = self.tags

        return task_dict

    def __unicode__(self):
        return self.title

class Report(db.Document):
    owner = db.ReferenceField(User, required=True)
    content = db.DictField()
    created = db.DateTimeField(default=datetime.now, required=True)
    is_draft = db.BooleanField(default=False, required=True)

    def to_dict(self):
        report_dict = {}
        report_dict['user'] = self.owner.username
        report_dict['created'] = self.created.isoformat().split('T')[0]
        report_dict['content'] = self.content
        report_dict['is_draft'] = self.is_draft
        report_dict['id'] = str(self.id)

        return report_dict

class Comment(db.Document):
    author = db.ReferenceField(User, required=True)
    post_title = db.StringField(default='default article')
    content = db.StringField()
    pub_time = db.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.pub_time:
            self.pub_time = datetime.datetime.now()

        return super(Comment, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.content

    meta = {
        'ordering': ['-pub_time']
    }
