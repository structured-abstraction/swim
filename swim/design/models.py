import time

from django.db import models
from django.conf import settings
from django.utils.http import http_date
from django.template import TemplateDoesNotExist
from django.contrib.sites.models import Site
from django.db.models import Q

from swim.core import modelfields, string_to_key
from swim.core.models import (
    KeyedModel,
    ModelBase,
    Resource,
    ResourceType,
    resource_type_default,
    ContentType as SwimContentType,
)
from swim.media.fields import ImageField

#-------------------------------------------------------------------------------
class WithResourceTypeAndTemplate(models.Manager):
    """
    A query manager which minimizes query to 'get' the associated resource_type.
    """
    def get_query_set(self):
        return super(WithResourceTypeAndTemplate, self).get_query_set().select_related(
                'resource_type',
                'template'
            )

#-------------------------------------------------------------------------------
def get_resource_swim_content_type():
    """stub function to deal with scoping issues below
    """
    return Resource.swim_content_type()

#-------------------------------------------------------------------------------
class Template(ModelBase):
    """Template for designers to modify.

    Defines a template model for use with the database template loader.
    The field ``path`` is the equivalent to the filename of a static template.
    """

    path = models.CharField(max_length=100)
    http_content_type = models.CharField(
            max_length=100,
            default='text/html; charset=utf-8'
        )
    swim_content_type = models.ForeignKey(
        SwimContentType,
        related_name="%(class)s_set",
        default=get_resource_swim_content_type,
        on_delete=models.CASCADE,
    )
    body = models.TextField("Body")

    domains = models.ManyToManyField(Site, related_name='templates', blank=True)

    def __str__(self):
        return "%s, %s -> %s" % (self.path, self.swim_content_type, self.http_content_type)

    def save(self, *args, **kwargs):
        # Templates need to store their paths lower case to do lookups properly
        self.path = self.path.lower()
        super(Template, self).save(*args, **kwargs)

    class Meta:
        verbose_name = 'template'
        verbose_name_plural = 'templates'
        ordering = ('path',)
        unique_together = (("path", "http_content_type", "swim_content_type" ),)


#------------------------------------------------------------------------------
class CSS(ModelBase):
    """
    """
    path = models.CharField(
        max_length=255,
        help_text = "The css will be available on /css/&lt;path&gt;/"
    )
    body = models.TextField()

    # Model instance methods and properties
    def __str__(self):
        return self.path

    class Meta:
        verbose_name = 'CSS'
        verbose_name_plural = 'CSS'
        ordering = ('path',)

#------------------------------------------------------------------------------
class JavaScript(ModelBase):
    """
    """
    path = models.CharField(
        max_length=255,
        help_text = "The javascript will be available on /js/&lt;path&gt;/"
    )
    body = models.TextField()

    # Model instance methods and properties
    def __str__(self) :
        return self.path

    class Meta:
        verbose_name = 'JavaScript'
        verbose_name_plural = 'JavaScript'
        ordering = ('path',)


#------------------------------------------------------------------------------
# TODO: generalize swim.design.image top swim.design. file or resource ?
class Image(KeyedModel):
    """
    """
    folder = 'design/image'
    image = ImageField(upload_to=folder,)
    alt = models.CharField(max_length=200, blank=True, null=True, help_text="Alternate Text")

    def __str__(self):
        return self.filename()

    def url(self):
        return self.image.url

    def ext(self):
        return self.filename().rsplit('.', 1)[-1]

    def filename(self):
        return self.image.path.rsplit('/', 1)[-1]

    # Special agregate classes
    class Admin:
        save_on_top = True
        list_display = ('filename', 'url', 'creationdate', 'modifieddate')

    def save(self, *args, **kwargs):
        self.key = self.key or string_to_key(self.alt or "Untitled")
        super(Image, self).save(*args, **kwargs)


RTTM_select_related = ['template__swim_content_type', 'resource_type']

