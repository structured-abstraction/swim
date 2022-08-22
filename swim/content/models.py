import os
import sys
import time
import string
import random
from datetime import datetime
import collections

from django.db import models, IntegrityError
from django.db.models.signals import post_init
from django.forms import ValidationError
from django.conf import settings
from django.utils.http import http_date
from django.template import Template, Context
from django.contrib.contenttypes.models import ContentType as DjangoContentType
from django.contrib.sites.models import Site
from django.template.defaultfilters import slugify
from django.core import files

from swim.core import WithRelated, is_subpath_on_path
from swim.core.content import (
        register_content_object,
        register_atom_type,
        AtomType,
        ReferencedAtomType,
    )
from swim.chronology.models import Period, AnonymousInstant
from swim.core import modelfields, string_to_key
from swim.core.models import (
    ModelBase,
    ModelIsContentType,
    ClassIsContentType,
    HasResourceType,
    HasArrangementType,
    Resource,
    RequestHandlerMapping,
    RequestHandler,
    Function,
    ResourceType,
    ArrangementType,
    EnumType,
    EnumTypeChoice,
    KeyedType,
    ContentSlot,
)
from swim.seo.models import HasSEOAttributes

#-------------------------------------------------------------------------------
class LinkResource(Resource, HasSEOAttributes):
    # TODO: Try out inherting from link in order to maintain our link.
    """Abstract class which maintains their own link.

    attributes:
    ownlink
        Pages maintain their own Link record which links to the Pages path.
    title
        Human readable title of the Page. Normally used in the HTML <title> tag
    """
    title = models.CharField(max_length=200)
    ownlink = models.ForeignKey(
        'content.Link',
        related_name='%(class)s_set',
        editable=False,
        blank=True,
        null=True,
        on_delete=models.CASCADE
    )

    #--------------------------------------------------------------------------
    def save(self, *args, **kwargs):
        if not self.ownlink_id:
            # There isn't a link in the Pages Foreign key, so create a new link
            self.ownlink = Link.objects.create(
                title = self.title,
                url = self.get_absolute_url()
            )
            self.ownlink.save()
        elif not Link.objects.filter(id = self.ownlink_id).count():
            # There is a reference to a foreign key, but the link is missing so create a new one
            # This may leave an orphan link in the system.
            self.ownlink = Link.objects.create(
                title = self.title,
                url = self.get_absolute_url()
            )
            self.ownlink.save()
        else:
            # There is a link and it exists fine, so update the link with current data.
            self.ownlink.title = self.title
            self.ownlink.url = self.get_absolute_url()

        super(LinkResource, self).save(*args, **kwargs)

        self.ownlink.save()

    #--------------------------------------------------------------------------
    def delete(self, **kwargs):
        if self.ownlink:
            self.ownlink.delete()
        super(LinkResource, self).delete(**kwargs)

    class Meta:
        abstract = True


#-------------------------------------------------------------------------------
class Copy(ModelIsContentType):
    """Represents text content
    """
    body = models.TextField(blank=True, null=True)

    class Meta(ModelIsContentType.Meta):
        verbose_name_plural = "Copy"

#-------------------------------------------------------------------------------
class TextInputCopy(ClassIsContentType):
    """
    Represents text content that uses a text input as it's data entry type.
    """

#-------------------------------------------------------------------------------
class TextAreaCopy(ClassIsContentType):
    """
    Represents text content that uses a text area as it's data entry type.
    """

#-------------------------------------------------------------------------------
class TinyMCECopy(ClassIsContentType):
    """
    Represents text content that uses a tinymce as it's data entry type.
    """

#-------------------------------------------------------------------------------
class CKEditorCopy(ClassIsContentType):
    """
    Represents text content that uses a CKEditor as it's data entry type.
    """

#-------------------------------------------------------------------------------
class EditAreaCopy(ClassIsContentType):
    """
    Represents text content that uses a tinymce as it's data entry type.
    """

