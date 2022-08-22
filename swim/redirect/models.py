from django.db import models
from django.conf import settings
from django.dispatch import dispatcher

from swim.core import modelfields
from swim.core.models import HasRequestHandler, RequestHandler

################################################################################
REDIRECT_TYPE_CHOICES = (
    (301, '301 - Moved Permanently'),
    (302, '302 - Found'),
    (303, '303 - See Other'),
    (307, '307 - Temporary Redirect'),
)

REDIRECT_HELP_TEXT = """
See http://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html for more information
on the types of redirects available.
"""

DOMAINS_HELP_TEXT = """
Restrict the redirect to occur only on the specified domains. If you select
no domains then the redirect occurs on all domains.
"""

#-------------------------------------------------------------------------------
class PathRedirect(HasRequestHandler):
    path = modelfields.Path('path')

    redirect_type = models.PositiveIntegerField(
            choices=REDIRECT_TYPE_CHOICES,
            default=REDIRECT_TYPE_CHOICES[0][0],
            help_text=REDIRECT_HELP_TEXT,
        )
    redirect_path = modelfields.Path()

    #--------------------------------------------------------------------------
    def url(self):
        return self.path

    #--------------------------------------------------------------------------
    def get_request_handler(self):
        obj, _ = RequestHandler.objects.get_or_create(
                title='Redirect View',
                function = 'swim.redirect.views.RedirectView',
            )
        return obj

    #---------------------------------------------------------------------------
    def get_request_method(self):
        return "GET"

    #---------------------------------------------------------------------------
    def __str__(self) :
        return self.path

    class Meta:
        verbose_name = 'Path Redirect'
        verbose_name_plural = 'Path Redirects'
        ordering = ('path',)


