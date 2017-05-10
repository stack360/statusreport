from datetime import datetime
import simplejson as json

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


class Token(db.Document):
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


class User(UserMixin, db.Document):
    username = db.StringField(max_length=255, required=True)
    email = db.EmailField(max_length=255)
    first_name = db.StringField(max_length=32, required=True)
    last_name = db.StringField(max_length=32, required=True)
    password_hash = db.StringField(required=True)
    create_time = db.DateTimeField(default=datetime.now, required=True)
    last_login = db.DateTimeField(default=datetime.now, required=True)
    is_superuser = db.BooleanField(default=False)
    role = db.StringField(max_length=32, default='employee', choices=ROLES)
    token = db.ReferenceField(Token)
    gravatar_url = db.URLField(required=True)
    bio = db.StringField(max_length=255)

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
        user_dict['id'] = str(self.id)
        user_dict['username'] = self.username
        user_dict['email'] = self.email
        user_dict['first_name'] = self.first_name
        user_dict['last_name'] = self.last_name
        user_dict['full_name'] = ' '.join(filter(lambda x: x, [self.first_name, self.last_name]))
        user_dict['create_time'] = self.create_time.strftime('%m/%d/%y %H:%M')
        user_dict['last_login'] = self.last_login.strftime('%m/%d/%y %H:%M')
        user_dict['is_superuser'] = self.is_superuser
        user_dict['role'] = self.role
        user_dict['gravatar_url'] = self.gravatar_url
        user_dict['bio'] = self.bio
        if self.token:
            user_dict['token'] = self.token.token

        return user_dict

    def __unicode__(self):
        return self.username


class Member(db.Document):
    user = db.ReferenceField(User)
    joined_at=db.DateTimeField(default=datetime.now, required=False)
    email = db.StringField(max_length=255)
    status = db.StringField(max_length=255) # pending, accepted, rejected
    invitation_sent_at=db.DateTimeField(default=datetime.now, required=False)

    def to_dict(self):
        member_dict = {}
        member_dict['username'] = self.user.username if self.user else ''
        member_dict['gravatar_url'] = self.user.gravatar_url if self.user else ''
        member_dict['email'] = self.user.email if self.user else self.email
        member_dict['fullname'] = self.user.first_name + ' ' + self.user.last_name if self.user else ''
        member_dict['status'] = self.status
        member_dict['joined_at'] = self.joined_at.strftime('%m/%d/%y %H:%M') if self.joined_at else ''
        member_dict['invitation_sent_at'] = self.invitation_sent_at.strftime('%m/%d/%y %H:%M') if self.invitation_sent_at else ''
        return member_dict

class Team(db.Document):
    name = db.StringField(max_length=255)
    owner = db.ReferenceField(User)
    created = db.DateTimeField(default=datetime.now, required=True)
    members = db.ListField(db.ReferenceField(Member))

    def to_dict(self):
        team_dict = {}
        team_dict['id'] = str(self.id)
        team_dict['name'] = self.name
        team_dict['owner'] = self.owner.to_dict()
        team_dict['owner_fullname'] = self.owner.first_name + ' ' + self.owner.last_name
        team_dict['members'] = [ m.to_dict() for m in self.members]
        team_dict['created'] = self.created.strftime('%m/%d/%y %H:%M')
        return team_dict

class Project(db.Document):
    name = db.StringField(default="")
    intro = db.StringField(default="")
    members = db.ListField(db.ReferenceField(User))
    lead = db.ReferenceField(User)
    logo_file = db.StringField(max_length=255)

    def to_dict(self):
        project_dict = {}
        project_dict['id'] = str(self.id)
        project_dict['name'] = self.name
        project_dict['intro'] = self.intro
        project_dict['members'] = [member.to_dict() for member in self.members]
        project_dict['lead'] = self.lead.to_dict()
        project_dict['logo_file'] = self.logo_file

        return project_dict


class Comment(db.Document):
    author = db.ReferenceField(User, required=True)
    content = db.StringField()
    pub_time = db.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.pub_time:
            self.pub_time = datetime.now()

        return super(Comment, self).save(*args, **kwargs)

    def to_dict(self):
        comment_dict = {}
        comment_dict['comment_id'] = str(self.id)
        comment_dict['author'] = self.author.username
        comment_dict['author_gravatar'] = self.author.gravatar_url
        comment_dict['author_fullname'] = self.author.first_name + ' ' + self.author.last_name
        comment_dict['content'] = self.content
        comment_dict['pub_time'] = self.pub_time.strftime('%m/%d/%y %H:%M')

        return comment_dict

    meta = {
        'ordering': ['-pub_time']
    }


class Report(db.Document):
    owner = db.ReferenceField(User, required=True)
    content = db.DictField()
    created = db.DateTimeField(default=datetime.now, required=True)
    is_draft = db.BooleanField(default=False, required=True)
    projects = db.ListField(db.ReferenceField(Project))
    comments = db.ListField(db.ReferenceField(Comment))

    def to_dict(self):
        report_dict = {}
        report_dict['user'] = self.owner.username
        report_dict['user_fullname'] = self.owner.first_name + ' ' + self.owner.last_name
        report_dict['gravatar_url'] = self.owner.gravatar_url
        report_dict['created'] = self.created.strftime('%m/%d/%y %H:%M')
        report_dict['content'] = self.content
        report_dict['is_draft'] = self.is_draft
        report_dict['id'] = str(self.id)
        report_dict['comments'] = [c.to_dict() for c in self.comments]
        if self.projects:
            report_dict['projects'] = [p.to_dict() for p in self.projects]
        else:
            report_dict['projects'] = []
        report_dict['project_names'] = ', '.join(map(lambda x: x['name'], report_dict['projects']))
        return report_dict

class Meeting(db.Document):
    owner = db.ReferenceField(User, required=True)
    topic = db.StringField()
    created = db.DateTimeField(default=datetime.now, required=True)
    project = db.ReferenceField(Project)
    attendees = db.ListField(db.ReferenceField(User))
    start_time = db.DateTimeField()
    end_time = db.DateTimeField()

    def to_dict(self):
        meeting_dict = {}
        meeting_dict['id'] = str(self.id)
        meeting_dict['owner'] = self.owner.username
        meeting_dict['topic'] = self.topic
        meeting_dict['project'] = self.project.name
        meeting_dict['attendees'] = [u.username for u in self.attendees]
        meeting_dict['start_time'] = datetime.strftime(self.start_time, '%Y-%m-%dT%H:%M')
        meeting_dict['end_time'] = datetime.strftime(self.end_time, '%Y-%m-%dT%H:%M')
        return meeting_dict
