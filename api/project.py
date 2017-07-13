import os, sys
import utils

statusreport_dir = os.path.dirname(os.path.realpath(__file__ + "/../"))
sys.path.append(statusreport_dir)

from statusreport import exception_handler
from statusreport.config import *
from statusreport.models import models

from mongoengine.queryset.visitor import Q


def get_projects_by_username(user):
    projects = models.Project.objects.all()
    results = []
    for project in projects:
        if user.username == project.team.owner.username or user.username in map(lambda x:x['username'], project.to_dict()['members']):
            results.append(project)
    return [result.to_dict() for result in results]


def get_project_by_name(project_name):
    return models.Project.objects.get(name=project_name).to_dict()


def get_project_by_id(project_id):
    return models.Project.objects.get(id=project_id).to_dict()


@utils.supported_filters(
    optional_supported_keys=[
        'name', 'intro', 'members', 'lead', 'logo_file', 'coordinator'
    ],
    ignored_supported_keys=['id']
)
def update_project(project_id, **kwargs):
    try:
        project = models.Project.objects.get(id=project_id)
    except IndexError:
        raise exception_handler.ItemNotFound("Project not found!")

    for k, v in kwargs.iteritems():
        if k == 'members':
            v = [models.User.objects.get(username=username) for username in v]
        if k == 'lead':
            v = models.User.objects.get(username=v)
        setattr(project, k, v)
    project.save()

    return project.to_dict()


@utils.supported_filters(
    optional_supported_keys=[
        'name', 'intro', 'members', 'lead', 'team', 'coordinator'
    ],
    ignored_supported_keys=['id']
)
def create_project(**kwargs):
    project = models.Project()
    for k, v in kwargs.iteritems():
        if k == 'members':
            v = [models.User.objects.get(username=username) for username in v]
        if k == 'lead' or k == 'coordinator':
            v = models.User.objects.get(username=v)
        setattr(project, k, v)
    project.save()

    return project.to_dict()


def delete_project(project_id):
    try:
        project = models.Project.objects.get(id=project_id)
    except IndexError:
        raise exception_handler.ItemNotFound("Project you are trying to delete is not found.")
    project.delete()

    return project.to_dict()
