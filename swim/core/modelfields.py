from django.db import models
from django.db.models import signals
from swim.core import formfields

#-------------------------------------------------------------------------------
class Key(models.CharField):
    def __init__(self, *args, **kwargs):
        super(Key, self).__init__(*args, **kwargs)

    def formfield(self, **kwargs):
        defaults = {'form_class' : formfields.Key}
        defaults.update(kwargs)
        return super(Key, self).formfield(**defaults)

#-------------------------------------------------------------------------------
class Path(models.CharField):
    """A CharField which allows only alphanumeric url portions.

    This field uses strip('/')'s before it saves it's value.
    """

    def __init__(self, *args, **kwargs):
        # One can adjust the max_length, but we'll default it to 100
        if 'max_length' not in kwargs:
            kwargs['max_length'] = 255

        super(Path, self).__init__(*args, **kwargs)

    def formfield(self, **kwargs):
        defaults = {'form_class' : formfields.Path}
        defaults.update(kwargs)
        return super(Path, self).formfield(**defaults)

    def _strip_path_of_slashes(self, signal=None, sender=None, instance=None, **kwargs):
        """Paths should have their values all stripped of '/'s before saving.
        """
        if instance == None:
            return

        path = getattr(instance, self.attname, None)
        if path:
            # All paths MUST begin with "/"
            setattr(instance, self.attname, "/%s" % path.strip('/').lower())

    def contribute_to_class(self, cls, name):
        super(Path, self).contribute_to_class(cls, name)
        signals.pre_save.connect(self._strip_path_of_slashes, sender=cls)

