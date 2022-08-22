from django.db import models
from django.conf import settings

#-------------------------------------------------------------------------------
# A customization of django's model.fields TimeField which overrides the default
# input formats for times.
class TimeField(models.TimeField):
    def formfield(self, **kwargs):
        kwargs['input_formats'] = settings.TIME_INPUT_FORMATS
        return super(TimeField, self).formfield(**kwargs)

