
import json
from urllib.parse import urlparse

from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django.db import models
from django.conf.urls import url
from django.shortcuts import render, get_object_or_404, Http404
from django.urls import reverse
from django.utils.safestring import mark_safe

from swim.django_admin import (
    register_content_slot_admin,
    ModelAdmin,
    SingleContentSlotInlineAdmin,
    ListContentSlotInlineAdmin,
    UnusedContentSlotInlineAdmin,
    register_content_slot_admin_generator,
    register_model_generates_csm_types,
)
from swim.media.models import (
    Image,
    File,
    Folder,
    FileSlot,
    ImageSlot,
    ImageType,
    ImageVariant,
)
from swim.media.fields import ImageField

#-------------------------------------------------------------------------------
class ThumbnailLinkMixin:
    """
    Mixin for Admin classes that add a method to generate a thumbnail
    """

    #---------------------------------------------------------------------------
    def thumbnail(self, obj):
        if obj:
            image = None
            if obj and isinstance(obj, ImageSlot) and obj.image:
                image = obj.image
            elif obj and isinstance(obj, Image):
                image = obj
            if image:
                return mark_safe(f'<a href="{image.url()}" target="_blank">{image.admin_thumbnail()}</a>')
        return mark_safe('<img src="/static/swim/images/empty-image.png" width="128" height="64"/>')


#-------------------------------------------------------------------------------
class ThumbnailMixin:
    """
    Mixin for Admin classes that add a method to generate a thumbnail
    """

    #---------------------------------------------------------------------------
    def thumbnail(self, obj):
        if obj:
            image = None
            if isinstance(obj, ImageSlot) and obj.image:
                image = obj.image
            elif isinstance(obj, Image):
                image = obj
            if image:
                return mark_safe(f'{image.admin_thumbnail()}')
        return mark_safe('<img src="/static/swim/images/empty-image.png" width="128" height="64"/>')


#-------------------------------------------------------------------------------
class CroppableImageAdminMixin:
    """
    Mixin for Admin classes that add a method to generate a link to edit the
    cropping for an image field.
    """

    #---------------------------------------------------------------------------
    def user_variant_crop_link(self, obj):
        if obj.id and obj.image:
            content_type = ContentType.objects.get_for_model(obj)
            return mark_safe('<a onclick="return showAddAnotherPopup(this);" href="{}" title="Crop Image"><img src="/static/swim/images/crop-image.png"></a>'.format(
                reverse('admin:swim.media.user-variant-crop', args=[content_type.id, obj.id])
            ))

        return 'Not Available'
    user_variant_crop_link.short_description = 'Crop'


#-------------------------------------------------------------------------------
class SingleFileSlotInlineAdmin(SingleContentSlotInlineAdmin):
    template = "admin/swim_single_inline_single_field.html"
    model = FileSlot
    autocomplete_fields = ('file',)

#-------------------------------------------------------------------------------
class ListFileSlotInlineAdmin(ListContentSlotInlineAdmin):
    model = FileSlot
    autocomplete_fields = ('file',)

#-------------------------------------------------------------------------------
class UnusedFileSlotInlineAdmin(UnusedContentSlotInlineAdmin):
    model = FileSlot

#-------------------------------------------------------------------------------
register_content_slot_admin(
    'swim.media.File',
    single=SingleFileSlotInlineAdmin,
    list=ListFileSlotInlineAdmin,
    unused=UnusedFileSlotInlineAdmin,
    can_delete=True,
    model=File,
    storage_model=FileSlot,
)


#-------------------------------------------------------------------------------
class SingleImageSlotInlineAdmin(
    SingleContentSlotInlineAdmin, CroppableImageAdminMixin, ThumbnailLinkMixin
):
    model = ImageSlot
    template = "admin/swim_single_inline_stacked.html"
    fields = ('thumbnail', 'image', 'user_variant_crop_link')
    readonly_fields = ('thumbnail', 'user_variant_crop_link',)
    autocomplete_fields = ('image',)

#-------------------------------------------------------------------------------
class ListImageSlotInlineAdmin(
    ListContentSlotInlineAdmin, CroppableImageAdminMixin, ThumbnailLinkMixin
):
    model = ImageSlot
    template = "admin/edit_inline/stacked.html"
    fields = ('order', 'thumbnail', 'image', 'user_variant_crop_link')
    readonly_fields = ('thumbnail', 'user_variant_crop_link',)
    autocomplete_fields = ('image',)

#-------------------------------------------------------------------------------
class UnusedImageSlotInlineAdmin(UnusedContentSlotInlineAdmin):
    model = ImageSlot

#-------------------------------------------------------------------------------
register_content_slot_admin(
    'swim.media.Image',
    single=SingleImageSlotInlineAdmin,
    list=ListImageSlotInlineAdmin,
    unused=UnusedImageSlotInlineAdmin,
    can_delete=True,
    model=Image,
    storage_model=ImageSlot,
)


