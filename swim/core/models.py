import time
import string

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType as DjangoContentType
from django.contrib.sites.managers import CurrentSiteManager
from django.contrib.sites.models import Site
from django.db import models, IntegrityError
from django.db.models.signals import pre_delete, post_save
from django.utils.http import http_date

import swim
from swim.core import modelfields, string_to_key, WithRelated

#-------------------------------------------------------------------------------
class ModelBase(models.Model):
    """Base model for all SWIM models

    Every model has a creation and modified date so that we can provide
    correct modified information from webserver requests

    attributes:
    creationdate
        The date and time that the instance was created.
    modifieddate
        The date and time that an attribute on the instance was changed.
    """
    creationdate = models.DateTimeField(auto_now_add=True)
    modifieddate = models.DateTimeField(auto_now=True)

    # Waiting on - http://code.djangoproject.com/ticket/9638
    #sites = models.ManyToManyField(Site, related_name='%(app_label)s_%(class)s_site_set')
    #objects = models.Manager()
    #on_site = CurrentSiteManager()
#
    #def save(self, *args, **kwargs):
        #"""Will ensure that this object is associated with the correct site.
        #"""
        ## Ensure we have a primary key
        #super(ModelBase, self).save(*args, **kwargs)
        #if not self.sites:
            #current_site = Site.objects.get_current()
            #self.sites.add(current_site)
            #super(ModelBase, self).save()

    def http_last_modified(self):
        """A re-usable method to pin to each class with a modifieddate
        """
        return http_date(time.mktime(self.modifieddate.timetuple()))

    class Meta:
        abstract = True

#-------------------------------------------------------------------------------
class ContentType(ModelBase):
    """
    Lists of all of the ContentTypes that are available in this SWIM instance.

    Contains an entry for every django model within SWIM that inherits from
    ModelIsContentType. Also contains an entry for every python class that
    inherits from ClassIsContentType. Finally, also contains an entry
    for every instance of a model that inherits from
    ModelInstancesAreContentTypes, such as ContentSchema instances.
    """
    title = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return "%s" % self.title

    __repr__ = __str__

    class Meta:
        ordering = ("title",)

CONTENT_TYPE_CACHE = {}

#-------------------------------------------------------------------------------
class ClassIsContentType:
    """
    Designates that each instance of the given class is the same ContentType.
    """

    def swim_content_type(cls):
        """
        Returns the ContentType object associated to a model that extends this class
        """
        global CONTENT_TYPE_CACHE
        cached_content_object = CONTENT_TYPE_CACHE.get(cls, None)
        if cached_content_object:
            return cached_content_object

        title = "%s.%s" % (cls.__module__.rsplit('.', 1)[0], cls.__name__)

        try:
            cot, _ = ContentType.objects.get_or_create(
                title = title
            )
        except ContentType.DoesNotExist:
            return None
        CONTENT_TYPE_CACHE[cls] = cot
        return cot
    swim_content_type = classmethod(swim_content_type)

#-------------------------------------------------------------------------------
class ModelIsContentType(ModelBase, ClassIsContentType):
    """
    Registers that each instance of the given model is the same ContentType.
    """

    class Meta:
        abstract = True

