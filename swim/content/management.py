# vim: set fileencoding=utf-8
import os

from django.conf import settings

from swim.core import signals

from swim.core.management import (
    register_swim_code,
    create_groups,
    create_resource_types,
    create_arrangement_types,
)
from swim.content import models
from swim.core.models import (
    RequestHandler,
    ResourceType,
    ResourceTypeSwimContentTypeMapping,
)

from swim.content.models import (
    Page,
    TextInputCopy,
    CopySlot,
    Link,
    Menu,
    MenuLink,
    SiteWideContent,
)
from swim import settings as swim_settings

#-------------------------------------------------------------------------------
def register_page_view(**kwargs):
    """Registers the page view request handler
    """
    page_view_constructor = RequestHandler.objects.get_or_create(
            title = 'swim.content.views.PageView',
            function = 'swim.content.views.PageView',
        )


signals.initialswimdata.connect(register_page_view)

#-------------------------------------------------------------------------------
CONTENT_GROUPS = (
    ('Content Editor', "content", "add_copy",),
    ('Content Editor', "content", "add_link",),
    ('Content Editor', "content", "add_menu",),
    ('Content Editor', "content", "add_menulink",),
    ('Content Editor', "content", "add_page",),
    ('Content Editor', "content", "add_copyslot",),
    ('Content Editor', "content", "add_menuslot",),
    ('Content Editor', "content", "change_copy",),
    ('Content Editor', "content", "change_link",),
    ('Content Editor', "content", "change_menu",),
    ('Content Editor', "content", "change_menulink",),
    ('Content Editor', "content", "change_page",),
    ('Content Editor', "content", "change_copyslot",),
    ('Content Editor', "content", "change_menuslot",),
    ('Content Editor', "content", "delete_copy",),
    ('Content Editor', "content", "delete_link",),
    ('Content Editor', "content", "delete_menu",),
    ('Content Editor', "content", "delete_menulink",),
    ('Content Editor', "content", "delete_page",),
    ('Content Editor', "content", "delete_copyslot",),
    ('Content Editor', "content", "delete_menuslot",),

    ('Content Editor', "media", "add_image",),
    ('Content Editor', "media", "change_image",),
    ('Content Editor', "media", "delete_image",),
    ('Content Editor', "media", "add_file",),
    ('Content Editor', "media", "change_file",),
    ('Content Editor', "media", "delete_file",),
    ('Content Editor', "media", "add_fileslot",),
    ('Content Editor', "media", "change_fileslot",),
    ('Content Editor', "media", "delete_fileslot",),
    ('Content Editor', "media", "add_imageslot",),
    ('Content Editor', "media", "change_imageslot",),
    ('Content Editor', "media", "delete_imageslot",),
)

#-------------------------------------------------------------------------------
CAPTIONED_IMAGE_CONTENT_SCHEMA = (
    )

#-------------------------------------------------------------------------------
DEFAULT_ARRANGEMENT_TYPES = [
        # (key, title, swim_content_type, template_path, template_body)
    ]

#-------------------------------------------------------------------------------
SITE_WIDE_CONTENT_TYPE_CONTENT_SCHEMA = (
        # (order, key, header, cardinality, swim_content_type)
        (1, 'copyright', 'Copyright', 'single', CopySlot.swim_content_type,),
        (2, 'top_level_nav', 'Top Level Nav', 'single', Menu.swim_content_type,),
    )

#-------------------------------------------------------------------------------
STATIC_PAGE_TYPE_CONTENT_SCHEMA = (
        # (order, key, header, cardinality, swim_content_type)
        (1, 'header', 'Page Header Copy', 'single', CopySlot.swim_content_type,),
        (2, 'body', 'Page Body Copy', 'single', CopySlot.swim_content_type,),
        (3, 'footer', 'Page Footer Copy', 'single', CopySlot.swim_content_type,),
        (4, 'submenu', 'Page Sub-Menu', 'single', Menu.swim_content_type,),
        #(3, 'image_list', 'Page Image List', 'single', Menu.swim_content_type,),

    )

#-------------------------------------------------------------------------------
DEFAULT_PAGE_TYPES = (
        # (parent, key, title, swim_content_type, interface)
        ('default', 'simple_page', 'Simple Page', Page.swim_content_type,
            STATIC_PAGE_TYPE_CONTENT_SCHEMA),
        ('default', 'site_wide_content', 'Site-wide content', SiteWideContent.swim_content_type,
            SITE_WIDE_CONTENT_TYPE_CONTENT_SCHEMA),
    )


#-------------------------------------------------------------------------------
DEFAULT_SWIM_PAGES = (
    #(path, title)
    ('/', 'Home Page', 'simple_page',),
    ('/contact-us', 'Contact Us', 'simple_page',),
    ('/about-swim', 'About SWIM', 'simple_page',),
)
#-------------------------------------------------------------------------------
DEFAULT_COPY = (
    #(copy_key, copy)
    ("""All Content © 2008 <b>Structured Abstraction</b>"""),
)

#-------------------------------------------------------------------------------
DEFAULT_PAGE_COPY = (
    #(page_path, page_key, copy_key, copy)
    ('/', 'body', """"""),
    ('/', 'header', """The site is built using our
        <a href="/about-swim">SWIM</a> - our Simple Web Information Manager."""),
    ('/', 'footer',  """"""),
    ('/about-swim', 'header', """SWIM - Simple Website Information Manager."""),
    ('/about-swim', 'footer', """Clients own their content - we give them the tools to manage it."""),
    ('/about-swim', 'body', """"""),
)
#-------------------------------------------------------------------------------
DEFAULT_MENUS = (
    #(menu_key, order, link_title, link_url,)
    (1, 'Home Page', '/'),
    (2, 'About SWIM', '/about-swim'),
    (3, 'Contact Us', '/contact-us'),
)

#-------------------------------------------------------------------------------
def register_default_content(**kwargs):
    """Registers a few basic pages.
    """

    # Create the appropriate group
    create_groups(CONTENT_GROUPS)

    # Create our types
    create_resource_types(DEFAULT_PAGE_TYPES)
    create_arrangement_types(DEFAULT_ARRANGEMENT_TYPES)

    #---------------------------------------------------------------------------
    for path, title, resource_type_key in DEFAULT_SWIM_PAGES:
        page, created = Page.objects.get_or_create(
            path = path,
        )
        if created:
            page.resource_type = ResourceType.objects.get(key=resource_type_key)
            page.title = title
            page.save()

    #---------------------------------------------------------------------------
    for page_path, page_key, body in DEFAULT_PAGE_COPY:
        page = Page.objects.get(path=page_path)
        copy = CopySlot.objects.create(
            order = 1,
            key = page_key,
            content_object = page,
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



signals.initialswimdata.connect(register_default_content)

