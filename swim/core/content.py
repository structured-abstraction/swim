"""
Provides the API for defining and registering content types within SWIM

In SWIM, content is built up from a dynamic association of atomic content
containers. These content atoms are not atomic in the computer science sense, but rather
represent the lowest level, indivisble piece of content available to SWIM.

Content atoms can be associated to content objects via a generic foreign key and
we provide an API for accessing the atoms associated with any given instance.
When registering the atom, you provide the unique attribute_name which is used
to look up the content atoms.  We distinguish between two different types of
content atoms.  Those which are 'strong', which exist independent of any association
with a content object and are stored in their own table, and those which are 'weak'
which only exist in relation to a content object.

We provide a AtomType class which is used to associate 'weak' content atoms with
content objects via a register_atom_type call, and a ReferencedAtomType which is used
to associate a strong content atom with content objects via the same call.

TODO: Better documentation for this module.
"""
import itertools

from django.contrib.contenttypes.models import ContentType as DjangoContentType
from django.db.models.signals import post_init
from django.dispatch import Signal

from swim.core.models import ContentSchemaMember

#-------------------------------------------------------------------------------
def get_atoms(
    model,
    django_content_type,
    instance_id_list,
    related_args=None,
    related_kwargs=None
):
    """
    Builds a queryset for content atoms related to a given set of content objects.
    """
    if related_args is None:
        related_args = []
    if related_kwargs is None:
        related_kwargs = {}
    qs = model.objects.filter(
            django_content_type__pk=django_content_type.id,
            object_id__in=instance_id_list,
        ).order_by(
            'object_id',
            'order',
        )
    if not related_args and not related_kwargs:
        return qs
    else:
        return qs.select_related(*related_args, **related_kwargs)


#-------------------------------------------------------------------------------
class BaseAtomAccessor:
    """
    A class that eases the code necessary to access content atoms.
    """

    #---------------------------------------------------------------------------
    def __init__(self, model, gfk_model, attr_name):
        self.model = model
        self.gfk_model = gfk_model
        self.attr_name = attr_name
        self.cache_name = "_%s_cache" % attr_name

    #---------------------------------------------------------------------------
    def _is_cached(self, instance):
        """
        Determine if we have cached atoms in this case.
        """
        return getattr(instance, self.cache_name, None) is not None

    #---------------------------------------------------------------------------
    def _get_cache(self, instance):
        """
        Returns the cached items.
        """
        return getattr(instance, self.cache_name)

    #---------------------------------------------------------------------------
    def _update_cache(self, instance):
        # if the cache isn't there, go ahead and hit the database.
        if not self._is_cached(instance):
            self._generate_cache(instance)

    #---------------------------------------------------------------------------
    def __get__(self, instance, owner):
        raise NotImplementedError

    #---------------------------------------------------------------------------
    def _cache_atoms(self, instance, atoms):
        setattr(instance, self.cache_name, atoms)

    #---------------------------------------------------------------------------
    def _generate_cache(self, instance):
        django_content_type = DjangoContentType.objects.get_for_model(self.model)
        related_args = self.gfk_model.get_select_related()
        related = get_atoms(
            self.gfk_model, django_content_type, [instance.id],
            related_args=related_args
        )
        self._cache_atoms(instance, list(related))

    #---------------------------------------------------------------------------
    def _apply_interface(self, instance, key, atom_list):
        interface = None
        try:
            interface = instance.get_interface(key)
        except (ContentSchemaMember.DoesNotExist, IndexError, KeyError):
            pass

        if interface and interface['cardinality'] == 'list':
            return atom_list
        elif interface and interface['cardinality'] == 'single':
            return atom_list[0]
        else:
            return atom_list[0]