#-------------------------------------------------------------------------------
class ModelInstancesAreContentTypes(ModelBase):
    """
    Designates that each instance of the given model defines a new ContentType.
    """

    # TODO: this model name may be ambiguous. Something to do with classes
    # being first class objects, so it could be argued that a class that inherits
    # from Model is an instance of model - but this does not refer to the
    # class as an instance. We actually mean the instances of the Python Class
    # that inherits from django.db.Model - IE the python objects that represent
    # a record in a table.

    # Make this a private attribute so that we can expose a method of the
    # same name as is exposed on the python models:
    # swim_content_type()
    # this allows us to use objects of each type indentically
    _swim_content_type = models.ForeignKey(
        ContentType,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )

    #--------------------------------------------------------------------------
    def _content_type_name(self):
        raise NotImplementedError("Subclasses MUST implement this method.")

    #--------------------------------------------------------------------------
    def save(self, *args, **kwargs):
        # for the purposes of the following code, ensure that we always
        # have a valid _swim_content_type instance.
        cls = self.__class__
        title = "%s.%s.%s" % (
                cls.__module__.rsplit('.', 1)[0],
                cls.__name__,
                self._content_type_name()
            )

        if not self._swim_content_type:
            self._swim_content_type, _ = ContentType.objects.get_or_create(title=title)


        self._swim_content_type.title = title
        self._swim_content_type.save()

        super(ModelInstancesAreContentTypes, self).save(*args, **kwargs)

    #--------------------------------------------------------------------------
    def swim_content_type(self):
        """
        Returns the ContentType object associated to this instance COT.
        """

        request = swim.current_request()
        if request and not hasattr(request, 'resource_type_swim_content_types'):
            request.resource_type_swim_content_types = {}

        if request:
            request_rtcot = request.resource_type_swim_content_types
        else:
            request_rtcot = {}

        lookup_key = '{}-{}'.format(
            type(self).__name__,
            self.id
        )

        cot = request_rtcot.get(lookup_key, None)
        if cot: return cot

        cot = self._swim_content_type
        request_rtcot[lookup_key] = cot
        return cot

    #--------------------------------------------------------------------------
    class Meta:
        abstract = True

#-------------------------------------------------------------------------------
class KeyedModel(ModelIsContentType):
    """
    Content in SWIM is keyed so templates can refer to individual objects.
    """

    key = modelfields.Key(
        max_length = 128,
        unique = True,
        blank = True,
        null = True
    )

    def __str__(self):
        if self.key:
            return '%s' % self.key
        else:
            return 'untitled-%s' % self.id

    def save(self, *args, **kwargs):
        """Will populate the key field from the id field if not specified
        """

        # Save once so that we have an id
        super(KeyedModel, self).save(*args, **kwargs)

        # If we don't have a key force ourselves to have one.
        if not self.key:
            potential_key = "%d" % (self.id,)
            saved = False
            count = 0
            self.key = potential_key
            while not saved:
                try:
                    super(KeyedModel, self).save(force_update=True)
                    saved = True
                except IntegrityError:
                    self.key = "%s-%s" % (potential_key, count)
                count += 1


    class Meta:
        abstract = True

        # Specific permission that hides the key from the end user.
        permissions = (
            ("can_edit_key", "Can Edit Key"),
        )


#-------------------------------------------------------------------------------
class Function(ModelBase):
    """References a python function.
    """

    function = models.CharField(max_length=100, unique=True, default="swim.")
    title = models.CharField(max_length=100)

    def invoke(self, *args, **kwargs):
        """
        Invoke the function represented by this row in the database.
        """
        # TODO: This class lacks tests!
        # Try to import the function specified by arbitrary code.
        (module_name, function_name) = self.function.rsplit('.', 1)
        module = __import__(module_name, globals(), locals(), [str(function_name)])
        try:
            arbitrary_code_function = module.__dict__[function_name]
        except KeyError:
            raise ImportError("Could not import %s from %s" % (function_name, module_name))

        # run the function and return anything that is retured by it
        return arbitrary_code_function(*args, **kwargs)

    def callable(self):
        return self.invoke

    def __str__(self):
        return self.title

    class Meta:
        abstract = True

#-------------------------------------------------------------------------------
class RequestHandler(Function):
    """
    A registration of a function that can handle requests.
    """

