from django import forms
from swim.media.models import Image, File

#-------------------------------------------------------------------------------
class ImageForm(forms.ModelForm):
    class Meta:
        model = Image
        exclude = []

#-------------------------------------------------------------------------------
class FileForm(forms.ModelForm):
    class Meta:
        model = File
        exclude = []