#-------------------------------------------------------------------------------
class AtomAccessor(BaseAtomAccessor):

    #---------------------------------------------------------------------------
    def __get__(self, instance, owner):
        self._update_cache(instance)
        return self._get_cache(instance)

    #---------------------------------------------------------------------------
    def __set__(self, instance, value):
        if not isinstance(value, list):
            value = [value]
        self._cache_atoms(instance, value)

    #---------------------------------------------------------------------------
    def _cache_atoms(self, instance, atoms):
        cache = {}
        setattr(instance, self.cache_name, cache)

        keys = set()
        for atom_instance in atoms:
            keys.add(atom_instance.key)
            instance_list = cache.setdefault(atom_instance.key, [])
            atom_instance.content_object = instance
            instance_list.append(atom_instance)

        for key in keys:
            cache[key] = self._apply_interface(instance, key, cache[key])

#-------------------------------------------------------------------------------
class BaseAtomType:
    #---------------------------------------------------------------------------
    def get_atoms(self, slot_model, django_content_type, instance_id_list):
        return get_atoms(slot_model, django_content_type, instance_id_list)

#-------------------------------------------------------------------------------
class AtomType(BaseAtomType):
    """
    An atom type that is stored directly in the content_slot model.
    """

    #---------------------------------------------------------------------------
    def __init__(self, content_slot_model):
        self.content_slot_model = content_slot_model

    #---------------------------------------------------------------------------
    def contribute_to_model(self, attr_name, model):
        # Set up the content schema member accessor so that this works:
        # instance.copy.<attr_name>
        keyed_accessor = AtomAccessor(
            model, self.content_slot_model, attr_name=attr_name
        )
        model._atom_accessors.append(keyed_accessor)
        setattr(model, attr_name, keyed_accessor)

#-------------------------------------------------------------------------------
class BaseReferencedAtomAccessor(BaseAtomAccessor):
    """
    A class that eases the code necessary to access content atoms.
    """

    #---------------------------------------------------------------------------
    def __init__(
            self,
            model,
            gfk_model,
            content_atom_model,
            gfk_attrname=None,
            attr_name=None,
        ):
        super(BaseReferencedAtomAccessor, self).__init__(model, gfk_model, attr_name)
        self.content_atom_model = content_atom_model

        if not gfk_attrname:
            self.gfk_attrname = '%s' % (
                    self.content_atom_model.__name__.lower(),
                )

    #---------------------------------------------------------------------------
    def __get__(self, instance, owner):
        raise NotImplementedError

#-------------------------------------------------------------------------------
class ReferencedAtomAccessor(BaseReferencedAtomAccessor):
    #---------------------------------------------------------------------------
    def __get__(self, instance, value):
        self._update_cache(instance)
        return self._get_cache(instance)

    #---------------------------------------------------------------------------
    def __set__(self, instance, value):
        if not isinstance(value, list):
            value = [value]
        self._cache_atoms(instance, value)

    #---------------------------------------------------------------------------
    def _cache_atoms(self, instance, atoms):
        cache = {}
        setattr(instance, self.cache_name, cache)

        keys = set()
        for atom_instance in atoms:
            keys.add(atom_instance.key)
            atom_instance.content_object = instance
            resourceattribute = getattr(atom_instance, self.gfk_attrname)
            resourceattribute._content_slot = atom_instance
            instance_list = cache.setdefault(atom_instance.key, [])
            instance_list.append(resourceattribute)

        for key in keys:
            cache[key] = self._apply_interface(instance, key, cache[key])

#-------------------------------------------------------------------------------
class ReferencedAtomType(BaseAtomType):
    """
    An atom type that is stored via a reference.
    """
    #---------------------------------------------------------------------------
    def __init__(self, atom_model, content_slot_model):
        self.atom_model = atom_model
        self.content_slot_model = content_slot_model

    #---------------------------------------------------------------------------
    def get_atoms(self, slot_model, django_content_type, instance_id_list):
        related_args = slot_model.get_select_related()
        return get_atoms(
                slot_model,
                django_content_type,
                instance_id_list,
                related_args=related_args
            )

    #---------------------------------------------------------------------------
    def contribute_to_model(self, attr_name, model):
        # Set up the content schema member accessor so that this works:
        # instance.copy.<attr_name>
        keyed_accessor = ReferencedAtomAccessor(
                model=model,
                content_atom_model=self.atom_model,
                gfk_model=self.content_slot_model,
                attr_name=attr_name,
            )
        model._atom_accessors.append(keyed_accessor)
        setattr(model, attr_name, keyed_accessor)

