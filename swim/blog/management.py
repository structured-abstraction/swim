from swim.core import signals

from swim.core.management import create_groups, create_resource_types
from swim.blog import models
from swim.blog.models import Post, Blog
from swim.design.models import (
    Template,
    ResourceTypeTemplateMapping,
)
from swim.core.models import (
    Resource,
    ResourceType,
    ResourceTypeSwimContentTypeMapping,
    ResourceTypeMiddleware,
    ResourceTypeMiddlewareMapping,
)
from swim.content.models import (
    Page,
    Menu,
    Link,
    MenuLink,
    CopySlot,
)




#-------------------------------------------------------------------------------
BLOG_GROUPS = (
    # (group_name, app_label, codename)
    ("Blog Editor", "blog", "add_post",),
    ("Blog Editor", "blog", "change_post",),
    ("Blog Editor", "blog", "delete_post",),
    ("Blog Editor", "blog", "add_blog",),
    ("Blog Editor", "blog", "change_blog",),
    ("Blog Editor", "blog", "delete_blog",),
    ("Blog Editor", "blog", "add_tag",),
    ("Blog Editor", "blog", "change_tag",),
    ("Blog Editor", "blog", "delete_tag",),
)

#-------------------------------------------------------------------------------
BLOG_POST_TYPE_RESOURCE_INTERFACE = (
        # (order, key, header, cardinality, swim_content_type)
        (1, 'body', 'Post Body Copy', 'single', CopySlot.swim_content_type,),
    )

#-------------------------------------------------------------------------------
RESOURCE_TYPES = (
    # ( parent, key, title, swim_content_type, interface )
    ('default', 'blog', 'Blog Page', Blog.swim_content_type, None),
    ('blog', 'blog_year', 'Blog Year Page', None, None),
    ('blog', 'blog_month', 'Blog Month Page', None, None),
    ('blog', 'blog_day', 'Blog Day Page', None, None),
    ('blog', 'tag', 'Blog Tag Page', None, None),
    ('default', 'post', 'Blog Post', Post.swim_content_type,
        BLOG_POST_TYPE_RESOURCE_INTERFACE),
)

#-------------------------------------------------------------------------------
BLOG_PAGES = (
        # ( type_key, path, title )
        ('blog', '/news', 'News'),
    )

#-------------------------------------------------------------------------------
SWIM_MIDDLEWARE_PATHS = (
    # (function_name, resource_type)
    ('swim.blog.swimmiddleware.blog_context', 'blog'),
    ('swim.blog.swimmiddleware.all_blog_posts', 'default'),
)

#-------------------------------------------------------------------------------
DEFAULT_MENUS = (
    #(menu_key, order, link_title, link_url,)
    (4, 'News', '/news'),
)

#-------------------------------------------------------------------------------
DEFAULT_PAGE_COPY = (
    #(page_path, page_key, copy_key, copy)
    ('/news', 'header', """News"""),
    ('/news', 'body',
        """Check back often for our updated news."""),
)

#-------------------------------------------------------------------------------
POST_TEMPLATE_BODY = """
<h5>{{ target.title }}</h5>
<div class='post post-{{target.id}}'>{{ target.copy.body }}</div>
<div>{{target.gallery.gallery}}</div>
"""

#-------------------------------------------------------------------------------
DEFAULT_BLOG_TEMPLATE = """
{% extends '/system/default/base' %}
{% block content %}
  {{ block.super }}

    {% if resource.post_list %}
        <h3>Latest Posts!</h3>
        {{ resource.post_list|safe }}
    {% endif %}
{% endblock %}
"""


#-------------------------------------------------------------------------------
def sync_blog_swim_data(**kwargs):
    # Create the base group.
    create_groups(BLOG_GROUPS)

    #---------------------------------------------------------------------------
    # Create The Resource Types
    create_resource_types(RESOURCE_TYPES)

    #---------------------------------------------------------------------------
    for type_key, path, title in BLOG_PAGES:
        resource_type = ResourceType.objects.get(key = type_key)
        blog, created = Blog.objects.get_or_create(
                resource_type=resource_type,
                path=path,
            )
        if created:
            blog.title = title
            blog.save()

    #---------------------------------------------------------------------------
    for page_path, page_key, body in DEFAULT_PAGE_COPY:
        blog = Blog.objects.get(path=page_path)
        CopySlot.objects.create(
            order = 1,
            content_object = blog,
            key = page_key,
            body = body,
        )

    #---------------------------------------------------------------------------
    for order, title, url in DEFAULT_MENUS:
        menu = Menu.objects.create(title=title)
        link, created = Link.objects.get_or_create(url=url)

        if created:
            link.title = title
            link.save()
        try:
            menu_link = MenuLink.objects.get(menu=menu, link=link)
        except MenuLink.DoesNotExist:
            menu_link = MenuLink.objects.create(menu=menu, link=link, order=order)



    #---------------------------------------------------------------------------
    # Create The Middleware that will run on each resource type
    for function_name, type_key in SWIM_MIDDLEWARE_PATHS:
        resource_type = ResourceType.objects.get(
                key = type_key
            )

        # Get a reference to the registration handler
        middleware = ResourceTypeMiddleware.objects.get(
                function = function_name,
            )
        # Create the ResourceTypeMiddlewareMapping default for confirmation
        try:
            resource_type_middleware_mapping = ResourceTypeMiddlewareMapping.objects.get(
                    resource_type=resource_type,
                    function=middleware
                )
        except ResourceTypeMiddlewareMapping.DoesNotExist:
            resource_type_middleware_mapping = ResourceTypeMiddlewareMapping.objects.create(
                    resource_type=resource_type,
                    function=middleware,
                )


    #---------------------------------------------------------------------------
    # The following definitions MUST not be run at the module level otherwise
    # they'll cause an IntegrityError because the database won't have been
    # created yet.
    HTTP_CONTENT_TYPE = 'text/html; charset=utf-8'
    BLOG_PAGE_TYPE = ResourceType.objects.get(key = 'blog')
    RESOURCE_SCO = Resource.swim_content_type()
    POST_SCO = Post.swim_content_type()
    DEFAULT_RESOURCE_TYPE = ResourceType.objects.get(title='default')

    #---------------------------------------------------------------------------
    BLOG_TEMPLATES = (
        #(path, http_content_type, swim_content_type, body, resource_type)
        ('/blog/default/post', HTTP_CONTENT_TYPE, POST_SCO, POST_TEMPLATE_BODY, DEFAULT_RESOURCE_TYPE),
        ('/blog/default/base', HTTP_CONTENT_TYPE, RESOURCE_SCO, DEFAULT_BLOG_TEMPLATE, BLOG_PAGE_TYPE),
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