#-------------------------------------------------------------------------------
class ResourceTypeTemplateMapping(ModelBase):
    """Relates content.ResourceType and design.Template

    attributes:
    order
        Orders these into a priority list.
    template
        Maps a template to a particular ResourceType
    resource_type
        Maps a ResourceType to a particular template
    """
    # TODO: consider a unique_together = ('template__http_content_type', 'resource_type')
    order = models.IntegerField(default=1)
    template = models.ForeignKey(
        Template,
        on_delete=models.CASCADE,
    )
    resource_type = models.ForeignKey(
        ResourceType,
        default=resource_type_default,
        on_delete=models.CASCADE,
    )

    objects = WithResourceTypeAndTemplate()



    def __str__(self):
        return "%s -> %s" % (self.resource_type, self.template)

    def get_template(request, resource_type, swim_content_type, http_content_type):
        """
        Return a the highest priority template for the given types.

        If there are no templates for that resource_type/swim_content_type try our
        parent.

        raises ResourceTypeTemplateMapping.DoesNotExist when no template exists.
        """
        resource_type_templates = getattr(request, 'resource_type_templates', {}).setdefault(
                resource_type.id, {})

        template =  resource_type_templates.get(swim_content_type, None)
        if not template:
            host_name = request.META.get('HTTP_HOST')
            domain_specific_template_set = []
            if host_name:
                template_set = ResourceTypeTemplateMapping.objects.filter(
                        Q(resource_type=resource_type) &
                        (
                            Q(template__domains__domain__iexact=host_name) |
                            Q(template__domains__domain__isnull=True)
                        )
                    ).select_related(
                        *RTTM_select_related
                    ).extra(
                        select={'has_domain': "COALESCE(django_site.domain, '/')"}
                    ).extra(
                        order_by = ['-has_domain', 'template__swim_content_type', 'order']
                    )
            else:
                template_set = ResourceTypeTemplateMapping.objects.filter(
                        resource_type = resource_type,
                        template__domains__domain__isnull=True,
                    ).select_related(*RTTM_select_related).order_by('template__swim_content_type', 'order')

            for template in template_set:
                if template.template.swim_content_type not in resource_type_templates:
                    resource_type_templates[template.template.swim_content_type] = template

        template =  resource_type_templates.get(swim_content_type, None)
        if template:
            return template

        if resource_type.parent:
            template = ResourceTypeTemplateMapping.get_template(
                    request,
                    resource_type.parent,
                    swim_content_type,
                    http_content_type
                )
            if template:
                resource_type_templates[swim_content_type] = template
                return template

        error_message = "No template matching %s, %s, %s" % (
                resource_type, swim_content_type, http_content_type
            )
        raise TemplateDoesNotExist(error_message)
    get_template = staticmethod(get_template)

    def get_potential_templates(request, resource_type, swim_content_type):
        """Return a prioritized set of templates based on resource_type/swim_content_type.

        If there are no templates for that resource_type/swim_content_type try our
        parent.

        Returns an empty list when none are found.
        """
        host_name = request.META.get('HTTP_HOST')
        domain_specific_template_set = []
        if host_name:
            template_set = ResourceTypeTemplateMapping.objects.filter(
                    Q(resource_type=resource_type) &
                    Q(template__swim_content_type=swim_content_type) &
                    (
                        Q(template__domains__domain__iexact=host_name) |
                        Q(template__domains__domain__isnull=True)
                    )
                ).select_related(
                    *RTTM_select_related
                ).extra(
                    select={'has_domain': "COALESCE(django_site.domain, '/')"}
                ).extra(
                    order_by = ['-has_domain', 'order']
                )
        else:
            template_set = ResourceTypeTemplateMapping.objects.filter(
                    resource_type=resource_type,
                    template__swim_content_type=swim_content_type,
                    template__domains__domain__isnull=True,
                ).select_related(*RTTM_select_related).order_by('order')

        if resource_type.parent and len(template_set) == 0:
            return ResourceTypeTemplateMapping.get_potential_templates(
                    request,
                    resource_type.parent,
                    swim_content_type
                )
        else:
            return template_set
    get_potential_templates = staticmethod(get_potential_templates)


    class Meta:
        ordering = ('order',)