#-------------------------------------------------------------------------------
class ImageSlotAdmin(ModelAdmin):
    save_on_top = True
    model = ImageSlot
    autocomplete_fields = ('image',)

    #---------------------------------------------------------------------------
    def get_model_perms(self, request):
        return {}

    #---------------------------------------------------------------------------
    def get_urls(self):
        urls = super(ImageSlotAdmin, self).get_urls()
        my_urls = [
            url(r'^(?P<content_type_id>[0-9]+)/(?P<object_id>[0-9]+)/user-variant-crop/$',
                self.admin_site.admin_view(self.user_variant_crop_view),
                name='swim.media.user-variant-crop'),
        ]
        return my_urls + urls

    #---------------------------------------------------------------------------
    def user_variant_crop_view(self, request, content_type_id, object_id):
        content_type = get_object_or_404(ContentType, id=content_type_id)
        klass = content_type.model_class()
        obj = get_object_or_404(klass, pk=object_id)

        try:
            # Trick VariantDict into loading all of its variant info.
            obj.variant['__this_is_not_a_real_key__']
        except KeyError:
            pass

        # Flatten the VariantDict so we can access the parameters and only show crops, not thumbs.
        variants = obj.variant.copy()
        for key, attributes in list(variants.items()):
            if not attributes.get('algorithm').startswith('crop'):
                del variants[key]

        context = {}
        if request.method == 'POST':
            for key in request.POST:
                if key.startswith('__'):
                    variant_key = key[2:]
                    user_variant_crop = obj.user_variant_crop or {}
                    user_crop = json.loads(request.POST[key])
                    user_variant_crop[variant_key] = user_crop
                    obj.user_variant_crop = user_variant_crop
                    obj.save()

                obj.delete_variants()
                context['success'] = True

        context.update({
            'obj': obj,
            'variants': variants,
        })
        return render(request, 'swim/media/user-variant-crop.html', context)


#-------------------------------------------------------------------------------
def get_image_type_inline_admin(type):
    try:
        it = ImageType.objects.get(_swim_content_type__title=type)
    except ImageType.DoesNotExist:
        return None
    return {
        'single': SingleImageSlotInlineAdmin,
        'list': ListImageSlotInlineAdmin,
        'unused': UnusedImageSlotInlineAdmin,
        'can_delete': True,
        'model': ImageSlot,
        'storage_model': ImageSlot,
    }
register_content_slot_admin_generator(get_image_type_inline_admin)
register_model_generates_csm_types(ImageType)

#-------------------------------------------------------------------------------
class FolderMover:
    """Callable that will move things to a particular folder.
    """
    #-------------------------------------------------------------------------------
    def __init__(self, folder):
        self.folder = folder

    #-------------------------------------------------------------------------------
    def __call__(self, model_admin, request, queryset):
        queryset.update(folder=self.folder)

#-------------------------------------------------------------------------------
class _BaseFileAdmin(ModelAdmin):
    #---------------------------------------------------------------------------
    def get_actions(self, request):
        actions = super(_BaseFileAdmin, self).get_actions(request)
        for folder in Folder.objects.all().order_by('name'):
            actions['move_to_folder_%s'%folder.id] = (
                FolderMover(folder),
                'move_to_folder_%s' % folder.id,
                'Move to Folder: %s' % folder.name,
            )
        return actions

#-------------------------------------------------------------------------------
class ImageAdmin(
    _BaseFileAdmin, ThumbnailMixin
):
    save_on_top = True
    list_display = ('thumbnail', 'folder', 'url', 'creationdate', 'modifieddate')
    list_filter = ('folder',)
    search_fields = ('image', 'folder__name')
    readonly_fields = ('thumbnail',)
    fields = (
        "folder",
        "thumbnail",
        "image",
        "title",
        "alt",
        "caption",
        "link_url"
    )

#-------------------------------------------------------------------------------
class FileAdmin(_BaseFileAdmin):
    save_on_top = True
    list_display = ('filename', 'folder', 'url', 'creationdate', 'modifieddate')
    list_filter = ('folder',)
    search_fields = ('file', 'folder__name')

#-------------------------------------------------------------------------------
class ImageInlineAdmin(admin.TabularInline):
    model = Image

    readonly_fields = ('path',)
    fields = ('image',  'path', 'title', 'alt', 'caption', 'link_url')

    def path(self, obj):
        o = urlparse(obj.url())
        return o.path


#-------------------------------------------------------------------------------
class FileInlineAdmin(admin.TabularInline):
    model = File
    readonly_fields = ('path',)
    fields = ('file',  'path', 'caption')

    def path(self, obj):
        o = urlparse(obj.url())
        return o.path

#-------------------------------------------------------------------------------
class FolderAdmin(ModelAdmin):
    save_on_top = True
    list_display = ('name', 'file_count', 'image_count')

    inlines = [
        ImageInlineAdmin,
        FileInlineAdmin,
    ]


#-------------------------------------------------------------------------------
class ImageVariantInline(admin.TabularInline):
    template = "admin/swim_tabular.html"
    model = ImageVariant
    extra = 0

#-------------------------------------------------------------------------------
class ImageTypeAdmin(ModelAdmin):
    exclude = ['_swim_content_type',]
    search_fields = (
        'key',
        'title',
    )
    list_display = (
        'title',
        'key',
    )
    inlines = [
        ImageVariantInline,
    ]

# Content Models
admin.site.register(Image, ImageAdmin)
admin.site.register(File, FileAdmin)
admin.site.register(Folder, FolderAdmin)
admin.site.register(ImageType, ImageTypeAdmin)
admin.site.register(ImageSlot, ImageSlotAdmin)

