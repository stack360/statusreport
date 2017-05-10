import os, sys, re, traceback
import utils

statusreport_dir = os.path.dirname(os.path.realpath(__file__ + "/../"))
sys.path.append(statusreport_dir)

from statusreport import exception_handler
from statusreport.config import *
from statusreport.models import models

from datetime import datetime
from mongoengine.queryset.visitor import Q

@utils.supported_filters(
    optional_supported_keys=[
        'id', 'members', 'emails'
    ]
)
def invite_members(**kwargs):
  members = []
  team = models.Team.objects.get(id=kwargs['id'])

  # remove owner from member list to prevent infinity loop
  if team.owner.username in kwargs['members']:
    kwargs['members'].remove(team.owner.username)

  for username in kwargs['members']:
    try:
      user = models.User.objects.get(username=username)
      member = models.Member.objects(user=user)
      if member:
        # this user is currently member of another team
        continue
      else:
        member = models.Member(user=user)
        member.invitation_sent_at = datetime.now()
        member.save()
        members.append(member)
    except models.User.DoesNotExist:
      pass
  for email in kwargs['emails']:
    if re.match('[^@]+@[^@]+\.[^@]+', email):
      member = models.Member(email=email, status='pending')
      member.invitation_sent_at = datetime.now()
      member.save()
      members.append(member)

  team.members.extend(members)
  team.save()

  return team.to_dict()

@utils.supported_filters(
    optional_supported_keys=[
        'name', 'owner'
    ],
    ignored_supported_keys=['id']
)
def create_team(**kwargs):
    team = models.Team()

    for k, v in kwargs.iteritems():
        if k == 'owner':
            v = models.User.objects.get(username=v)
        setattr(team, k, v)
    team.created = datetime.now()
    team.save()

    return team.to_dict()

def get_team_by_owner(owner_username):
  owner = models.User.objects.get(username=owner_username)
  try:
    team = models.Team.objects.get(owner=owner)
  except models.Team.DoesNotExist:
    return {}
  return team.to_dict()

def get_my_teams(owner_username):
  try:
    owner = models.User.objects.get(username=owner_username)
    try:
      members = models.Member.objects(user=owner)
    except models.Member.DoesNotExist:
      members = []
      print 'members '
    teams = models.Team.objects( Q(owner=owner) | Q(members__in=members))
  except:
    traceback.print_exc()
    return []

  return [t.to_dict() for t in teams]

def get_team_by_id(id):
  try:
    team = models.Team.objects.get(id=id)
  except models.Team.DoesNotExist:
    return {}
  return team.to_dict()

def leave_team(id, username):
  try:
    team = models.Team.objects.get(id=id)
    user = models.User.objects.get(username=username)
    members = models.Member.objects(user=user)
    team.update(pull_all__members=members)
  except models.Team.DoesNotExist:
    return {}
  return team.to_dict()
