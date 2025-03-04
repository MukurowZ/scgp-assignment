from django.http import JsonResponse
from django.utils.dateparse import parse_datetime
from django.db.models import Avg, Min, Max
from django.db.models.functions import Cast
from django.db.models import FloatField
import numpy as np
from .models import Log

def get_log_statistics(request):
    return JsonResponse(stats, safe=False)
