import os, sys, re
import utils

statusreport_dir = os.path.dirname(os.path.realpath(__file__ + "/../"))
sys.path.append(statusreport_dir)

from statusreport import exception_handler
from statusreport.config import *
from statusreport.models import models

from datetime import datetime

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
      member = models.Member(user=user, status='pending')
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
