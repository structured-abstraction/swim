from swim.content.models import Page
from swim.core.models import (
    ResourceType,
)
from swim.seo import utils as seo_test_utils

#-------------------------------------------------------------------------------
class PageSEOTests(seo_test_utils.HasSEOAttributesTest):

    model = Page

    #---------------------------------------------------------------------------
    def setUp(self):
        super(PageSEOTests, self).setUp()
        self.resource_type = ResourceType.objects.create(
            key='new_type',
            title = 'New Page Type',
        )

    #---------------------------------------------------------------------------
    def create_resource(self, path):
        return Page.objects.create(
                resource_type=self.resource_type,
                path=path,
                title=path,
            )