#-------------------------------------------------------------------------------
class DjangoModelContentObject:
    """
    A wrapper around a django model which marks it as a content object.
    """
    #---------------------------------------------------------------------------
    def __init__(self, django_model):
        self.django_model = django_model
        self.django_model.content_object = self

    #---------------------------------------------------------------------------
    def get_name(self):
        # ex swim.content.Page
        return "%s.%s" % (
            self.django_model.__module__.rsplit('.', 1)[0],
            self.django_model.__name__
        )

    #---------------------------------------------------------------------------
    def get_context_name(self):
        return self.get_name().rsplit('.', 1)[1].lower()

    #---------------------------------------------------------------------------
    def lookup_key(self, key, request):
        content_obj = None
        if hasattr(self.django_model, 'type_field_name'):
            content_obj = self.django_model.objects.select_related(
                        self.django_model.type_field_name
                    ).get(key=key)
        else:
            content_obj = self.django_model.objects.get(key=key)

        if hasattr(content_obj, 'set_request'):
            content_obj.set_request(request)

        return content_obj

#-------------------------------------------------------------------------------
# A module level global that is used to lookup the appropriate content object
# type based on the values in the ContentType table.
DJANGO_MODEL_SWIM_CONTENT_TYPE_LOOKUPS = {}
CONTENT_OBJECTS = []

#-------------------------------------------------------------------------------
# A module level global that tracks the various types of content slots.
CONTENT_ATOM_METADATA = {}


#-------------------------------------------------------------------------------
class DjangoContentTypeGetter:
    """
    A callable that retrieves the django content type object for the given model.

    Caches it so that it's only looked up once per the lifetime of the model -
    which should approximate the server lifetime. This callable is attached to
    each content-object as it is registered with register_content_object below.
    """
    #---------------------------------------------------------------------------
    def __init__(self, cls):
        self.cls = cls

    #---------------------------------------------------------------------------
    def __call__(self):
        cls = self.cls
        if not hasattr(cls, '_django_content_type'):
            cls._django_content_type = DjangoContentType.objects.get_for_model(
                cls
            )
        return cls._django_content_type



#-------------------------------------------------------------------------------
def register_content_object(name, model, global_key=False):
    """
    """
    global DJANGO_MODEL_SWIM_CONTENT_TYPE_LOOKUPS
    global CONTENT_OBJECTS

    # Provide a way to get a (cached) instance of django's content type
    # for each content object.
    model.get_django_content_type = DjangoContentTypeGetter(model)

    # Keep a list of SWIM's content objects
    CONTENT_OBJECTS.append(model)

    #
    dmco = DjangoModelContentObject(model)
    DJANGO_MODEL_SWIM_CONTENT_TYPE_LOOKUPS[name] = dmco

    # TODO: this is a bit wasteful to be calling this everytime something
    #       is registered, but meh - we'll optimize that afterwards
    attach_content_atom_accessors()

#-------------------------------------------------------------------------------
def register_atom_type(attribute_name, content_atom):
    """
    Registers a new content atom type with SWIM.

    Use this to define a new atom type that can be accessed via the
    <attribute_name> attribute on all content objects.
    """
    global CONTENT_ATOM_METADATA
    CONTENT_ATOM_METADATA[attribute_name] = content_atom
    # TODO: this is a bit wasteful to be calling this everytime something
    #       is registered, but meh - we'll optimize that afterwards
    attach_content_atom_accessors()

#-------------------------------------------------------------------------------
def attach_content_atom_accessors():
    for name, dmco in DJANGO_MODEL_SWIM_CONTENT_TYPE_LOOKUPS.items():
        model = dmco.django_model
        model._atom_accessors = []
        for attr_name, content_atom in CONTENT_ATOM_METADATA.items():
            content_atom.contribute_to_model(attr_name, model)

