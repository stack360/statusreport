import os, sys
import utils

statusreport_dir = os.path.dirname(os.path.realpath(__file__ + "/../"))
sys.path.append(statusreport_dir)

from statusreport import exception_handler
from statusreport.config import *
from statusreport.models import models


def get_meeting_by_id(meeting_id):
    try:
        meeting = models.Meeting.objects.get(id=meeting_id)
    except IndexError:
        raise exception_handler.ItemNotFound("Meeting not found!")

    return meeting


@utils.supported_filters(
    optional_supported_keys=[
        'minutes','start_time','end_time','topic','minutes_authors'
    ],
    ignored_supported_keys=['id', 'project','owner']
)
def update_meeting_by_id(meeting_id, **kwargs):
    try:
        meeting = models.Meeting.objects.get(id=meeting_id)
    except IndexError:
        raise exception_handler.ItemNotFound("Meeting not found!")

    for k, v in kwargs.iteritems():
        setattr(meeting, k ,v)
    meeting.save()

    return meeting.to_dict()
