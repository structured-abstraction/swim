from datetime import datetime
import xml.dom.minidom
from io import StringIO

from django.test import override_settings
from django.conf import settings
from django.utils import timezone

from swim.test import TestCase
from swim.core.models import (
    ResourceType,
)
from swim.design.models import (
    Template,
    ResourceTypeTemplateMapping,
)
from swim.content.models import (
    Page,
)
from swim.blog.models import (
    Post,
    Blog,
    BlogYear,
    BlogMonth,
    BlogDay,
)

from swim.chronology import utils as chronologytests
from swim.seo import utils as seo_test_utils

#-------------------------------------------------------------------------------
class BlogTimelineTests(chronologytests.TimelineTests):
    #---------------------------------------------------------------------------
    def setUp(self):
        super(BlogTimelineTests, self).setUp()

        self.start_datetime_attr = "publish_timestamp"
        self.end_datetime_attr = "publish_timestamp"
        self.resource_type_attr = 'resource_type'

        self.all_timeline_name = "all_blog_posts"
        self.timeline_resource_type = self.blog_resource_type = ResourceType.objects.get(
                key = 'blog',
            )

        self.event_resource_type = blog_post_resource_type = ResourceType.objects.get(
                key = 'post',
            )

        self.blog_path = '/blog'
        self.blog_title = 'Le Whette Pirouette'

        self.timeline = self.blog_page = Blog.objects.create(
            path=self.blog_path,
            resource_type=self.blog_resource_type,
            title=self.blog_title,
        )
        self.timeline_event_set = self.blog_page.posts.all()

        self.timeline2 = self.blog_page2 = Blog.objects.create(
            path=self.blog_path + '-2',
            resource_type=self.blog_resource_type,
            title=self.blog_title + '-2',
        )


    #---------------------------------------------------------------------------
    def _create_events(self, event_list, blog=None):
        if blog is None:
            blog = self.blog_page
        event_instance_list = []
        for event_type, title, start, end in event_list:
            resource_type = ResourceType.objects.get(key = event_type)
            if start:
                start_date = start.date()
                start_time = start.time()
            else:
                start_date = None
                start_time = None
            event_instance_list.append(
                Post.objects.create(
                    resource_type=resource_type,
                    blog=blog,
                    title=title,
                    publish_date=start_date,
                    publish_time=start_time,
                )
            )
        return event_instance_list



#-------------------------------------------------------------------------------
@override_settings(ROOT_URLCONF='swim.urls')
class BlogManagementTests(TestCase):
    """These tests make sure that the appropriate items are installed.
    """

    # TODO: These management tests aren't as useful in their current form.
    #       rather than testing that certain things are installed by default
    #       it might be a better use of our time to connect to the default site
    #       that is produced after the initial swim data is installed and to test
    #       that it works as intended.  This is a more functional sort of test
    #       and not really a unit test but I think it'll be immensely useful.

    #---------------------------------------------------------------------------
    def test_blog_type(self):
        try:
            self.blog_resource_type = ResourceType.objects.get(
                    key = 'blog',
                )
        except ResourceType.DoesNotExist:
            self.fail("swim.blog.management must install a Blog Page ResourceType")

    #---------------------------------------------------------------------------
    def test_blog_post_type(self):
        try:
            self.blog_post_resource_type = ResourceType.objects.get(
                    key = 'post',
                )
        except ResourceType.DoesNotExist:
            self.fail("swim.blog.management must install a Blog Post ResourceType")

