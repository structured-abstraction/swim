from datetime import datetime
import xml.dom.minidom
from io import StringIO

from django.contrib.sites.models import Site
from django.test import override_settings

from swim.test import TestCase
from swim.core.models import ResourceType
from swim.design.models import Template, ResourceTypeTemplateMapping
from swim.content.models import Page, CopySlot
from swim.membership.models import Member
from swim.blog.models import Post, Blog
from swim.syndication.models import RSSFeed

#-------------------------------------------------------------------------------
@override_settings(ROOT_URLCONF='swim.urls')
class SyndicationTests(TestCase):
    """These tests make sure some default behaviour for syndication works.
    """

    #---------------------------------------------------------------------------
    def setUp(self):
        from swim.design.management import COPY_BODY
        super(SyndicationTests, self).setUp()
        self.copy_template = Template.objects.create(
            path = '/',
            body = COPY_BODY,
            swim_content_type = CopySlot.swim_content_type(),
            http_content_type = 'text/html; charset=utf-8',
        )
        self.resource_type = ResourceType.objects.get(key = 'blog')
        ResourceTypeTemplateMapping.objects.create(
            resource_type = self.resource_type,
            template = self.copy_template
        )

        self.rss_feed_resource_type = ResourceType.objects.get(
                key = 'rss_feed',
            )
        self.blog_resource_type = ResourceType.objects.get(
                key = 'blog',
            )
        self.blog_post_resource_type = ResourceType.objects.get(
                key = 'post',
            )
        self.blogger = Member.objects.create(
            given_name = 'lakin',
            family_name = 'wecker',
            display_name='lakin.wecker.2',
            email_address='lakin.wecker@gmail.com',
        )
        self.password = 'foo'
        self.blogger.user.set_password(self.password)

        self.blog_path = '/a-better-kind-of-angry'
        self.blog_title = 'Le Whette Pirouette'

        self.blog_page = Blog.objects.create(
            path = self.blog_path,
            resource_type=self.blog_resource_type,
            title=self.blog_title,
        )
        self.blog_page_description = CopySlot.objects.create(
            content_object = self.blog_page,
            key = 'body',
            order = 0,
            body = "Don't pee into the wind",
        )



    #---------------------------------------------------------------------------
    def test_blog_rss_path(self):
        abkoa_rss_path = '/a-better-kind-of-angry/rss'
        abkoa_blog_path = '/a-better-kind-of-angry'

        # To start, that URL should 404
        response = self.client.get(abkoa_rss_path)
        self.assertEqual(404, response.status_code)


        rss_feed = RSSFeed.objects.create(
            path = abkoa_rss_path,
            blog = self.blog_page,
            resource_type=self.rss_feed_resource_type,
        )

        post_defs = (
                # (publish_date, body,)
                (datetime(2007, 1, 1), "one",),
                (datetime(2007, 2, 1), "two",),
                (datetime(2007, 3, 1), "three",),
                (datetime(2007, 4, 1), "four",),
                (datetime(2007, 5, 1), "five",),
                (datetime(2007, 6, 1), "six",),
                (datetime(2007, 7, 1), "seven",),
                (datetime(2007, 8, 1), "eight",),
                (datetime(2007, 9, 1), "nine",),
                (datetime(2007, 10, 1), "ten",),
                (datetime(2007, 11, 1), "eleven",),
                (datetime(2007, 12, 1), "twelve",),
            )
        posts = []
        for publish_date, body in post_defs:
            posts.append(Post.objects.create(
                    blogger = self.blogger,
                    blog=self.blog_page,
                    title=body,
                    publish_date = publish_date.date(),
                    publish_time = publish_date.time(),
                )
            )
            # Store the piece of copy for later use.
            posts[-1].tmp_copy = CopySlot.objects.create(
                content_object = posts[-1],
                key = 'body',
                order = 0,
                body = body,
            )


        # Now the url MUST return well-formed XML
        response = self.client.get(abkoa_rss_path)
        self.assertEqual(200, response.status_code)
        self.assertTrue(response['Content-Type'], 'application/rss+xml')

        self._testRSSFeedContent(response.content, posts)

        # If we set the appropriate Accept header so should the
        # blog url
        rss_accept_headers = {'HTTP_ACCEPT': 'application/rss+xml'}
        response = self.client.get(abkoa_blog_path, **rss_accept_headers)
        self.assertEqual(200, response.status_code)
        self.assertTrue(response['Content-Type'], 'application/rss+xml')
        self._testRSSFeedContent(response.content, posts)


    def _testRSSFeedContent(self, content, posts):
        try:
            doc = xml.dom.minidom.parseString(content)
        except:
            self.failWithTraceback("RSS Feed failed to be valid XML!")

        channel_nodes = doc.getElementsByTagName('channel')
        self.assertEqual(1, len(channel_nodes))
        channel = channel_nodes[0]


        test_cases = (
                # (node_name, count, values)
                # The count is eleven because the subsequent items ALSO have title tags
                ('title', 11, (
                    (0, self.blog_page.title),
                    ),),
                # The count is eleven because the subsequent items ALSO have link tags
                ('link', 11, (
                    (0, 'http://%s%s' % (Site.objects.get_current().domain, self.blog_page.url())),
                    ),),
                # The count is eleven because the subsequent items ALSO have description tags
                ('description', 11, (
                    (0, u'\n\n\n    <div class="copy copy_%s">\n    Don\'t pee into the wind\n    </div>\n\n' % self.blog_page_description.id),
                    ),),
            )
        for node_name, count, values in test_cases:
            nodes = channel.getElementsByTagName(node_name)
            self.assertEqual(
                    count, len(nodes),
                    "Expected %d of %s but only found %d" % (count, node_name, len(nodes))
                )
            for index, expected_value in values:
                feed_value = nodes[index].firstChild.nodeValue
                self.assertEqual(feed_value, expected_value)

        item_nodes = channel.getElementsByTagName('item')
        self.assertEqual(len(item_nodes), 10) # Our default template only shows 10
        for item_node, post in zip(item_nodes, reversed(posts[-11:])):
            post_url = 'http://%s%s' % (Site.objects.get_current().domain, post.url())
            pubDate = '%s %s' % (
                post.publish_date.strftime("%a, %d %b %Y"),
                post.publish_time.strftime("%H:%M:%S"),
            )
            tz = post.publish_date.strftime(" %Z")
            pubDate += tz
            test_cases = (
                    # (tag_name, count, values)
                    ('title', 1, (
                        (0, post.title),
                        ),),
                    ('link', 1, (
                        (0, post_url),
                        ),),
                    ('guid', 1, (
                        (0, post_url),
                        ),),
                    ('pubDate', 1, (
                        (0, pubDate),
                        ),),
                    ('description', 1, (
                        (0, '\n\n\n    <div class="copy copy_%s">\n    %s\n    </div>\n\n' % (post.tmp_copy.id, post.title)),
                        ),),
                )
            for tag_name, expected_count, values in test_cases:
                # Ensure the title element is properly set.
                nodes = item_node.getElementsByTagName(tag_name)
                self.assertEqual(expected_count, len(nodes))
                for index, expected_value in values:
                    value = nodes[index].firstChild.nodeValue
                    self.assertEqual(value, expected_value)

            # Ensure the link element is properly set.
            link_nodes = item_node.getElementsByTagName('link')
            self.assertEqual(1, len(link_nodes))
            link = link_nodes[0].firstChild.nodeValue
            self.assertEqual(link, post_url)


