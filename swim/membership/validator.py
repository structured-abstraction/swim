"""
Validators specific to the membership application.
"""
from django import forms

from swim.membership.models import Member

#-------------------------------------------------------------------------------
def registration_validator(form, cleaned_data):
    """
    Ensure the email address isn't already used.
    """
    email_address = cleaned_data.get('email_address', None)
    try:
        member = Member.objects.get(email_address=email_address)
        raise forms.ValidationError("That email address already is a member")
    except Member.DoesNotExist:
        pass

    display_name = cleaned_data.get('display_name', None)
    try:
        member = Member.objects.get(display_name=display_name)
        raise forms.ValidationError("That display name is already taken.")
    except Member.DoesNotExist:
        pass

    if not display_name:
        raise forms.ValidationError("Display name is required.")

    username = display_name.lower().replace(' ', '')
    try:
        member = Member.objects.get(username=username)
        raise forms.ValidationError("That display name is not available.")
    except Member.DoesNotExist:
        pass

    return cleaned_data



#-------------------------------------------------------------------------------
def confirmation_password_validator(form, cleaned_data):
    """
    Validation that ensures the user has entered the same password twice.
    """
    new_password = cleaned_data.get('new_password', None)
    new_password_again = cleaned_data.get('new_password_again', False)
    if new_password != new_password_again:
        raise forms.ValidationError("Passwords do not match.")
    return cleaned_data

#-------------------------------------------------------------------------------
def change_password_validator(form, cleaned_data):
    """
    Validation that ensures the user has entered the correct current pw.
    """
    if not form.request.user.is_authenticated:
        raise forms.ValidationError("Not logged in!")

    cleaned_data = confirmation_password_validator(form, cleaned_data)

    if not form.request.user or not form.request.user.check_password(
            cleaned_data.get('current_password', None)):
        raise forms.ValidationError("Invalid password")

    return cleaned_data

#-------------------------------------------------------------------------------
def forgotten_password_validator(form, cleaned_data):
    """
    Validation that ensures the user has entered a valid email address.
    """
    try:
        cleaned_data['member'] = Member.objects.get(
                email_address=cleaned_data.get('email_address', None))
    except Member.DoesNotExist:
        raise forms.ValidationError("Invalid email address")

    return cleaned_data

#-------------------------------------------------------------------------------
def member_login_validator(form, cleaned_data):
    """
    Validation that ensures the user has entered a valid email and password.
    """
    try:
        member = cleaned_data['member'] = Member.objects.get(
                email_address=cleaned_data.get('email_address', None))
    except Member.DoesNotExist:
        raise forms.ValidationError("Invalid email address")

    if not member.user or not member.user.is_active:
        raise forms.ValidationError("This account has been disabled")

    if not member.user or not member.user.check_password(
            cleaned_data.get('password', None)):
        raise forms.ValidationError("Invalid password")

    return cleaned_data
