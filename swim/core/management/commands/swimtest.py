"""
Provides a swimtest command which skips tests listed in settings.SKIP_TESTS
"""
from django.conf import settings
from django.core.management.commands import test
from django.test.simple import get_tests
from django.db.models import get_app

from south.management.commands import patch_for_test_db_setup

def app_label(app_name):
    return app_name.split('.')[-1]

class Command(test.Command):
    def handle(self, *test_labels, **kwargs):
        patch_for_test_db_setup()

        # If they've asked for specific tests, let 'em have it.
        # otherwise test only the apps that we want to test.
        if not test_labels:
            SKIP_TESTS = getattr(settings, 'SKIP_TESTS', [])

            # Filter out tests based on our SKIP_TESTS attribute
            test_labels = [
                app_label(app) for app in settings.INSTALLED_APPS if app not in SKIP_TESTS]

            # Filter out labels based on whether they are an app or not.
            test_labels = [
                app for app in test_labels if get_app(app, emptyOK=True)]
            test_labels = [
                app for app in test_labels if get_tests(get_app(app))]

        super(Command, self).handle(*test_labels, **kwargs)

