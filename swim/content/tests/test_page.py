from swim.content.tests.base import NoContentTestCase
from swim.core.models import (
    ResourceType,
    ReservedPath,
    ContentSchema,
    ContentSchemaMember,
)
from swim.design.models import Template, ResourceTypeTemplateMapping
from swim.content.models import (
    Page,
    Link,
    Menu,
    MenuLink,
    MenuSlot,
)
from django.test import override_settings

#-------------------------------------------------------------------------------
@override_settings(ROOT_URLCONF='swim.urls')
class PageTest(NoContentTestCase):

    def test_empty_site_404(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 404)

    def test_empty_site_no_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 404)

    def test_path_case_matchin(self):
        self.template = Template.objects.create(
            path = '/Eagles',
            http_content_type = 'text/html; charset=utf-8',
            body = '',
        )
        self.content_schema = ContentSchema.objects.create(title="Eagles")
        self.resource_type = ResourceType.objects.create(
            title = 'Eagles',
            content_schema = self.content_schema,
        )
        ResourceTypeTemplateMapping.objects.create(
            resource_type = self.resource_type,
            template = self.template
        )
        self.page = Page.objects.create(
            resource_type = self.resource_type,
            path = '/Eagles',
            title = 'eagles'
        )
        response = self.client.get('/Eagles')
        self.assertRedirects(response, '/eagles')

    def test_empty_path_does_not_error(self):
        data = {
            'path': u'/',
            'resource_type': ResourceType.objects.get(key="simple_page").id,
            'title': u'Premier Bundles',
            '_continue': u'Save and continue editing',
            'sitemap_include': 1,
            'sitemap_priority': 10,
            'sitemap_change_frequency': "yearly",
            'meta_no_follow': 1,
            'meta_no_index': 1,
            'meta_description': "",
            'meta_keywords': "",
        }

        user = self.create_and_login_superuser('lakin2', 'password')
        # The first one works - uses a path of '/'
        response = self.client.post("/admin/content/page/add/?no_initial_formsets=1", data)

        # The second should also work - generates a path from title
        data['path'] = u''
        response = self.client.post("/admin/content/page/add/?no_initial_formsets=1", data)
        self.assertEqual(1, len(Page.objects.filter(path='/premier-bundles')))

        # The third one should give the user a valid error about
        # non-unique paths.
        data['path'] = u''
        response = self.client.post("/admin/content/page/add/?no_initial_formsets=1", data)
        self.assertEqual(200, response.status_code)
        self.assertContains(
                response,
                'No path was provided, so a path was generated from the title ' \
                '- /premier-bundles. There already exists a Page with the path ' \
                'of: &quot;/premier-bundles&quot;',
            )

    def test_path_reservation_admin_validation(self):
        user = self.create_and_login_superuser('lakin2', 'password')

        data = {
            'resource_type': ResourceType.objects.get(key="simple_page").id,
            'path': u'/foo',
            'title': 'Foo page title',
            'sitemap_include': 1,
            'sitemap_priority': 10,
            'sitemap_change_frequency': "yearly",
            'meta_no_follow': 1,
            'meta_no_index': 1,
            'meta_description': "",
            'meta_keywords': "",
        }
        # Before we have reserved any of the paths we MUST be allowed
        # to create resources on that path.

        response = self.client.post("/admin/content/page/add/?no_initial_formsets=1", data)
        self.assertNotIn(
                'There already exists a Page with the path of:', response.content
            )
        try:
            p = Page.objects.get(path='/foo')
        except Page.DoesNotExist:
            self.fail("Posting to the above path MUST have created the page '/foo'")
        p.delete()

        test_cases = (
                ('/foo', 'single', '/foo',
                    'There already exists a resource with the path of:',),
                ('/foo', 'tree', '/foo',
                    'All paths starting with /foo are reserved.',),
                ('/foo', 'tree', '/foo/index',
                    'All paths starting with /foo are reserved.',),
                ('/foo', 'tree', '/foo/index/shoo',
                    'All paths starting with /foo are reserved.',),
                ('/foo/index', 'tree', '/foo/index/shoo',
                    'All paths starting with /foo/index are reserved.',),
                ('/foo/index/shoo', 'tree', '/foo/index/shoo',
                    'All paths starting with /foo/index/shoo are reserved.',),
            )

        for reserved_path, reservation_type, page_path, error_message in test_cases:
            reservation = ReservedPath.objects.create(
                    # In this case the related object isn't actually pertinent
                    content_object=user,
                    path=reserved_path,
                    reservation_type=reservation_type,
                )
            data['path'] = page_path
            response = self.client.post("/admin/content/page/add/?no_initial_formsets=1", data)
            self.assertContains(response, error_message)
            self.assertEqual(0, Page.objects.filter(path=page_path).count())

            reservation.delete()

    def test_editing_of_pages_with_resource_types_that_are_not_normally_selectable(self):
        user = self.create_and_login_superuser('lakin2', 'password')

        data = {
            'resource_type': ResourceType.objects.get(key='simple_page').id,
            'title': 'Foo!',
            'path': '/foo',
            'sitemap_include': 1,
            'sitemap_priority': 10,
            'sitemap_change_frequency': "yearly",
            'meta_no_follow': 1,
            'meta_no_index': 1,
            'meta_description': "",
            'meta_keywords': "",
        }
        # Before we have reserved any of the paths we MUST be allowed
        # to create resources on that path.
        response = self.client.post("/admin/content/page/add/?no_initial_formsets=1", data)
        try:
            p = Page.objects.get(path='/foo')
        except Page.DoesNotExist:
            self.fail("Posting to the above path MUST have created the page '/foo'")

        self.assertEqual(data['title'], p.title)

        resource_type = ResourceType.objects.get(key='blog_year')

        # Before we change the page type we should get an error if we try to
        # change the resource type during submission
        # So this _should_ fail
        # TODO: Get this test working.
        # data['resource_type'] = resource_type.id
        # data['title'] = 'New Title'
        # data['id'] = p.id
        # data['_continue'] = True
        # response = self.client.post("/admin/content/page/%d/" % p.id, data)
        # self.assertEqual(200, response.status_code)
        # print response
        # p = Page.objects.get(path='/foo')
        # self.assertNotEqual(data['title'], p.title)

        # We are allowed to update pages to something that's not editable.
        p.resource_type = resource_type
        p.save()

        # Once saved, the administration interface for said page MUST show the
        # right type in the edit screen:
        response = self.client.get("/admin/content/page/%d/change/" % p.id)
        expected_select = '<option value="%d" selected>%s</option>' % (
                p.resource_type.id,
                p.resource_type.title,
            )
        self.assertContains(response, expected_select)

        # We MUST also be able to save the page from the admin changing its
        # title - but only because it was already of that resource
        data['resource_type'] = p.resource_type.id
        data['title'] = 'New Title'
        data['id'] = p.id
        data['_continue'] = True
        response = self.client.post("/admin/content/page/%d/change/" % p.id, data)
        self.assertEqual(302, response.status_code)

        p = Page.objects.get(path='/foo')
        self.assertEqual(data['title'], p.title)

    def test_page_maintains_and_deletes_link(self):
        page = Page.objects.create(
            path='/foo',
            title='Foo',
        )
        try:
            link = Link.objects.get(url='/foo')
        except Link.DoesNotExist:
            self.fail("Page fails to create its own link")

        self.assertEqual(page.ownlink, link)

        page.delete()

        try:
            link = Link.objects.get(url='/foo')
            self.fail("Page failed to delete its associated link")
        except Link.DoesNotExist:
            pass

