import traceback

from django import test
from django.conf import settings
from django.contrib.auth.models import User
from django.core import management
from django.db.backends.base.creation import BaseDatabaseCreation
from django.utils.encoding import smart_str

#-------------------------------------------------------------------------------
# Monkey patch django's connection class to ensure we only syncswimdata right
# after creating the db (this will run when we _don't_ use SOUTH migrations for
# creating the test db.
BaseDatabaseCreation._real_create_test_db = BaseDatabaseCreation.create_test_db
def create_test_db(self, verbosity=1, autoclobber=False, serialize=True, keepdb=False):
    retval = self._real_create_test_db(verbosity=verbosity, autoclobber=autoclobber, serialize=serialize, keepdb=keepdb)
    if 'syncswimdata' in management.get_commands():
        management.call_command('syncswimdata', verbosity=verbosity, interactive=False)
    return retval
BaseDatabaseCreation.create_test_db = create_test_db

#-------------------------------------------------------------------------------
class SWIMTestMixin:

    #---------------------------------------------------------------------------
    def setUp(self):
        from swim.core import models
        models.CONTENT_TYPE_CACHE = {}
        self.OLD_SWIM_RUN_MIDDLEWARE = settings.SWIM_RUN_MIDDLEWARE
        self.OLD_SWIM_RUN_RESPONSE_PROCESSOR = settings.SWIM_RUN_RESPONSE_PROCESSOR

        settings.SWIM_RUN_MIDDLEWARE = True
        settings.SWIM_RUN_RESPONSE_PROCESSOR = True
        super(SWIMTestMixin, self).setUp()

    #---------------------------------------------------------------------------
    def tearDown(self):
        settings.SWIM_RUN_MIDDLEWARE = self.OLD_SWIM_RUN_MIDDLEWARE
        settings.SWIM_RUN_RESPONSE_PROCESSOR = self.OLD_SWIM_RUN_RESPONSE_PROCESSOR
        super(SWIMTestMixin, self).tearDown()

    #---------------------------------------------------------------------------
    def assertIn(self, subject, target, message=None):
        error_message = u"Could not find [%s] within [%s]" % (subject, target)
        if message:
            error_message += u" " + str(message)
        self.assertTrue(
            smart_str(subject) in smart_str(target),
            error_message,
        )

    #---------------------------------------------------------------------------
    def assertNotIn(self, subject, target):
        self.assertFalse(
            smart_str(subject) in smart_str(target),
            "Incorrectly found [%s] within [%s]" % (subject, target),
        )

    #---------------------------------------------------------------------------
    def assertCount(self, count, subject, target):
        self.assertEqual(count, target.count(subject),
            "Could not find [%s] %s times within [%s]" % (subject, count, target),
        )


    #---------------------------------------------------------------------------
    def failWithTraceback(self, message):
        """
        For use within an except block that caught an exception indicating fail.
        """
        message = "\n\n".join([message, traceback.format_exc()])
        self.fail(message)


    #---------------------------------------------------------------------------
    def create_and_login_superuser(self, username, password):
        user = User.objects.create(
                username=username,
                is_active=True,
                is_staff=True,
                is_superuser=True,
                email='%s@structuredabstraction.com' % username,
            )
        user.set_password(password)
        user.save()
        self.client.login(username=username, password=password)
        return user

    #---------------------------------------------------------------------------
    def create_and_login_nonsuperuser(self, username, password):
        user = User.objects.create(
                username=username,
                is_active=True,
                is_staff=True,
                is_superuser=False,
                email='%s@structuredabstraction.com' % username,
            )
        user.set_password(password)
        user.save()
        self.client.login(username=username, password=password)
        return user

#-------------------------------------------------------------------------------
class TestCase(SWIMTestMixin, test.TestCase):
    pass
#-------------------------------------------------------------------------------
class TransactionTestCase(SWIMTestMixin, test.TransactionTestCase):
    pass