#-------------------------------------------------------------------------------
class Link(ModelIsContentType):
    """
    """
    title = models.CharField(max_length=200, blank=True, null=True)
    url = models.CharField(max_length=1024)

    def __str__(self):
        return '%s - %s' % (self.url, self.title)

    class Meta:
        ordering = ('url', 'title')

#-------------------------------------------------------------------------------
class Menu(ModelIsContentType):
    """
    """
    title = models.CharField(max_length=200, blank=True, null=True)

    #---------------------------------------------------------------------------
    def __str__(self):
        if self.title:
            return self.title
        else:
            return 'Untitled %s' % self.id


    #---------------------------------------------------------------------------
    def get_links(self):
        links = []
        for menulink in self.menulink_set.all().select_related('link'):
            links.append(menulink.link)
        return links
    links = property(get_links, )

    #---------------------------------------------------------------------------
    def get_menulinks(self):
        links = []
        for menulink in self.menulink_set.all().select_related('link'):
            links.append(menulink)
        return links
    menulinks = property(get_menulinks, )

    #---------------------------------------------------------------------------
    def get_pages(self):
        """
        Gets all of the pages that are associated via a Menu Link.


        This is a frequently accomplished task - and because of this we want to
        make sure it's as efficient as possible.
        """
        links = []
        return Page.objects.filter(
                ownlink__menulink__menu=self
            ).order_by('ownlink__menulink__order').select_related("resource_type")
    pages = property(get_pages, )

#-------------------------------------------------------------------------------
class MenuLink(models.Model):
    """
    """
    menu = models.ForeignKey(Menu, on_delete=models.CASCADE)
    order = models.IntegerField()
    link = models.ForeignKey(Link, on_delete=models.CASCADE)

    #---------------------------------------------------------------------------
    def get_resource(self):
        """
        Gets the page that is associated to this Menu Link.

        This is a frequently accomplished task - and because of this we want to
        make sure it's as efficient as possible.
        """
        pages = Page.objects.filter(ownlink__menulink=self)
        if pages:
            return pages[0]

        pages = Page.objects.filter(path=self.link.url)
        if pages:
            return pages[0]

        # instead of special casing blog here returning a LinkResource would
        # make more sense... if LinkResource weren't abstract of course
        from swim.blog.models import Blog
        blogs = Blog.objects.filter(ownlink__menulink=self)
        if blogs:
            return blogs[0]

        return None
    resource = property(get_resource, )

    class Meta:
        ordering = ('order', )

#-------------------------------------------------------------------------------
class Arrangement(HasArrangementType):
    """Arrangements are groupings of other content types with ordering.
    """

register_content_object('arrangement', Arrangement)

#-------------------------------------------------------------------------------
class CopySlot(ContentSlot, ModelIsContentType):
    body = models.TextField(blank=True, default='')

    copy = models.ForeignKey(
        Copy,
        editable=False,
        related_name="slots",
        on_delete=models.CASCADE,
        null=True,
    )

    # The body on the CopySlot is a cached, non-authoritative copy of the
    # body of the related copy, used simply as a container into the appropriate
    # administration interfaces.
    #
    # Intentially private as its only intended use is in the admin, don't use
    # it from the db-api unless you're certain you know what you're doing.
    _body = models.TextField(blank=True, default='', editable=False)

    """
    #---------------------------------------------------------------------------
    def save(self, *args, **kwargs):
        ""
        Save the copyslot instance into the database.

        Ensure that the copyslot is associated with a copy object.
        ""
        try:
            copy = self.copy
        except Copy.DoesNotExist:
            copy = None
        if not copy:
            self.copy = Copy.objects.create(
                    body=self._body,
                )

        self.copy.body = self._body
        self.copy.save()

        super(CopySlot, self).save(*args, **kwargs)
    """

    #---------------------------------------------------------------------------
    def __str__(self):
        obj_url_func = getattr(self.content_object, 'url', None)
        title = getattr(self.content_object, 'title', '')
        if not obj_url_func:
            url_func = lambda: ""
        else:
            url_func = lambda: " on %s - %s" % (title, obj_url_func())
        return "Copy #%d %s%s" % (self.order, self.key, url_func())

    #---------------------------------------------------------------------------
    class Meta:
        verbose_name_plural = "Copy"
        ordering = ['order',]

