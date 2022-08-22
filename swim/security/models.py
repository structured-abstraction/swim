from datetime import datetime

from django.db import models
from django.contrib.auth.models import Group, User
from django.urls import reverse

from swim.core import modelfields, WithRelated
from swim.core.models import (
    ModelIsContentType,
    ContentSlot,
    KeyedType,
)

from swim.core.content import (
        register_atom_type,
        ReferencedAtomType,
    )

from swim.media.fields import FileField


#-------------------------------------------------------------------------------
ONLY_ALLOW_CHOICES = (
    ('all_superusers', 'Only Allow Supers Users',),
    ('all_staff', 'Only Allow Staff Users',),
    ('all_users', 'Only Allow Logged in Users',),
    ('specific_groups', 'Only Allow Groups specified below.',),
    ('everyone', 'Allow everyone.',),
)
ONLY_ALLOW_CHOICES_DICT = dict(ONLY_ALLOW_CHOICES)

#-------------------------------------------------------------------------------
class SslEncryption(models.Model):
    path = modelfields.Path('path', unique=True)

    force_ssl_connection = models.BooleanField(
        help_text='Forces the server to use an SSL encrypted connection when serving this path.',
        default=False,
    )


#-------------------------------------------------------------------------------
class AccessRestriction(models.Model):
    path = modelfields.Path('path', unique=True)

    redirect_path = models.CharField(
        max_length=255,
        unique=False,
        help_text="If the user doesn't meet this requirement, they will be "\
                   " redirected to this url.",
        default="/login/",
    )

    only_allow = models.CharField(
        max_length=255,
        choices=ONLY_ALLOW_CHOICES,
        default=ONLY_ALLOW_CHOICES_DICT['everyone'],
    )

    allow_groups = models.ManyToManyField(
        Group,
        related_name='access_restriction',
        help_text='Select the groups who should have access to this path. '
                  ' This option only applies if you select '
                  ' "%(specific_groups)s" above.' % ONLY_ALLOW_CHOICES_DICT,
    )

    def __str__(self):
        return "</%s/ %s>" % (
            self.path,
            self.only_allow,
        )

#-------------------------------------------------------------------------------
# This is here because django and apache have no way to communicate regarding
# a user's access level for files, if apache is serving up.
class File(ModelIsContentType):
    """
    """
    title = models.CharField(max_length=200)

    folder = 'content/secure/files'
    file = FileField(upload_to=folder,)

    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.title

    def url(self):
        return self.get_absolute_url()

    def ext(self):
        return self.filename().split('.')[-1]

    def filename(self):
        return self.file.name[len(self.folder)+1:]

    def get_absolute_url(self):
        return reverse('swim.security.views.secure_file_download', [self.id])

    class Meta:
        verbose_name = "Secure File"
        verbose_name_plural = "Secure Files"

#-------------------------------------------------------------------------------
class SecureFileSlot(ContentSlot):
    file = models.ForeignKey(File, related_name='slots', on_delete=models.CASCADE)

    objects = WithRelated('file')

    class Meta:
        verbose_name_plural = "Files"
        ordering = ['order',]

register_atom_type(
        'secure_file',
        ReferencedAtomType(File, SecureFileSlot)
    )
