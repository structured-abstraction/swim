from swim.content.models import Page
from swim.core.models import ResourceType

def foo(request, form):
    Page.objects.create(
        path = '/new/page',
        resource_type = ResourceType.objects.get(title = 'default'),
        title = 'test page'
    )

def donothing(request, form):
    pass
