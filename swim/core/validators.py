import re

from django.template import Template
from django.forms.utils import ValidationError

#-------------------------------------------------------------------------------
alnumurl_re = re.compile(r'^[-\w/#\.~]+$')
alnum_re = re.compile(r'^\w+$')

#-------------------------------------------------------------------------------
def isValidTemplate(value):
    """
    Asserts the template doesn't raise an error when it's compiled.
    """
    try:
        t = Template(value)
    except Exception as e:
        raise ValidationError(str(e))

#-------------------------------------------------------------------------------
def isAlphaNumericURL(value):
    if value is None or not alnumurl_re.search(value):
        raise ValidationError("This value must contain only letters, numbers, underscores, dashes or slashes.")

#-------------------------------------------------------------------------------
def isAlphaNumeric(value):
    if value is None or not alnum_re.search(value):
        raise ValidationError("This value must contain only letters, numbers and underscores.")
