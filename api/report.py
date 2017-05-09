import os, sys
import utils

statusreport_dir = os.path.dirname(os.path.realpath(__file__ + "/../"))
sys.path.append(statusreport_dir)

from statusreport.config import *
from statusreport.models import models


def get_report_by_id(report_id):
    return models.Report.objects.get(id=report_id).to_dict()
