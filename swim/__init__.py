# threadlocals middleware
try:
    from threading import local
except ImportError:
    from django.utils._threading_local import local

_thread_locals = local()
def current_request():
    return getattr(_thread_locals, 'request', None)
request = property(current_request)
