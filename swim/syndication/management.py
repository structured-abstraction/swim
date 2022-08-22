from swim.core import signals
from swim.core.management import create_groups, create_resource_types
from swim.syndication import models
from swim.design.models import (
    Template,
    ResourceTypeTemplateMapping,
)
from swim.core.models import (
    Resource,
    ResourceType,
    ResourceTypeSwimContentTypeMapping,
)
from swim.content.models import (
    Page,
)
from swim.blog.models import (
    Post,
)
from swim.syndication.models import (
    RSSFeed,
)



#-------------------------------------------------------------------------------
RSS_GROUPS = (
    # (group_name, app_label, codename)
    ("RSS Editor", "syndication", "add_rssfeed",),
    ("RSS Editor", "syndication", "change_rssfeed",),
    ("RSS Editor", "syndication", "delete_rssfeed",),
)

#-------------------------------------------------------------------------------
RESOURCE_TYPES = (
    # ( parent, key, title, swim_content_type, interface )
    ('blog', 'rss_feed', 'RSS Feed', RSSFeed.swim_content_type, None),
)

#-------------------------------------------------------------------------------
RSS_PAGES = (
        # ( type_key, path, blog )
        ('rss_feed', '/news/rss', '/news'),
    )

#-------------------------------------------------------------------------------
DEFAULT_RSS_POST_TEMPLATE = """
{% load swim_tags %}<item>
  <title>{{target.title}}</title>
  <link>http://{{site.domain}}{{target.url}}</link>
  {% get_resource for target as target %}
  <description><![CDATA[{% render target.copy.body %}]]></description>
  <pubDate>{{target.publish_date|date:"D, d M Y"}} {{target.publish_time|time:"H:i:s"}}{{target.publish_time|date:" Z"}}</pubDate>
  <guid isPermaLink="true">http://{{site.domain}}{{target.url}}</guid>
</item>
"""

#-------------------------------------------------------------------------------
DEFAULT_RSS_TEMPLATE = """{% load swim_tags %}<?xml version="1.0"?>
<rss version="2.0">
  <channel>
    <title>{{blog.title}}</title>
    <link>http://{{site.domain}}{{blog.url}}</link>
    <description><![CDATA[{% render blog.copy.body %}]]></description>
    {% with blog.post_list|slice:"10" as latest %}
        {% for post in latest %}{% render post %}{% endfor %}
    {% endwith %}
    {% comment %} <pubDate>Tue, 10 Jun 2003 04:00:00 GMT</pubDate> TODO: figure this shit out.
    {% if blog.copy.language %}<language>{{ blog.copy.language.body }}</language>{% endif %}
    <lastBuildDate>Tue, 10 Jun 2003 09:41:01 GMT</lastBuildDate>
    <docs>http://blogs.law.harvard.edu/tech/rss</docs>
    <generator>Weblog Editor 2.0</generator>
    <managingEditor>editor@example.com</managingEditor>
    <webMaster>webmaster@example.com</webMaster>
    <ttl>5</ttl> {% endcomment %}
  </channel>
</rss>"""


#-------------------------------------------------------------------------------
def sync_blog_swim_data(**kwargs):
    # Create the base group.
    create_groups(RSS_GROUPS)

    #---------------------------------------------------------------------------
    # Create The Resource Types
    create_resource_types(RESOURCE_TYPES)

    #---------------------------------------------------------------------------
    for type_key, path, title in RSS_PAGES:
        resource_type = ResourceType.objects.get(key=type_key)
        page, created = Page.objects.get_or_create(
                resource_type=resource_type,
                path=path,
            )
        if created:
            page.title = title
            page.save()

    #---------------------------------------------------------------------------
    # The following definitions MUST not be run at the module level otherwise
    # they'll cause an IntegrityError because the database won't have been
    # created yet.
    RSS_CONTENT_TYPE = 'application/rss+xml'
    BLOG_PAGE_TYPE = ResourceType.objects.get(key='blog')
    RSS_PAGE_TYPE = ResourceType.objects.get(key='rss_feed')
    RESOURCE_SCO = Resource.swim_content_type()
    POST_SCO = Post.swim_content_type()
    DEFAULT_RESOURCE_TYPE = ResourceType.objects.get(title='default')

    #---------------------------------------------------------------------------
    BLOG_TEMPLATES = (
        #(path, http_content_type, swim_content_type, body, resource_type)
        ('/syndication/rss', RSS_CONTENT_TYPE, RESOURCE_SCO, DEFAULT_RSS_TEMPLATE, RSS_PAGE_TYPE),
        ('/syndication/rss/post', RSS_CONTENT_TYPE, POST_SCO, DEFAULT_RSS_POST_TEMPLATE, RSS_PAGE_TYPE),

        # Install the same template for blogs when the content type is considered to be RSS
        ('/syndication/rss', RSS_CONTENT_TYPE, RESOURCE_SCO, DEFAULT_RSS_TEMPLATE, BLOG_PAGE_TYPE),
        ('/syndication/rss/post', RSS_CONTENT_TYPE, POST_SCO, DEFAULT_RSS_POST_TEMPLATE, BLOG_PAGE_TYPE),
    )

    for path, http_content_type, swim_content_type, body, resource_type in BLOG_TEMPLATES:
        template, created = Template.objects.get_or_create(
            path = path,
            http_content_type = http_content_type,
            swim_content_type = swim_content_type
        )

        if created:
            template.body = body
            template.save()

        ResourceTypeTemplateMapping.objects.get_or_create(
            resource_type=resource_type,
            template=template
        )

signals.initialswimdata.connect(sync_blog_swim_data)
