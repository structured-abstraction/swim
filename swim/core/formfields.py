from os import path

from django import forms
from django.forms import fields
from django.forms.utils import ValidationError

from swim.core.validators import isAlphaNumeric, isAlphaNumericURL

#-------------------------------------------------------------------------------
class Key(forms.CharField):
    def clean(self, value):
        value = value.strip() # strip whitespace from either side
        if value != '':
            isAlphaNumeric(value)
        return value

#-------------------------------------------------------------------------------
class Path(forms.CharField):
    def clean(self, value):
        value = value.strip() # strip whitespace from either side
        if value != '':
            isAlphaNumericURL(value)
        return value