#-------------------------------------------------------------------------------
class RequestHandlerMapping(ModelBase):
    """
    A list of the available request handlers.
    """

    #---------------------------------------------------------------------------
    # Relate to the instance that created us, so that we can ensure only one
    # RequestHandlerMapping exists for every resource.
    django_content_type = models.ForeignKey(
        DjangoContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('django_content_type', 'object_id')

    path = modelfields.Path()
    method = models.CharField(max_length=10, default="GET",
        choices = (
            ("GET", "GET",),
            ("POST", "POST",),
            ("PUT", "PUT",),
            ("DELETE", "DELETE",),
            ("HEAD", "HEAD",),
        )
    )
    constructor = models.ForeignKey(RequestHandler, on_delete=models.CASCADE)

    #--------------------------------------------------------------------------
    def save(self, *args, **kwargs):
        self.method = self.method.upper()
        super(RequestHandlerMapping, self).save(*args, **kwargs)

    #--------------------------------------------------------------------------
    def __str__(self):
        return "%s %s %s" % (self.method, self.path, self.constructor.title)

    #--------------------------------------------------------------------------
    class Meta:
        unique_together = (("path", "method", ),)


#-------------------------------------------------------------------------------
class ReservedPath(ModelBase):
    """
    Represents a reserved path in the system - used for validation in the admin.

    This reservation of path namespace doesn't indicate that no further request
    handlers can be created in this space, it just indicates that the end user
    may not choose one of these paths for a new resource from the administration
    interface.
    """

    #---------------------------------------------------------------------------
    # Relate to the instance that created us, so that we can ensure only one
    # ReservedPath instance exists for every resource.
    django_content_type = models.ForeignKey(
        DjangoContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('django_content_type', 'object_id')


    path = modelfields.Path(unique=True)

    reservation_type_choices = (
            ('single', 'single',),
            ('tree', 'tree',),
        )
    reservation_type = models.CharField(
            max_length = 10,
            default="single",
            choices = reservation_type_choices
        )

    def __str__(self):
        return self.path


#-------------------------------------------------------------------------------
class ContentSchema(ModelBase):
    """
    Content Schema defines a particular pattern of content.
    """
    title = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ('title',)

#-------------------------------------------------------------------------------
class ContentSchemaMember(ModelBase):
    """
    Represents a single member within a content schema.
    """
    content_schema = models.ForeignKey(
        ContentSchema, related_name="members", on_delete=models.CASCADE)

    order = models.IntegerField()
    key = modelfields.Key(max_length=100, unique=False)
    title = models.CharField(max_length=100)
    cardinality = models.CharField(max_length=100,
            choices = (
                ('single', 'single'),
                ('list', 'list'),
            )
        )
    swim_content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE)

    objects = WithRelated(('content_schema', 'swim_content_type'))

    class Meta:
        unique_together = ('content_schema', 'key',)
        ordering = ('order',)


#-------------------------------------------------------------------------------
def resource_type_default():
    try:
        return ResourceType.objects.get(key='default').pk
    except ResourceType.DoesNotExist:
        return None

#-------------------------------------------------------------------------------
class EntityType(ModelInstancesAreContentTypes):
    """
    EntityType models abstract the common elements of ResourceType and ArrangementType.

    attributes:
    key
        The unique key of the type.
    title
        The human readable name of the type. Ex: contact, default, search.
    """
    key = modelfields.Key(max_length=200, unique=True)
    title = models.CharField(max_length=100, unique=True)

    content_schema = models.ForeignKey(
        ContentSchema,
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )

    content_schema_cache = models.JSONField(blank=True, null=True)

    #--------------------------------------------------------------------------
    def _content_type_name(self):
        return self.key


    #--------------------------------------------------------------------------
    def save(self, *args, **kwargs):
        if not self.key:
            self.key = string_to_key(self.title)
            self.key = self.key.lower()

        super(EntityType, self).save(*args, **kwargs)

    #--------------------------------------------------------------------------
    def __str__(self):
        return self.title

    #--------------------------------------------------------------------------
    def get_interface(self, key):
        """
        Return a cached version of the related interface element.
        """

        # Use the cached one if it's available.
        if self.content_schema_cache:
            return self.content_schema_cache['members_key_lookup'].get(key, None)

        # otherwise, try the database.
        cache_object = swim.current_request()
        if not cache_object:
            cache_object = self

        if not hasattr(cache_object, 'resource_type_interfaces'):
            cache_object.resource_type_interfaces = {}
        request_rti = cache_object.resource_type_interfaces
        if self.id not in request_rti:
            interfaces = {}
            for interface in ContentSchemaMember.objects.filter(
                        content_schema=self.content_schema,
                    ):
                interfaces[interface.key] = interface
            request_rti[self.id] = interfaces
        return content_schema_member_to_dict(request_rti[self.id][key])


#-------------------------------------------------------------------------------
def content_schema_member_to_dict(member):
    return {
            'order': member.order,
            'key': member.key,
            'title': member.title,
            'cardinality': member.cardinality,
            'swim_content_type': member.swim_content_type.title,
        }

#-------------------------------------------------------------------------------
def content_schema_to_dict(content_schema):
    """
    Produce a dict from a content schema object.

    Note: the 0002_add_in_cached_content_schema_fields migration depends on this.
    Due to the way that migrations work, this algorithm MUST be stable for the
    migration.  Hence, if you decide to update/change this algorithm in any way,
    we should move a duplicate of this exact version into that migration.

    As of now, I'm not duplicating it.
    """
    schema_cache = {
            'title': content_schema.title,
            'members_list': [],
            'members_key_lookup': {},
        }
    for member in content_schema.members.all() \
            .order_by('order').select_related('swim_content_type'):
        member_dict = content_schema_member_to_dict(member)
        schema_cache['members_list'].append(member_dict)
        schema_cache['members_key_lookup'][member_dict['key']] = member_dict
    return schema_cache


#-------------------------------------------------------------------------------
def update_content_schema_cache(sender, instance, **kwargs):

    # First - figure out if we have a content schema we should be
    # caching.
    content_schema = None
    if isinstance(instance, EntityType):
        content_schema = instance.content_schema
    elif isinstance(instance, ContentSchema):
        content_schema = instance
    elif isinstance(instance, ContentSchemaMember):
        content_schema = instance.content_schema

    # If not, then don't bother caching it.
    if not content_schema:
        return

    # otherwise, git'er'done!
    entity_type_ids = [et.id for et in content_schema.entitytype_set.all()]

    schema_cache = content_schema_to_dict(content_schema)

    EntityType.objects.filter(id__in=entity_type_ids).update(
            content_schema_cache=schema_cache
        )

post_save.connect(update_content_schema_cache)

#-------------------------------------------------------------------------------
class ArrangementType(EntityType):
    """
    Arrangement types encapsulate the description of an arrangement.
    """

    #inline_display_template = models.ForeignKey(
            #'design.Template',
            #help_text="""
            #The display for each arrangement when it appears in an inline form:<br/>
            #The template has access only to the arrangement instance via the context
            #variable `arrangement`
            #""",
        #)

#-------------------------------------------------------------------------------
class ArrangementTypeMapping(ModelBase):
    """
    Designates a resource type as being suitable for the content administrator.
    """
    arrangement_type = models.ForeignKey(
        ArrangementType,
        related_name='adminable_set', blank=True, null=True,
        on_delete=models.CASCADE
    )
    swim_content_type = models.ForeignKey(
        ContentType,
        related_name="arrangement_type_set",
        on_delete=models.CASCADE
    )

    objects = WithRelated(('arrangement_type', 'swim_content_type'))


#-------------------------------------------------------------------------------
class HasArrangementType(ModelIsContentType):
    """A mixin that allows this type to have a resource type."""

    arrangement_type = models.ForeignKey(
        ArrangementType,
        related_name='%(class)s_set',
        blank=True,
        null=True,
        on_delete=models.CASCADE
    )

    type_field_name = 'arrangement_type'

    #---------------------------------------------------------------------------
    def get_type(self):
        return self.arrangement_type

    #---------------------------------------------------------------------------
    def get_interface(self, key):
        """Utility function that allows for cached retrieval of interfaces."""
        # The fact that this uses a request object is a bit wierd.
        # TODO: move this somewhere else.
        cache_object = swim.current_request()
        if not cache_object:
            cache_object = self

        types = getattr(cache_object, 'arrangement_types', {})
        cache_object.arrangement_types = types

        at = types.get(self.arrangement_type_id, None)
        if not at: at = self.arrangement_type
        types[at.id] = at
        return at.get_interface(key)

    class Meta:
        abstract = True


#-------------------------------------------------------------------------------
class ResourceType(EntityType):
    """Every request handler is expected to return a resource

    attributes:
    parent
        Creates a hierarchy of ResourceTypes which inherit their mappings.
    """

    parent = models.ForeignKey(
        'ResourceType',
        blank=True,
        null=True,
        default=resource_type_default,
        on_delete=models.CASCADE
    )


    #--------------------------------------------------------------------------
    def get_middleware(self):
        """Return middleware for this resource type.

        Include parent middleware.
        """
        my_middleware = list(ResourceTypeMiddlewareMapping.objects.filter(
            resource_type = self,
        ))
        parent_middleware = []
        if self.parent:
            parent_middleware = self.parent.get_middleware()

        return my_middleware + parent_middleware

    #--------------------------------------------------------------------------
    def get_response_processors(self):
        """Return response processors for this resource type.

        Include parent response processors.
        """
        my_response_processors = list(ResourceTypeResponseProcessorMapping.objects.filter(
            resource_type = self,
        ))
        parent_response_processors = []
        if self.parent:
            parent_response_processors = self.parent.get_response_processors()

        return my_response_processors + parent_response_processors

    #--------------------------------------------------------------------------
    class Meta:
        ordering = ['title']

#-------------------------------------------------------------------------------
class DefaultResourceTypeMapping(ModelBase):
    """
    Maps django content types to their default Resource Type for resource models.

    There are situations in SWIM where we create resources on behalf of
    the administrator.  IE, no numan has chosen a resource type for the resource.
    In this case, the default resource type will be used as is defined by this
    model.
    """

    resource_model = models.OneToOneField(
        DjangoContentType,
        help_text="""
        If you delete the default mapping for any particular resource model,
        then swim will not be able to appropriately creates resources
        of this type.  It will cause a database lookup error whenever it
        attempts to look up the default.
        """,
        on_delete=models.CASCADE,
    )
    resource_type = models.ForeignKey(ResourceType, on_delete=models.CASCADE)

#-------------------------------------------------------------------------------
class ResourceTypeSwimContentTypeMapping(ModelBase):
    """
    Designates a resource type as being suitable for the content administrator.
    """
    resource_type = models.ForeignKey(
        ResourceType,
        related_name='adminable_set',
        blank=True,
        null=True,
        on_delete=models.CASCADE
    )
    swim_content_type = models.ForeignKey(
        ContentType,
        related_name="resource_type_set",
        on_delete=models.CASCADE,
        )

    objects = WithRelated(('resource_type', 'swim_content_type'))

#-------------------------------------------------------------------------------
class ResourceTypeResponseProcessor(Function):
    """Python Code that runs just before the response is returned.

    The code stored in this model has access to the following variables
    within it's scope.
    context - The context that the view will render the matching template with
    request - The request object for the HTTPRequest
    resource - The SWIM resource object that was matched for the request
    template - The SWIM template object that was matched for the request
    response - The current response object that is being returned.
    The return value is ignored.
    """

#-------------------------------------------------------------------------------
class ResourceTypeResponseProcessorMapping(ModelBase):
    """A mapping of Response Processors to the view within which it will be run.
    """

    resource_type = models.ForeignKey(
        ResourceType, default=resource_type_default, on_delete=models.CASCADE)
    function = models.ForeignKey(
        ResourceTypeResponseProcessor, on_delete=models.CASCADE)

    objects = WithRelated(('resource_type', 'function'))

    class Meta:
        unique_together = (("resource_type", "function", ),)
        verbose_name = "ResourceType ResponseProcessor Mapping"
        verbose_name_plural = "ResourceType ResponseProcessor Mappings"


#-------------------------------------------------------------------------------
class ResourceTypeMiddleware(Function):
    """Python Code that runs within the views.

    The code stored in this model has access to the following variables
    within it's scope.
    context - The context that the view will render the matching template with
    request - The request object for the HTTPRequest
    resource - The SWIM resource object that was matched for the request
    template - The SWIM template object that was matched for the request
    The return value is ignored.
    """

#-------------------------------------------------------------------------------
class ResourceTypeMiddlewareMapping(ModelBase):
    """A mapping of Python Code to the view within which it will be run.
    """

    resource_type = models.ForeignKey(
        ResourceType, default=resource_type_default, on_delete=models.CASCADE)
    function = models.ForeignKey(
        ResourceTypeMiddleware, on_delete=models.CASCADE)

    objects = WithRelated(('resource_type', 'function'))

    class Meta:
        unique_together = (("resource_type", "function", ),)


#-------------------------------------------------------------------------------
class HasResourceType(ModelIsContentType):
    """A mixin that allows this type to have a resource type.
    """

    resource_type = models.ForeignKey(
        ResourceType,
        related_name='%(class)s_set',
        blank=True,
        null=True,
        on_delete=models.CASCADE
    )

    type_field_name = 'resource_type'

    #---------------------------------------------------------------------------
    def get_type(self):
        return self.resource_type

    #---------------------------------------------------------------------------
    def get_interface(self, key):
        """
        Utility function that allows for cached retrieval of interfaces.

        """
        # The fact that this uses a request object is a bit wierd.
        # TODO: move this somewhere else.
        cache_object = swim.current_request()
        if not cache_object:
            cache_object = self

        types = getattr(cache_object, 'types', {})

        rt = types.get(self.resource_type_id, None)
        if not rt:
            rt = self.resource_type
            types[rt.id] = rt
        return rt.get_interface(key)

    #---------------------------------------------------------------------------
    def get_default_type(self):
        """Should return the ResourceType which is the default.

        return
            an instance of ResourceType
        """
        # TODO: what should this do if it can't find one?
        default = DefaultResourceTypeMapping.objects.select_related(
                "resource_type"
            ).get(
                resource_model=DjangoContentType.objects.get_for_model(self)
            )
        return default.resource_type

    #--------------------------------------------------------------------------
    def save(self, *args, **kwargs):
        if not self.resource_type:
            self.resource_type = self.get_default_type()
        super(HasResourceType, self).save(*args, **kwargs)

    class Meta:
        abstract = True

#-------------------------------------------------------------------------------
class HasRequestHandler(models.Model):
    """
    Instances manage at least a single request handler and path reservation.
    """
    request_handler_mappings = GenericRelation(
            RequestHandlerMapping,
            object_id_field="object_id",
            content_type_field="django_content_type"
        )
    reserved_paths = GenericRelation(
            ReservedPath,
            object_id_field="object_id",
            content_type_field="django_content_type"
        )

    #--------------------------------------------------------------------------
    def url(self):
        raise NotImplementedError("Subclasses MUST implement this method")

    #--------------------------------------------------------------------------
    def get_absolute_url(self):
        return self.url()

    #--------------------------------------------------------------------------
    def get_request_handler(self):
        """Should return the view that the request to this model goes to

        return
            Some callback function that can return a HttpResponse
        """
        raise NotImplementedError("Subclasses MUST implement this method")

    #---------------------------------------------------------------------------
    def get_request_method(self):
        """Should return the HTTP method the request handler deals with

        return
            string containing the HTTP method acceptible by the request handler.
            ex: "GET", "POST", "DELETE"
        """
        raise NotImplementedError("Subclasses MUST implement this method")

    #---------------------------------------------------------------------------
    def get_path_reservation_type(self):
        """Should return the type of path reservation employed by this resource.

        Resources may reserve entire trees of paths by overriding and returning
        'tree' from this method. If they do this, the entire tree of paths
        rooted at self.path is reserved.  The default method returns 'single'
        which indicates that this resource is only reserving its exact path.

        This reservation of path namespace doesn't indicate that no further
        request handlers can be created in this space, it just indicates that
        the end user may not choose one of these paths for a new resource
        from the administration interface.

        return
            string containing the the reservation type
            ex: "single", "tree"
        """
        return "single"

    #---------------------------------------------------------------------------
    class Meta:
        abstract = True

#-------------------------------------------------------------------------------
def update_request_handlers(sender, instance, **kwargs):
    if not isinstance(instance, HasRequestHandler):
        return
    path = "/%s" % (instance.url().strip("/"),)

    if instance.request_handler_mappings.count() == 0:
        request_handler = RequestHandlerMapping.objects.create(
                content_object=instance,
                path=path,
                method=instance.get_request_method(),
                constructor=instance.get_request_handler()
            )
    else:
        request_handler = instance.request_handler_mappings.all()[0]

    # We need to ensure that if our path changes that we
    # keep our request handlers updated.
    request_handler.path = path
    request_handler.save()

post_save.connect(update_request_handlers)

#-------------------------------------------------------------------------------
def update_path_reservations(sender, instance, **kwargs):
    if not isinstance(instance, HasRequestHandler):
        return
    path = "/%s" % (instance.url().strip("/"),)
    if instance.reserved_paths.count() == 0:
        reserved_path = ReservedPath(
                path=path,
                content_object=instance,
                reservation_type=instance.get_path_reservation_type()
            )
    else:
        reserved_path = instance.reserved_paths.all()[0]

    # We need to ensure that if our path changes that we
    # keep our reservations updated.
    reserved_path.path = path
    reserved_path.save()
post_save.connect(update_path_reservations)

#-------------------------------------------------------------------------------
def delete_request_handlers(sender, instance, **kwargs):
    if not isinstance(instance, HasRequestHandler):
        return
    instance.request_handler_mappings.all().delete()
pre_delete.connect(delete_request_handlers)

#-------------------------------------------------------------------------------
def delete_path_reservations(sender, instance, **kwargs):
    if not isinstance(instance, HasRequestHandler):
        return
    # Delete all of my reserved paths!
    instance.reserved_paths.all().delete()
pre_delete.connect(delete_path_reservations)


#-------------------------------------------------------------------------------
class Resource(HasResourceType, HasRequestHandler):
    """Designates that models inheriting from this base will have a RequestHandler mapped to it.
    """

    objects = WithRelated('resource_type')

    class Meta:
        abstract = True

#-------------------------------------------------------------------------------
class KeyedType(ModelInstancesAreContentTypes):
    """
    Instances of this model are content types where their type name is their key.

    attributes:
    key
        The unique key of the type.
    title
        The human readable name of the type. Ex: contact, default, search.
    """
    key = modelfields.Key(max_length=200, unique=True)
    title = models.CharField(max_length=100, unique=True)

    #--------------------------------------------------------------------------
    def _content_type_name(self):
        return self.key

    #--------------------------------------------------------------------------
    def save(self, *args, **kwargs):
        if not self.key:
            self.key = string_to_key(self.title)
            self.key = self.key.lower()

        super(KeyedType, self).save(*args, **kwargs)

    #--------------------------------------------------------------------------
    def __str__(self):
        return self.title

#-------------------------------------------------------------------------------
class EnumType(KeyedType):
    """
    Defines a list of mutually exclusive values for use as Content Atom Types.

    """

#-------------------------------------------------------------------------------
class EnumTypeChoice(ModelBase):
    """
    Defines a single choice within an EnumType.

    attributes:
    enum_type
    order
        The order of this choice within the choices
    value
        The value that is to be displayed and stored for this choice.
    """
    enum_type = models.ForeignKey(EnumType, on_delete=models.CASCADE)

    order = models.IntegerField(default=1)
    title = models.CharField(max_length=255)
    value = models.CharField(max_length=255)

    def __str__(self):
        return self.title

    def __lt__(self, other):
        return self.order < other.order

    class Meta:
        ordering = ('order', 'value',)

#-------------------------------------------------------------------------------
class ContentSlot(models.Model):

    #---------------------------------------------------------------------------
    # Relate to the any resource within the system
    django_content_type = models.ForeignKey(
        DjangoContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('django_content_type', 'object_id')

    order = models.IntegerField(default=1)
    key = modelfields.Key(max_length=200, unique=False, blank=True, null=True)

    class Meta:
        abstract = True
        ordering = ['order',]

    def save(self, *args, **kwargs):
        # Populate the key from the id of the slot
        super(ContentSlot, self).save(*args, **kwargs)
        self.key = self.key or "%d" % self.id # TODO: Find out if this line is effective anymore
        super(ContentSlot, self).save()

    def update_related(self, form=None):
        """
        A hook that is only run in the admin when someone save the resource.

        Use this to provide facilities like updating related fields based on
        our fields.
        """

    def get_resource_url(self):
        obj_url_func = getattr(self.content_object, 'url', None)
        if not obj_url_func:
            return ''
        else:
            return obj_url_func()

    def get_content_key(self, id=None):
        return string_to_key(
                "resource_%s_%s_%s_%s_%s_%s" % (
                    self.content_object.id,
                    self.__class__.__name__.replace("Resource", ""),
                    id or 0,
                    getattr(self.content_object, 'title', self.get_resource_url()),
                    self.key,
                    self.order
                )
            ).lower()

    @classmethod
    def get_select_related(cls):
        return []