#-------------------------------------------------------------------------------
@override_settings(ROOT_URLCONF='swim.urls')
class BlogTests(TestCase):
    """These tests make sure some default behaviour for blogs works.
    """

    #---------------------------------------------------------------------------
    def setUp(self):
        super(BlogTests, self).setUp()
        self.blog_resource_type = ResourceType.objects.get(
                key = 'blog',
            )
        self.blog_post_resource_type = ResourceType.objects.get(
                key = 'post',
            )

        self.template = Template.objects.create(
                path="/blog/index",
                body="BLOG!"
            )
        self.pagetypetemplate = ResourceTypeTemplateMapping.objects.create(
            order = 0,
            resource_type = self.blog_resource_type,
            template = self.template
        )

        self.blog_path = '/blog'
        self.blog_title = 'Le Whette Pirouette'

        self.blog_page = Blog.objects.create(
            path=self.blog_path,
            resource_type=self.blog_resource_type,
            title=self.blog_title,
        )


    #---------------------------------------------------------------------------
    def test_blog_request_handler_registration(self):
        abkoa_blog_path='/a-better-kind-of-angry'

        # To start, that URL should 404
        response = self.client.get(abkoa_blog_path + "/")
        self.assertEqual(404, response.status_code)

        blog_page = Blog.objects.create(
            path=abkoa_blog_path,
            resource_type=self.blog_resource_type,
            title='A Better Kind Of Angry',
        )

        # After creating the, there should be a valid response using the blog
        # resource_type template.
        response = self.client.get(abkoa_blog_path)
        self.assertEqual(200, response.status_code)
        self.assertEqual(b"BLOG!", response.content)
        self.assertEqual(blog_page, response.context['resource'])

        blog_page.delete()

        # After deleting the blog, it should once again 404.
        response = self.client.get(abkoa_blog_path + "/")
        self.assertEqual(404, response.status_code)


    #---------------------------------------------------------------------------
    def test_blog_time_objects_delete(self):
        # Before any posts are created, no Blog* objects should be created.
        self.assertEqual(0, BlogYear.objects.count())
        self.assertEqual(0, BlogMonth.objects.count())
        self.assertEqual(0, BlogDay.objects.count())


        #-----------------------------------------------------------------------
        test_cases = (
            # ( delta, year_count, month_count, day_count, body )
            (datetime(2008,0o1,0o1), 1, 1, 1, "one",),
            (datetime(2008,0o1,0o2), 1, 1, 2, "two",),
            (datetime(2008,0o2,0o1), 1, 2, 3, "three",),
            (datetime(2009,0o1,0o1), 2, 3, 4, "four",),
        )

        blog_posts = []
        for publish_date, year_count, month_count, day_count, body in test_cases:
            blog_posts.append(Post.objects.create(
                    blog=self.blog_page,
                    title=body,
                    publish_date = publish_date.date(),
                    publish_time = publish_date.time(),
                )
            )

            # After each post is created, some of the counts should increment.
            self.assertEqual(year_count, BlogYear.objects.count())
            self.assertEqual(month_count, BlogMonth.objects.count())
            self.assertEqual(day_count, BlogDay.objects.count())

        #-----------------------------------------------------------------------
        # In the following test cases, the numbers will slowly move towards 0
        test_cases = (
            # ( post, year_count, month_count, day_count,)
            (blog_posts[0], 2, 3, 3),
            (blog_posts[1], 2, 2, 2),
            (blog_posts[2], 1, 1, 1),
            (blog_posts[3], 0, 0, 0),
        )
        for post, year_count, month_count, day_count in test_cases:
            post.delete()

            # After each post is deleted, some of the counts should decrement.
            self.assertEqual(year_count, BlogYear.objects.count())
            self.assertEqual(month_count, BlogMonth.objects.count())
            self.assertEqual(day_count, BlogDay.objects.count())


    #---------------------------------------------------------------------------
    def test_blog_post_years_url(self):
        post_defs_in_08 = (
                # (publish_date, body,)
                (datetime(2008, 0o1, 0o1), "one",),
                (datetime(2008, 0o2, 0o1), "two",),
                (datetime(2008, 0o3, 0o1), "three",),
            )
        posts_in_08 = []
        for publish_date, body in post_defs_in_08:
            posts_in_08.append(Post.objects.create(
                    blog=self.blog_page,
                    title=body,
                    publish_date = publish_date.date(),
                    publish_time = publish_date.time(),
                )
            )
        post_defs_not_in_08 = (
                # (publish_date, title,)
                (datetime(2007, 0o1, 0o1), "four",),
                (datetime(2007, 0o2, 0o1), "five",),
                (datetime(2007, 0o3, 0o1), "six",),
                (datetime(2007, 12, 31), "seven",),
                (datetime(2009, 0o1, 0o1), "eight",),
            )
        posts_not_in_08 = []
        for publish_date, body in post_defs_not_in_08:
            posts_not_in_08.append(Post.objects.create(
                    blog=self.blog_page,
                    title=body,
                    publish_date = publish_date.date(),
                    publish_time = publish_date.time(),
                )
            )

        response = self.client.get('/blog/2008')
        self.assertEqual(self.blog_page, response.context['blog'])

        for post in posts_in_08:
            self.assertTrue(post in iter(response.context['resource'].post_list))

        for post in posts_not_in_08:
            self.assertFalse(post in response.context['resource'].post_list)

    #---------------------------------------------------------------------------
    def test_blog_post_months_url(self):
        post_defs_in_jan = (
                # (publish_date, body,)
                (datetime(2008, 0o1, 0o1), "one",),
                (datetime(2008, 0o1, 0o2), "two",),
                (datetime(2008, 0o1, 0o3), "three",),
            )
        posts_in_jan = []
        for publish_date, body in post_defs_in_jan:
            posts_in_jan.append(Post.objects.create(
                    blog=self.blog_page,
                    title=body,
                    publish_date = publish_date.date(),
                    publish_time = publish_date.time(),
                )
            )
        post_defs_not_in_jan = (
                # (publish_date, title,)
                (datetime(2007, 12, 31), "four",),
                (datetime(2008, 0o2, 0o1), "five",),
                (datetime(2009, 0o1, 0o1), "six",),
                (datetime(2007, 0o1, 0o1), "seven",),
            )
        posts_not_in_jan = []
        for publish_date, body in post_defs_not_in_jan:
            posts_not_in_jan.append(Post.objects.create(
                    blog=self.blog_page,
                    title=body,
                    publish_date = publish_date.date(),
                    publish_time = publish_date.time(),
                )
            )

        response = self.client.get('/blog/2008/1')
        self.assertEqual(self.blog_page, response.context['blog'])

        for post in posts_in_jan:
            self.assertTrue(post in response.context['resource'].post_list)

        for post in posts_not_in_jan:
            self.assertFalse(post in response.context['resource'].post_list)

    #---------------------------------------------------------------------------
    def test_blog_post_day_url(self):
        post_defs_on_the_first = (
                # (publish_date, body,)
                (datetime(2008, 0o1, 0o1), "one",),
                (datetime(2008, 0o1, 0o1), "two",),
                (datetime(2008, 0o1, 0o1), "three",),
            )
        post_on_the_first = []
        for publish_date, body in post_defs_on_the_first:
            post_on_the_first.append(Post.objects.create(
                    blog=self.blog_page,
                    title=body,
                    publish_date = publish_date.date(),
                    publish_time = publish_date.time(),
                )
            )
        post_defs_not_on_the_first = (
                # (publish_date, title,)
                (datetime(2007, 0o1, 0o2), "four",),
                (datetime(2008, 12, 31), "five",),
            )
        posts_on_the_first = []
        for publish_date, body in post_defs_not_on_the_first:
            posts_on_the_first.append(Post.objects.create(
                    blog=self.blog_page,
                    title=body,
                    publish_date = publish_date.date(),
                    publish_time = publish_date.time(),
                )
            )

        response = self.client.get('/blog/2008/1/1')
        self.assertEqual(self.blog_page, response.context['blog'])

        for post in post_on_the_first:
            self.assertTrue(post in response.context['resource'].post_list)

        for post in posts_on_the_first:
            self.assertFalse(post in response.context['resource'].post_list)

    #---------------------------------------------------------------------------
    def test_blog_post_scot(self):
        Page.objects.all().delete()
        self.blog = Blog.objects.create(
            resource_type = self.blog_resource_type,
            path = '/',
            title = 'eagles'
        )
        self.template = Template.objects.create(
            path = '/',
            body = """asdf
{% for post in resource.post_list %}1
    {{ post }}
{% endfor %}""",
        )
        ResourceTypeTemplateMapping.objects.create(
            order=-1, # Make sure this is the highest priority
            resource_type = self.blog_resource_type,
            template = self.template
        )
        Post.objects.create(
            blog = self.blog,
            title = 'blog post 1',
            name = 'eagles',
            publish_date = datetime(2008, 0o1, 0o1).date(),
            publish_time = datetime(2008, 0o1, 0o1).time()
        )
        response = self.client.get('/')
        self.assertIn('blog post 1', response.content)


    #---------------------------------------------------------------------------
    def test_blog_post_url(self):
        post_defs = (
                # (publish_date, body,)
                (datetime(2008, 0o1, 0o1), "one",),
            )
        actual_posts = []
        for publish_date, body in post_defs:
            actual_posts.append(Post.objects.create(
                    resource_type = self.blog_post_resource_type,
                    blog=self.blog_page,
                    title=body,
                    name=body,
                    publish_date = publish_date.date(),
                    publish_time = publish_date.time(),
                )
            )
        other_post_defs = (
                # (publish_date, title,)
                (datetime(2008, 0o1, 0o1), "two",),
                (datetime(2008, 0o1, 0o1), "three",),
                (datetime(2007, 0o1, 0o2), "four",),
                (datetime(2008, 12, 31), "five",),
            )
        other_posts = []
        for publish_date, body in other_post_defs:
            other_posts.append(Post.objects.create(
                    resource_type = self.blog_post_resource_type,
                    blog=self.blog_page,
                    title=body,
                    publish_date = publish_date.date(),
                    publish_time = publish_date.time(),
                )
            )

        response = self.client.get('/blog/2008/1/1/one')

        self.assertEqual(self.blog_page, response.context['blog'])

        for post in actual_posts:
            self.assertEqual(post, response.context['resource'])

        for post in other_posts:
            self.assertNotEqual(post, response.context['resource'])

    #---------------------------------------------------------------------------
    def test_blog_post_odd_title_characters(self):
        """Ensure that a wide variety of titles won't mess up the URLS to the post."""
        post_defs = (
                # (publish_date, title)
                (datetime(2008, 0o1, 0o1), 'one:one'),
                (datetime(2008, 0o1, 0o1), 'one::one'),
                (datetime(2008, 0o1, 0o1), 'one : one'),
                (datetime(2008, 0o1, 0o1), 'two%two'),
                (datetime(2008, 0o1, 0o1), 'three?three')
            )
        actual_posts = []
        for publish_date, body in post_defs:
            actual_posts.append(Post.objects.create(
                    resource_type=self.blog_post_resource_type,
                    blog=self.blog_page,
                    title=body,
                    publish_date=publish_date.date(),
                    publish_time=publish_date.time()
                )
            )

        response = self.client.get('/blog/2008/1/1/oneone-' + str(actual_posts[0].id))
        self.assertEqual(actual_posts[0], response.context['resource'])

        response = self.client.get('/blog/2008/1/1/oneone-' + str(actual_posts[1].id))
        self.assertEqual(actual_posts[1], response.context['resource'])

        response = self.client.get('/blog/2008/1/1/one-one-' + str(actual_posts[2].id))
        self.assertEqual(actual_posts[2], response.context['resource'])

        response = self.client.get('/blog/2008/1/1/twotwo-' + str(actual_posts[3].id))
        self.assertEqual(actual_posts[3], response.context['resource'])

        response = self.client.get('/blog/2008/1/1/threethree-' + str(actual_posts[4].id))
        self.assertEqual(actual_posts[4], response.context['resource'])

    #---------------------------------------------------------------------------
    def test_blog_url(self):
        post_defs = (
                # (publish_date, body,)
                (datetime(2008, 0o1, 0o1), "one",),
                (datetime(2008, 0o1, 0o1), "two",),
                (datetime(2008, 0o1, 0o1), "three",),
                (datetime(2007, 0o1, 0o2), "four",),
                (datetime(2008, 12, 31), "five",),
            )
        actual_posts = []
        for publish_date, body in post_defs:
            actual_posts.append(Post.objects.create(
                    resource_type = self.blog_post_resource_type,
                    blog=self.blog_page,
                    title=body,
                    name=body,
                    publish_date = publish_date.date(),
                    publish_time = publish_date.time(),
                )
            )

        response = self.client.get('/blog')
        self.assertEqual(self.blog_page, response.context['blog'])

        for post in actual_posts:
            self.assertTrue(post in list(response.context['resource'].post_list))
            self.assertTrue(post in list(response.context['blog'].post_list))

    #---------------------------------------------------------------------------
    def test_creating_page_with_blog_url(self):
        user = self.create_and_login_superuser('lakin2', 'password')

        # TODO: referring to types by id? Really?!?!
        data = {
            'resource_type': 4,
            'path': '',
        }
        # Because we've created a blog rooted at these urls ALL of the following
        # page creations MUST fail

        test_cases = (
                ('%s' % self.blog_path, 1,
                    'All paths starting with /blog are reserved.',),
                ('%s/foo' % self.blog_path, 0,
                    'All paths starting with /blog are reserved.',),
                ('%s/foo/index' % self.blog_path, 0,
                    'All paths starting with /blog are reserved.',),
                ('%s/foo/index/shoo' % self.blog_path, 0,
                    'All paths starting with /blog are reserved.',),
            )

        for page_path, page_count, error_message in test_cases:
            data['path'] = page_path
            response = self.client.post("/admin/content/page/add/?no_initial_formsets=1", data)
            self.assertContains(response, error_message)

            # There _is_ a blog page, so the other pages should fail.
            self.assertEqual(page_count, Blog.objects.filter(path=page_path).count())


    #---------------------------------------------------------------------------
    def test_blog_page_path_moves_all_posts_request_handlers(self):

        # First create some blog posts
        test_cases = (
            # ( delta, year_count, month_count, day_count, body )
            (datetime(2008,0o1,0o1), 1, 1, 1, "one",),
            (datetime(2008,0o1,0o2), 1, 1, 2, "two",),
            (datetime(2008,0o2,0o1), 1, 2, 3, "three",),
            (datetime(2009,0o1,0o1), 2, 3, 4, "four",),
        )

        blog_posts = []
        for publish_date, year_count, month_count, day_count, body in test_cases:
            blog_posts.append(Post.objects.create(
                    blog=self.blog_page,
                    title=body,
                    publish_date = publish_date.date(),
                    publish_time = publish_date.time(),
                )
            )

        for post in blog_posts:
            self.assertIn(self.blog_path, post.url())

        self.blog_page.path = '/blog-new-for-you!'
        self.blog_page.save()

        for post in blog_posts:
            post = Post.objects.get(id=post.id)
            self.assertIn(self.blog_page.path, post.url())


#-------------------------------------------------------------------------------
class BlogSEOTests(seo_test_utils.HasSEOAttributesTest):

    #---------------------------------------------------------------------------
    def setUp(self):
        super(BlogSEOTests, self).setUp()
        self.resource_type = ResourceType.objects.create(
            key='new_type',
            title = 'New Page Type',
        )

    #---------------------------------------------------------------------------
    def create_resource(self, path):
        return Blog.objects.create(
                resource_type=self.resource_type,
                path=path,
                title=path,
            )

#-------------------------------------------------------------------------------
class PostSEOTests(seo_test_utils.HasSEOAttributesTest):

    #---------------------------------------------------------------------------
    def setUp(self):
        super(PostSEOTests, self).setUp()
        self.resource_type = ResourceType.objects.create(
            key='new_type',
            title = 'New Page Type',
        )
        self.blog = Blog.objects.create(
                resource_type=self.resource_type,
                path="/something",
                title="Something Title",
            )

    #---------------------------------------------------------------------------
    def create_resource(self, path):
        return Post.objects.create(
                blog=self.blog,
                publish_date=datetime.now().date(),
                publish_time=datetime.now().time(),
                resource_type=self.resource_type,
                name=path.replace("/", ""),
                title=path,
            )