#-------------------------------------------------------------------------------
@override_settings(ROOT_URLCONF='swim.urls')
class MenuTreeTests(NoContentTestCase):

    #---------------------------------------------------------------------------
    def setUp(self):
        super(MenuTreeTests, self).setUp()
        self.content_schema = ContentSchema.objects.create(title="Eagles")
        self.sub_nav = ContentSchemaMember.objects.create(
                content_schema=self.content_schema,
                order=1,
                title="Sub Nav",
                key="sub_nav",
                cardinality="single",
                swim_content_type=Menu.swim_content_type(),
            )
        self.simple_page_resource_type = ResourceType.objects.create(
            key="simple_page_test",
            title='Simple Page(test)',
            content_schema=self.content_schema,
        )
        self.home_page_resource_type = ResourceType.objects.create(
            key="home_page_test",
            title = 'Home(test)',
        )

    #---------------------------------------------------------------------------
    def test_menu_tree_generation(self):
        home_page = Page.objects.create(
            resource_type=self.home_page_resource_type,
            path = '/',
            title = 'Home'
        )
        about_page = Page.objects.create(
            resource_type=self.simple_page_resource_type,
            path = '/about',
            title = 'About'
        )
        about_history_page = Page.objects.create(
            resource_type=self.simple_page_resource_type,
            path = '/about/history',
            title = 'About History'
        )
        about_other_page = Page.objects.create(
            resource_type=self.simple_page_resource_type,
            path = '/about/other',
            title = 'About other'
        )
        about_history_first_years = Page.objects.create(
            resource_type=self.simple_page_resource_type,
            path = '/about/history/first-years',
            title = 'About History: First Years'
        )
        about_history_2007 = Page.objects.create(
            resource_type=self.simple_page_resource_type,
            path = '/about/history/first-years/2007',
            title = 'About History: First Years 2007'
        )
        about_history_2008 = Page.objects.create(
            resource_type=self.simple_page_resource_type,
            path = '/about/history/first-years/2008',
            title = 'About History: First Years 2008'
        )
        about_history_2009 = Page.objects.create(
            resource_type=self.simple_page_resource_type,
            path = '/about/history/first-years/2009',
            title = 'About History: First Years 2009'
        )
        about_history_final_years = Page.objects.create(
            resource_type=self.simple_page_resource_type,
            path = '/about/history/other-years',
            title = 'About History: Other Years'
        )

        # Setup the section menus.
        about_page_menu = Menu.objects.create(
                title="About Page Menu",
            )
        for count, page in enumerate((about_history_page, about_other_page)):
            MenuLink.objects.create(
                    menu=about_page_menu,
                    order=count,
                    link=page.ownlink,
                )
        MenuSlot.objects.create(
                key='sub_nav',
                order=1,
                menu=about_page_menu,
                content_object=about_page,
            )
        about_history_menu = Menu.objects.create(
                title="About History Page Menu",
            )
        for count, page in enumerate((about_history_first_years, about_history_final_years)):
            MenuLink.objects.create(
                    menu=about_history_menu,
                    order=count,
                    link=page.ownlink,
                )
        MenuSlot.objects.create(
                key='sub_nav',
                order=1,
                menu=about_history_menu,
                content_object=about_history_page,
            )

        about_history_first_years_menu = Menu.objects.create(
                title="About History Page Menu",
            )
        for count, page in enumerate(
                (
                    about_history_2007, about_history_2008, about_history_2009
                )
            ):
            MenuLink.objects.create(
                    menu=about_history_first_years_menu,
                    order=count,
                    link=page.ownlink,
                )
        MenuSlot.objects.create(
                key='sub_nav',
                order=1,
                menu=about_history_first_years_menu,
                content_object=about_history_first_years,
            )

        menu_tree = about_history_first_years.menu_tree['sub_nav']

        # In this diagram we use the following acronyms to make it shorter:
        # a = about
        # h = history
        # fy = first-years
        # oy = other-years
        # o = other
        # 7 = 2007
        # 8 = 2008
        # 9 = 2009
        # We should get a tree that looks like this:
        #----------------------------------------------------------------------
        #  /a +
        #     | /a/h (active) +
        #                     | /a/h/fy (active) +
        #                                        | /a/h/fy/7 (inactive)
        #                                        | /a/h/fy/8 (inactive)
        #                                        | /a/h/fy/9 (inactive)
        #                     | /a/h/oy (inactive)
        #     | /a/o (inactive)
        self.assertEqual(menu_tree.url, "/about")
        self.assertEqual(menu_tree.title, "About")
        self.assertEqual(len(menu_tree.children), 2)
        self.assertTrue(menu_tree.active)

        inactive_child = menu_tree.children[1]
        self.assertEqual(inactive_child.url, "/about/other")
        self.assertEqual(inactive_child.title, "About other")
        self.assertEqual(inactive_child.children,[])
        self.assertFalse(inactive_child.active)

        active_child = menu_tree.children[0]
        self.assertEqual(active_child.url, "/about/history")
        self.assertEqual(active_child.title, "About History")
        self.assertEqual(len(active_child.children), 2)
        self.assertTrue(active_child.active)

        inactive_child = active_child.children[1]
        self.assertEqual(inactive_child.url, "/about/history/other-years")
        self.assertEqual(inactive_child.title, "About History: Other Years")
        self.assertEqual(inactive_child.children,[])
        self.assertFalse(inactive_child.active)

        active_child = active_child.children[0]
        self.assertEqual(active_child.url, "/about/history/first-years")
        self.assertEqual(active_child.title, "About History: First Years")
        self.assertEqual(len(active_child.children), 3)
        self.assertTrue(active_child.active)

        for i, year in enumerate(["2007", "2008", "2009"]):
            final_child = active_child.children[i]
            self.assertEqual(final_child.url, "/about/history/first-years/" + year)
            self.assertEqual(final_child.title, "About History: First Years " + year)
            self.assertEqual(len(final_child.children), 0)
            self.assertFalse(final_child.active)