register_atom_type('copy', AtomType(CopySlot))

#-------------------------------------------------------------------------------
class MenuSlot(ContentSlot):
    menu = models.ForeignKey(
        Menu,
        related_name='slots',
        on_delete=models.CASCADE
    )

    objects = WithRelated('menu')

    class Meta:
        verbose_name_plural = "Menus"
        ordering = ['order',]

    @classmethod
    def get_select_related(cls):
        return ['menu']

register_atom_type(
        'menu',
        ReferencedAtomType(Menu, MenuSlot)
    )

#-------------------------------------------------------------------------------
class ArrangementSlot(ContentSlot):
    arrangement = models.ForeignKey(
            Arrangement,
            related_name='slots',
            on_delete=models.CASCADE
        )

    objects = WithRelated('arrangement')

    class Meta:
        verbose_name_plural = "Sub-Arrangements"
        ordering = ['order',]

    @classmethod
    def get_select_related(cls):
        return ['arrangement']

register_atom_type(
        'arrangement',
        ReferencedAtomType(Arrangement, ArrangementSlot)
    )

#-------------------------------------------------------------------------------
class DateSlot(ContentSlot, ModelIsContentType):
    value = models.DateField(blank=True, null=True)

    class Meta:
        ordering = ['order',]

register_atom_type(
        'date',
        AtomType(DateSlot)
    )

#-------------------------------------------------------------------------------
class DateTimeSlot(ContentSlot, ModelIsContentType):
    value = models.DateTimeField(blank=True, null=True)

    #---------------------------------------------------------------------------
    def in_past(self):
        if self.value <= datetime.now():
            return True
        return False

    #---------------------------------------------------------------------------
    def in_future(self):
        if self.value >= datetime.now():
            return True
        return False

    class Meta:
        ordering = ['order',]
register_atom_type(
        'datetime',
        AtomType(DateTimeSlot)
    )

#-------------------------------------------------------------------------------
class TimeSlot(ContentSlot, ModelIsContentType):
    value = models.TimeField(blank=True, null=True)

    class Meta:
        ordering = ['order',]
register_atom_type(
        'time',
        AtomType(TimeSlot)
    )

#-------------------------------------------------------------------------------
class InstantSlot(AnonymousInstant, ContentSlot, ModelIsContentType):
    class Meta:
        ordering = ['order',]
register_atom_type(
        'instant',
        AtomType(InstantSlot)
    )

#-------------------------------------------------------------------------------
class PeriodSlot(Period, ContentSlot, ModelIsContentType):

    class Meta:
        ordering = ['order',]
register_atom_type(
        'period',
        AtomType(PeriodSlot)
    )

#-------------------------------------------------------------------------------
class IntegerSlot(ContentSlot, ModelIsContentType):
    value = models.IntegerField(blank=True, null=True)

    class Meta:
        ordering = ['order',]
register_atom_type(
        'integer',
        AtomType(IntegerSlot)
    )

#-------------------------------------------------------------------------------
class EnumSlot(ContentSlot, ModelIsContentType):
    enum_type = models.ForeignKey(
        EnumType,
        editable=False,
        on_delete=models.CASCADE,
    )
    choice = models.ForeignKey(
        EnumTypeChoice,
        on_delete=models.CASCADE
    )

    #--------------------------------------------------------------------------
    def save(self, *args, **kwargs):
        self.enum_type = self.choice.enum_type

        super(EnumSlot, self).save(*args, **kwargs)

    class Meta:
        ordering = ['order',]
register_atom_type(
        'enum',
        AtomType(EnumSlot)
    )

