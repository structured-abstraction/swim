from django import template
from django.contrib.auth.models import User
from swim.membership.models import Member

def member(member_or_user, args=''):
    """
    Pass in a member OR a user and retrieve their display name.
    """

    # Allow for a member OR a user to be passed in.
    user = None
    if isinstance(member_or_user, User):
        user = member_or_user
    elif isinstance(member_or_user, Member):
        user = member_or_user.user

    try:
        member = Member.objects.get(user=user)
    except Member.DoesNotExist:
        return 'Non-member'
    return member

register = template.Library()
register.filter('member', member)
