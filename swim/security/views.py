try:
    from hashlib import md5 as md5
except ImportError:
    from md5 import new as md5
import shutil
import time
import os.path

from swim import settings
from swim.security.models import File
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.http import (
    HttpResponse,
    HttpResponseRedirect,
)
from django.template import Context
from django.template.loader import get_template

secure_download_script_has_been_copied = False

#-------------------------------------------------------------------------------
@login_required
def secure_file_download(request, file_id):
    secure_file = get_object_or_404(File, pk=file_id)
    raise NotImplementedError("This is the old, busted way of doing it. A new way needs to be implemented")

    return response