#-------------------------------------------------------------------------------
class MenuTreeNode:
    """
    An object which represents a node in a menu tree.

    This node (along with its children) represents a navigation tree (menu
    tree) for a particular page, its parents and its children.

    attributes:
        children:
            a list of children nodes. Will always be an list, but may
            be empty.
        url:
            the url that this node links to.
        title:
            the title of this node.
        active:
            a boolean indicating whether the url that this node links to
            is part of the current navigation path.
    """
    #---------------------------------------------------------------------------
    def __init__(self, url, title, active=False, children=None):
        self.url = url
        self.title = title
        self.active = active
        if children is None:
            children = []
        self.children = children

#-------------------------------------------------------------------------------
class MenuTreeGenerator:
    """
    An object which can use a key-lookup syntax to generate a MenuTreeNode

    Given a hierarchy of pages with a common menu that represents a conceptual
    menu tree, and a key identifying the particular content schema member that
    contains said menu - this object can generate the appropriate MenuTreeNode
    instance.
    """
    #---------------------------------------------------------------------------
    def __init__(self, page):
        self.page = page

    #---------------------------------------------------------------------------
    def __getitem__(self, key):
        """
        Generates the appropriate tree based on the menus and parent pages.

        First, we'll look up all the parent pages using a single query, then we
        will find out which ones have the appropriate menu (if they don't they
        are excluded).  Once we have a list of ones with the appropriate menus
        we will get all of their menu links, and generate the appropriate tree.


        Note: once we generate the list of paths in order from '/' to the page
        that we are targetting - we will iterate over the paths for most of
        the loops in this algorithm in order to consistently order them.
        """
        parent_paths = []
        path_parts = self.page.path.strip("/").split("/")
        for i in range(0, len(path_parts)):
            parent_paths.append("/" + "/".join(path_parts[:i]))
        parent_pages = Page.objects.filter(path__in=parent_paths)
        page_lookup = {self.page.path: self.page}
        for page in parent_pages:
            page_lookup[page.path] = page

        # Now that we have all of the pages we are to include, let's see if
        # they have a menu associated with them
        menu_lookup = {}
        menu_by_id_lookup = {}
        path_by_menu_id = {}
        target_paths = []
        menu_ids = []
        for path in parent_paths + [self.page.path]:
            page = page_lookup[path]
            try:
                menu = page.menu[key]
                target_paths.append(path)
                menu_lookup[path] = menu
                menu_by_id_lookup[menu.id] = menu
                menu_ids.append(menu.id)
                path_by_menu_id[menu.id] = path
            except KeyError:
                continue

        # Now we have a list of paths that have the appropriate menus in
        # order.
        menu_link_lookup = collections.defaultdict(list)
        menu_link_as = MenuLink.objects.filter(
                menu__id__in=menu_ids
            ).order_by('order').select_related('link')
        for menu_link in MenuLink.objects.filter(menu__id__in=menu_ids).order_by('order'):
            menu = menu_by_id_lookup[menu_link.menu_id]
            menu_link_lookup[path_by_menu_id[menu.id]].append(menu_link.link)

        # Now we'll start at the base level and work our way back up.
        # NOTE: This algorithm does assume that the menu tree implies only one
        #       way to navigate to the current page.  It probably won't cause a
        #       any sort of exception to be thrown if this isn't the case
        #       but rather might just highlight the "First" way to get to this
        #       page.
        #       We should probably test what it does and see if it makese "sense"
        previous_children = []
        current_path = self.page.path
        for path in reversed(target_paths):
            current_children = []
            for link in menu_link_lookup[path]:
                active = False
                children = []

                # If this link is part of the navigation path - add in the last
                # level and mark it as active.
                if is_subpath_on_path(link.url, current_path):
                    active = True
                    children = previous_children
                current_children.append(
                        MenuTreeNode(link.url, link.title, active, children)
                    )

            # Now we have this level done, store it and go back up the tree:
            previous_children = current_children

        # The last step is to use the root itself to create the root tree node
        if not target_paths:
            target_paths = [self.page.path]
        root_path = target_paths[0]
        root = MenuTreeNode(
                root_path,
                page_lookup[root_path].title,
                active=True,
                children=previous_children
            )

        return root

