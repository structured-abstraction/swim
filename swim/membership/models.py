import string
import random

from django.db import models, IntegrityError
from django.contrib.auth.models import User
from django.conf import settings


#-------------------------------------------------------------------------------
class Member(models.Model):
    """
    Member info such as email, display name, password etc.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.CASCADE
    )
    display_name = models.CharField(max_length=255, unique=True )
    username = models.CharField(max_length=255, unique=True, editable=False )
    given_name = models.CharField(max_length=255)
    family_name = models.CharField(max_length=255)

    postal_code = models.CharField(max_length=255, blank=True, null=True)

    email_address = models.EmailField(
        unique=True,
        help_text="Creating a new Member will send the new user an "
            " email with their password."
    )
    change_password_code = models.CharField(max_length=25, blank=True, null=True)

    creationdate = models.DateTimeField(auto_now_add = True)
    modifieddate = models.DateTimeField(auto_now = True)

    def __str__(self) :
        return u"%s" % ( self.display_name,)

    def save(self, *args, **kwargs):
        self.username = self.display_name.lower().replace(' ','')

        save_first_time = False
        if self.id is None:
            save_first_time = True

        super(Member, self).save(*args, **kwargs)


        if save_first_time:
            username = 'member_%d' % self.id
            u = User.objects.create(
                username = username,
                first_name = self.given_name,
                last_name = self.family_name,
                email = self.email_address,
                is_active = False,
            )
            self.user = u
            super(Member, self).save()

            # We want to send out passwords even when members are
            # created in the admin.
            self.create_change_password_code()

    def create_change_password_code(self, is_code=False):
        """
        Can be used to generate a random initial password for new member
        """
        password_characters = string.ascii_letters + string.digits# + string.punctuation
        password_characters = password_characters.replace(" ", "").replace("=", "")
        new_password = ''.join([random.choice(password_characters) for x in range(10)])

        # By default their password is the change_password_code
        self.change_password_code = new_password
        self.save()

