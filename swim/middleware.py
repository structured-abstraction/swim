"""
SWIM global middleware.
"""
import os

from django.conf import settings
from django.http import HttpResponseRedirect

#-------------------------------------------------------------------------------
class AdminRedirect:
    """
    Work around django's admin's inability to redirect the user after login.

    Django's admin doesn't have a redirect facility, so we have to use our own
    login method, OR we can use this method which only redirect staff members
    and only if they're logged in.

    Note: Run this _after_ the session middleware.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        redirect_to = request.GET.get('_admin_redirect')

        if request.user.is_authenticated and request.user.is_staff and \
                redirect_to:
            return HttpResponseRedirect(redirect_to)
        return self.get_response(request)


#-------------------------------------------------------------------------------
class Profile:
    """
    Profile django's views and then write the data to a file in the cwd.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        import cProfile
        self.profile = cProfile.Profile()
        self.lsprofcalltree = True

    def __call__(self, request):
        if request.GET.get('__swim_profile', None) != None:
            response = self.get_response(request)
            self.writedata()
            return response
        else:
            return self.get_response(request)

    def writedata(self):
        count = 1
        filename = None
        path = "swim-profile"
        base_path = getattr(settings, "SWIM_CACHEGRIND_TARGET_DIR", ".")
        while not filename or os.path.exists(filename):
            filename = os.path.join(base_path, "cachegrind.out.%s_%d" % (path, count))
            count += 1
        #print "writing profile output to %s" % filename
        if self.lsprofcalltree:
            from swim.thirdparty import lsprofcalltree
            k = lsprofcalltree.KCacheGrind(self.profile)
            data = open(filename, 'w+')
            k.output(data)
            data.close()
        else:
            self.profile.dump_stats(filename)