#-------------------------------------------------------------------------------
class Page(LinkResource, ClassIsContentType):
    """A resource with a URL, title and content defined by its content schema.

    :param resource_type:
        The type of this pages which dictates the content available.
    :param path:
        The path that the page will be mounted on. You will be able to access
        the page on a case insensitive manner and will be redirected to the
        case exact path specified in this attribute.
    """
    path = modelfields.Path('path', unique=True)
    key = modelfields.Key(max_length=200, editable=False, unique=True)

    #--------------------------------------------------------------------------
    def get_parent(self):
        """
        A reference to the page who's path is the direct ancestor to this page.

        returns:
            a reference to the parent page.
        """
        base, leaf_atom = self.path.rsplit("/", 1)
        return Page.objects.get(path=base)

    #--------------------------------------------------------------------------
    def has_parent(self):
        """
        Boolean indicating whether this page has a parent or not.

        returns:
            a boolean indicating if this page has a parent.
        """
        base, leaf_atom = self.path.rsplit("/", 1)
        return Page.objects.filter(path=base).count() > 0

    #--------------------------------------------------------------------------
    def get_menu_tree(self):
        """
        An object that will generate a MenuTreeNode for this page's menu tree.

        :rtype:
            a reference to the menu tree for this page.
        """
        return MenuTreeGenerator(self)
    menu_tree = property(get_menu_tree)

    #--------------------------------------------------------------------------
    def url(self):
        if self.path.strip('/') == '':
            return '/'
        else:
            return '/%s' % self.path.strip('/')

    #--------------------------------------------------------------------------
    def __str__(self):
        return "%s (%s)" % (self.path, self.title or "untitled")

    #--------------------------------------------------------------------------
    def save(self, *args, **kwargs):
        self.key = "%s" % self.path.strip('/').replace('/', '_').replace('#', '_')

        super(Page, self).save(*args, **kwargs)

    #--------------------------------------------------------------------------
    def get_request_handler(self):
        obj, _ = RequestHandler.objects.get_or_create(
                title = settings.DEFAULT_PAGE_VIEW,
                function = settings.DEFAULT_PAGE_VIEW,
            )
        return obj

    #--------------------------------------------------------------------------
    def get_request_method(self):
        return "GET"

    class Meta:
        ordering = ('path',)

class PageSlot(ContentSlot):
    page = models.ForeignKey(
        Page,
        related_name='slots',
        on_delete=models.CASCADE,
    )

    objects = WithRelated('page')

    class Meta:
        verbose_name_plural = "Pages"
        ordering = ['order',]

    @classmethod
    def get_select_related(cls):
        return ['page']

    def _get_page_type(self):
        type = self.content_object.get_type()
        try:
            csm = type.get_interface(self.key)
            return PageType.objects.get(
                _swim_content_type__title=csm['swim_content_type']
            )
        except (PageType.DoesNotExist, ContentSchemaMember.DoesNotExist, TypeError):
            return None

    def __str__(self):
        return self.page.title

register_atom_type(
        'page',
        ReferencedAtomType(Page, PageSlot)
    )
register_content_object('page', Page)


#-------------------------------------------------------------------------------
class PageType(KeyedType):
    """
    Define a Page Type.
    """

    resource_type = models.ForeignKey(
        ResourceType,
        on_delete=models.CASCADE,
    )


#-------------------------------------------------------------------------------
class SiteWideContent(HasResourceType):

    key = modelfields.Key(max_length=200, unique=True)

    objects = WithRelated('resource_type')

    #--------------------------------------------------------------------------
    def __str__(self):
        return u"%s" % (self.key,)

    #--------------------------------------------------------------------------
    class Meta:
        ordering = ('key',)
        verbose_name_plural = "Site-wide content"
        verbose_name = "Site-wide content"

#-------------------------------------------------------------------------------
register_content_object('site', SiteWideContent)

