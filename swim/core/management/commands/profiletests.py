from __future__ import print_function
from django.core.management.base import BaseCommand
from django.core.management.commands.test import Command as TestCommand
from optparse import make_option
import sys
import os

class Command(TestCommand):
    def writedata(self):
        from swim.thirdparty import lsprofcalltree
        count = 1
        filename = None
        path = "swim-test-profile"
        while not filename or os.path.exists(filename):
            filename = "cachegrind.out.%s_%d" % (path, count)
            count += 1
        print("writing profile output to %s" % filename)
        k = lsprofcalltree.KCacheGrind(self.profile)
        data = open(filename, 'w+')
        k.output(data)
        data.close()

    def handle(self, *test_labels, **options):
        import atexit
        from swim.thirdparty import lsprofcalltree
        import cProfile
        self.profile = cProfile.Profile()
        atexit.register(self.writedata)

        from django.conf import settings
        return self.profile.runcall(TestCommand.handle, self, *test_labels, **options)
