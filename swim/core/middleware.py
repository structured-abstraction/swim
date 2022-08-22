from itertools import groupby

from django.db.models import Q
from django.db.models.signals import post_init

import swim
from swim.core import content

#-------------------------------------------------------------------------------
class RequestThreadLocal:
    """
    Allows global, thread safe access to the request object via thread locals.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        swim._thread_locals.request = request
        response = self.get_response(request)
        swim._thread_locals.request = None
        return response

