from os import path
from django.contrib import admin
from django.db import models
from django import forms
from django.contrib.contenttypes.models import ContentType as DjangoContentType
from django.template.defaultfilters import slugify
from django.core.exceptions import ObjectDoesNotExist
from django.utils.safestring import mark_safe

from swim.generic import (
    DisabledWithHidden,
    ArrangementSingleResourceFormSet,
    ArrangementListResourceFormSet,
    ClassFactory,
)
from swim.django_admin import (
    register_content_slot_admin,
    register_content_slot_admin_generator,
    ResourceModelAdmin,
    ArrangementModelAdmin,
    ModelAdmin,
    TextAreaMixin,
    TextInputMixin,
    TinyMCEMixin,
    CKEditorMixin,
    EditAreaMixin,
    ContentSlotInlineAdmin,
    SingleContentSlotInlineAdmin,
    ListContentSlotInlineAdmin,
    UnusedContentSlotInlineAdmin,
    ContentSlotInlineAdmin,
    register_model_generates_csm_types,
)
from swim.core.models import (
    ResourceType,
    ReservedPath,
    ArrangementType,
    EnumType,
    EnumTypeChoice,
)
from swim.content.models import (
    TextInputCopy,
    TinyMCECopy,
    CKEditorCopy,
    EditAreaCopy,
    TextAreaCopy,
    Link,
    Menu,
    MenuLink,
    Arrangement,
    Page,
    PageSlot,
    PageType,
    CopySlot,
    MenuSlot,
    DateSlot,
    DateTimeSlot,
    TimeSlot,
    IntegerSlot,
    InstantSlot,
    PeriodSlot,
    ArrangementSlot,
    EnumSlot,
    SiteWideContent,
)
from swim.seo.admin import SEO_FIELDSET

#-------------------------------------------------------------------------------
class SingleCopySlotInlineAdmin(TinyMCEMixin, SingleContentSlotInlineAdmin):
    template = "admin/swim_single_inline_single_field.html"
    model = CopySlot

#-------------------------------------------------------------------------------
class ListCopySlotInlineAdmin(TinyMCEMixin, ListContentSlotInlineAdmin):
    model = CopySlot

#-------------------------------------------------------------------------------
class UnusedCopySlotInlineAdmin(TinyMCEMixin, UnusedContentSlotInlineAdmin):
    model = CopySlot

#-------------------------------------------------------------------------------
register_content_slot_admin(
    'swim.content.CopySlot',
    single=SingleCopySlotInlineAdmin,
    list=ListCopySlotInlineAdmin,
    unused=UnusedCopySlotInlineAdmin,
    can_delete=True,
    model=CopySlot,
    storage_model=CopySlot,
)

#-------------------------------------------------------------------------------
class SingleResourceTextInputCopyInlineAdmin(TextInputMixin, SingleContentSlotInlineAdmin):
    template = "admin/swim_single_inline_single_field.html"
    model = CopySlot

#-------------------------------------------------------------------------------
class ListResourceTextInputCopyInlineAdmin(TextInputMixin, ListContentSlotInlineAdmin):
    model = CopySlot

#-------------------------------------------------------------------------------
class UnusedResourceTextInputCopyInlineAdmin(TextInputMixin, UnusedContentSlotInlineAdmin):
    model = CopySlot

#-------------------------------------------------------------------------------
register_content_slot_admin(
    'swim.content.TextInputCopy',
    single=SingleResourceTextInputCopyInlineAdmin,
    list=ListResourceTextInputCopyInlineAdmin,
    unused=UnusedResourceTextInputCopyInlineAdmin,
    can_delete=True,
    model=TextInputCopy,
    storage_model=CopySlot,
)

#-------------------------------------------------------------------------------
class SingleResourceTextAreaCopyInlineAdmin(TextAreaMixin, SingleContentSlotInlineAdmin):
    template = "admin/swim_single_inline_single_field.html"
    model = CopySlot

#-------------------------------------------------------------------------------
class UnusedResourceTextAreaCopyInlineAdmin(TextAreaMixin, UnusedContentSlotInlineAdmin):
    model = CopySlot

#-------------------------------------------------------------------------------
class ListResourceTextAreaCopyInlineAdmin(TextAreaMixin, ListContentSlotInlineAdmin):
    model = CopySlot

#-------------------------------------------------------------------------------
register_content_slot_admin(
    'swim.content.TextAreaCopy',
    single=SingleResourceTextAreaCopyInlineAdmin,
    list=ListResourceTextAreaCopyInlineAdmin,
    unused=UnusedResourceTextAreaCopyInlineAdmin,
    can_delete=True,
    model=TextAreaCopy,
    storage_model=CopySlot,
)


#-------------------------------------------------------------------------------
class SingleResourceEditAreaCopyInlineAdmin(EditAreaMixin, SingleContentSlotInlineAdmin):
    template = "admin/swim_single_inline_single_field.html"
    model = CopySlot

#-------------------------------------------------------------------------------
class ListResourceEditAreaCopyInlineAdmin(EditAreaMixin, ListContentSlotInlineAdmin):
    model = CopySlot

#-------------------------------------------------------------------------------
class UnusedResourceEditAreaCopyInlineAdmin(EditAreaMixin, UnusedContentSlotInlineAdmin):
    model = CopySlot

#-------------------------------------------------------------------------------
register_content_slot_admin(
    'swim.content.EditAreaCopy',
    single=SingleResourceEditAreaCopyInlineAdmin,
    list=ListResourceEditAreaCopyInlineAdmin,
    unused=UnusedResourceEditAreaCopyInlineAdmin,
    can_delete=True,
    model=EditAreaCopy,
    storage_model=CopySlot,
)

#-------------------------------------------------------------------------------
class SingleResourceTinyMCECopyInlineAdmin(TinyMCEMixin, SingleContentSlotInlineAdmin):
    template = "admin/swim_single_inline_single_field.html"
    model = CopySlot

#-------------------------------------------------------------------------------
class ListResourceTinyMCECopyInlineAdmin(TinyMCEMixin, ListContentSlotInlineAdmin):
    model = CopySlot

#-------------------------------------------------------------------------------
class UnusedResourceTinyMCECopyInlineAdmin(TinyMCEMixin, UnusedContentSlotInlineAdmin):
    model = CopySlot

#-------------------------------------------------------------------------------
# TODO: add tests for TinyMCE
register_content_slot_admin(
    'swim.content.TinyMCECopy',
    single=SingleResourceTinyMCECopyInlineAdmin,
    list=ListResourceTinyMCECopyInlineAdmin,
    unused=UnusedResourceTinyMCECopyInlineAdmin,
    can_delete=True,
    model=TinyMCECopy,
    storage_model=CopySlot,
)

#-------------------------------------------------------------------------------
class SingleResourceCKEditorCopyInlineAdmin(CKEditorMixin, SingleContentSlotInlineAdmin):
    template = "admin/swim_single_inline_single_field.html"
    model = CopySlot

#-------------------------------------------------------------------------------
class ListResourceCKEditorCopyInlineAdmin(CKEditorMixin, ListContentSlotInlineAdmin):
    model = CopySlot

#-------------------------------------------------------------------------------
class UnusedResourceCKEditorCopyInlineAdmin(CKEditorMixin, UnusedContentSlotInlineAdmin):
    model = CopySlot

#-------------------------------------------------------------------------------
# TODO: add tests for CKEditor
register_content_slot_admin(
    'swim.content.CKEditorCopy',
    single=SingleResourceCKEditorCopyInlineAdmin,
    list=ListResourceCKEditorCopyInlineAdmin,
    unused=UnusedResourceCKEditorCopyInlineAdmin,
    can_delete=True,
    model=CKEditorCopy,
    storage_model=CopySlot,
)

#-------------------------------------------------------------------------------
class SingleMenuSlotInlineAdmin(SingleContentSlotInlineAdmin):
    template = "admin/swim_single_inline_single_field.html"
    model = MenuSlot

#-------------------------------------------------------------------------------
class ListMenuSlotInlineAdmin(ListContentSlotInlineAdmin):
    model = MenuSlot

#-------------------------------------------------------------------------------
class UnusedMenuSlotInlineAdmin(UnusedContentSlotInlineAdmin):
    model = MenuSlot

#-------------------------------------------------------------------------------
register_content_slot_admin(
    'swim.content.Menu',
    single=SingleMenuSlotInlineAdmin,
    list=ListMenuSlotInlineAdmin,
    unused=UnusedMenuSlotInlineAdmin,
    can_delete=True,
    model=Menu,
    storage_model=MenuSlot,
)


#-------------------------------------------------------------------------------
class SingleDateSlotInlineAdmin(SingleContentSlotInlineAdmin):
    template = "admin/swim_single_inline_single_field.html"
    model = DateSlot

#-------------------------------------------------------------------------------
class ListDateSlotInlineAdmin(ListContentSlotInlineAdmin):
    model = DateSlot

#-------------------------------------------------------------------------------
class UnusedDateSlotInlineAdmin(UnusedContentSlotInlineAdmin):
    model = DateSlot

#-------------------------------------------------------------------------------
register_content_slot_admin(
    'swim.content.DateSlot',
    single=SingleDateSlotInlineAdmin,
    list=ListDateSlotInlineAdmin,
    unused=UnusedDateSlotInlineAdmin,
    can_delete=True,
    model=DateSlot,
    storage_model=DateSlot,
)


#-------------------------------------------------------------------------------
class SingleDateTimeSlotInlineAdmin(SingleContentSlotInlineAdmin):
    template = "admin/swim_single_inline_single_field.html"
    model = DateTimeSlot

#-------------------------------------------------------------------------------
class ListDateTimeSlotInlineAdmin(ListContentSlotInlineAdmin):
    model = DateTimeSlot

#-------------------------------------------------------------------------------
class UnusedDateTimeSlotInlineAdmin(UnusedContentSlotInlineAdmin):
    model = DateTimeSlot

#-------------------------------------------------------------------------------
register_content_slot_admin(
    'swim.content.DateTimeSlot',
    single=SingleDateTimeSlotInlineAdmin,
    list=ListDateTimeSlotInlineAdmin,
    unused=UnusedDateTimeSlotInlineAdmin,
    can_delete=True,
    model=DateTimeSlot,
    storage_model=DateTimeSlot,
)

#-------------------------------------------------------------------------------
class SingleTimeSlotInlineAdmin(SingleContentSlotInlineAdmin):
    template = "admin/swim_single_inline_single_field.html"
    model = TimeSlot

#-------------------------------------------------------------------------------
class ListTimeSlotInlineAdmin(ListContentSlotInlineAdmin):
    model = TimeSlot

#-------------------------------------------------------------------------------
class UnusedTimeSlotInlineAdmin(UnusedContentSlotInlineAdmin):
    model = TimeSlot

#-------------------------------------------------------------------------------
register_content_slot_admin(
    'swim.content.TimeSlot',
    single=SingleTimeSlotInlineAdmin,
    list=ListTimeSlotInlineAdmin,
    unused=UnusedTimeSlotInlineAdmin,
    can_delete=True,
    model=TimeSlot,
    storage_model=TimeSlot,
)

#-------------------------------------------------------------------------------
class SingleInstantSlotInlineAdmin(SingleContentSlotInlineAdmin):
    model = InstantSlot

#-------------------------------------------------------------------------------
class ListInstantSlotInlineAdmin(ListContentSlotInlineAdmin):
    model = InstantSlot

#-------------------------------------------------------------------------------
class UnusedInstantSlotInlineAdmin(UnusedContentSlotInlineAdmin):
    model = InstantSlot

#-------------------------------------------------------------------------------
register_content_slot_admin(
    'swim.content.InstantSlot',
    single=SingleInstantSlotInlineAdmin,
    list=ListInstantSlotInlineAdmin,
    unused=UnusedInstantSlotInlineAdmin,
    can_delete=True,
    model=InstantSlot,
    storage_model=InstantSlot,
)

#-------------------------------------------------------------------------------
class SinglePeriodSlotInlineAdmin(SingleContentSlotInlineAdmin):
    model = PeriodSlot

#-------------------------------------------------------------------------------
class ListPeriodSlotInlineAdmin(ListContentSlotInlineAdmin):
    model = PeriodSlot

#-------------------------------------------------------------------------------
class UnusedPeriodSlotInlineAdmin(UnusedContentSlotInlineAdmin):
    model = PeriodSlot

#-------------------------------------------------------------------------------
register_content_slot_admin(
    'swim.content.PeriodSlot',
    single=SinglePeriodSlotInlineAdmin,
    list=ListPeriodSlotInlineAdmin,
    unused=UnusedPeriodSlotInlineAdmin,
    can_delete=True,
    model=PeriodSlot,
    storage_model=PeriodSlot,
)

#-------------------------------------------------------------------------------
class SingleIntegerSlotInlineAdmin(SingleContentSlotInlineAdmin):
    template = "admin/swim_single_inline_single_field.html"
    model = IntegerSlot

#-------------------------------------------------------------------------------
class ListIntegerSlotInlineAdmin(ListContentSlotInlineAdmin):
    model = IntegerSlot

#-------------------------------------------------------------------------------
class UnusedIntegerSlotInlineAdmin(UnusedContentSlotInlineAdmin):
    model = IntegerSlot

#-------------------------------------------------------------------------------
register_content_slot_admin(
    'swim.content.IntegerSlot',
    single=SingleIntegerSlotInlineAdmin,
    list=ListIntegerSlotInlineAdmin,
    unused=UnusedIntegerSlotInlineAdmin,
    can_delete=True,
    model=IntegerSlot,
    storage_model=IntegerSlot,
)


#-------------------------------------------------------------------------------
class EnumAdminMixin:
    """
    Restricts the choices to those available for this enum type.
    """

    #---------------------------------------------------------------------------
    def get_enum_type(self):
        return EnumType.objects.get(
                _swim_content_type=self.interface.swim_content_type
            )

    #---------------------------------------------------------------------------
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "choice":
            kwargs["queryset"] = EnumTypeChoice.objects.filter(
                    enum_type=self.get_enum_type()
                ).order_by('order')
            return db_field.formfield(**kwargs)
        return super(EnumAdminMixin, self).formfield_for_foreignkey(db_field, request, **kwargs)

    #---------------------------------------------------------------------------
    def formfield_for_dbfield(self, db_field, **kwargs):
        """
        Override SWIM's Default form field behavior
        """

        # In this case, we're doing something that's probably considered bad form
        # referring to a type that we're not technically inherting from.  BUT
        # this class is intended to only be used with classes that DO inherit from
        # ContentSlotInlineAdmin - so we actually want to bypass it's handling
        # of foreign_keys
        return super(ContentSlotInlineAdmin, self).formfield_for_dbfield(
                db_field, **kwargs)

#-------------------------------------------------------------------------------
class SingleEnumSlotInlineAdmin(
    EnumAdminMixin,
    SingleContentSlotInlineAdmin
):
    template = "admin/swim_single_inline_single_field.html"
    exclude = ['enum_type', 'key', 'order']
    model = EnumSlot

#-------------------------------------------------------------------------------
class ListEnumSlotInlineAdmin(
    EnumAdminMixin,
    ListContentSlotInlineAdmin
):
    exclude = ['enum_type', 'key', ]
    model = EnumSlot

#-------------------------------------------------------------------------------
class UnusedEnumSlotInlineAdmin(UnusedContentSlotInlineAdmin):
    model = EnumSlot

#-------------------------------------------------------------------------------
def get_enum_type_inline_admin(type):
    try:
        et = EnumType.objects.get(_swim_content_type__title=type)
    except EnumType.DoesNotExist:
        return None
    return {
        'single': SingleEnumSlotInlineAdmin,
        'list': ListEnumSlotInlineAdmin,
        'unused': UnusedEnumSlotInlineAdmin,
        'can_delete': True,
        'model': EnumSlot,
        'storage_model': EnumSlot,
    }
register_content_slot_admin_generator(get_enum_type_inline_admin)
register_model_generates_csm_types(EnumType)

#-------------------------------------------------------------------------------
class ArrangementSlotInlineMixin:
    #---------------------------------------------------------------------------
    def formfield_for_dbfield(self, key, db_field, **kwargs):
        """
        Hide the arrangement drop down.
        """
        if isinstance(db_field, models.ForeignKey) and db_field.attname == "arrangement_id":
            formfield = db_field.formfield(**kwargs)
            formfield.widget = HiddenInput()
            return formfield

        return super(ArrangementSlotInlineMixin, self).formfield_for_dbfield(
                key, db_field, **kwargs)

#-------------------------------------------------------------------------------
class SingleArrangementSlotInlineAdmin(
    ArrangementSlotInlineMixin,
    SingleContentSlotInlineAdmin,
):
    template = "admin/swim_stacked_arrangement.html"
    model = ArrangementSlot
    formset = ArrangementSingleResourceFormSet

#-------------------------------------------------------------------------------
class UnusedArrangementSlotInlineAdmin(UnusedContentSlotInlineAdmin):
    model = ArrangementSlot

#-------------------------------------------------------------------------------
class ListArrangementSlotInlineAdmin(
    ArrangementSlotInlineMixin,
    ListContentSlotInlineAdmin,
):
    template = "admin/swim_stacked_arrangement.html"
    model = ArrangementSlot
    formset = ArrangementListResourceFormSet

#-------------------------------------------------------------------------------
register_content_slot_admin(
    'swim.content.Arrangement',
    single=SingleArrangementSlotInlineAdmin,
    list=ListArrangementSlotInlineAdmin,
    unused=UnusedArrangementSlotInlineAdmin,
    can_delete=True,
    model=Arrangement,
    storage_model=ArrangementSlot,
)

#-------------------------------------------------------------------------------
def get_arrangement_inline_admin(type):
    try:
        at = ArrangementType.objects.get(_swim_content_type__title=type)
    except ArrangementType.DoesNotExist:
        return None
    return {
        'single': SingleArrangementSlotInlineAdmin,
        'list': ListArrangementSlotInlineAdmin,
        'unused': UnusedArrangementSlotInlineAdmin,
        'can_delete': True,
        'model': Arrangement,
        'storage_model': ArrangementSlot,
    }
register_content_slot_admin_generator(get_arrangement_inline_admin)


#-------------------------------------------------------------------------------
class LinkAdminForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(LinkAdminForm, self).__init__(*args, **kwargs)

        # Check to see if the Link URL can be edited
        if Page.objects.filter(ownlink = self.instance.id).count():
            # The readonly attribute is a really bad hack as Django prints out syntatically incorrect
            # HTML readonly="", instead of just readonly
            self.fields.get('url').widget = forms.TextInput(attrs={'readonly':''})
            self.fields.get('url').help_text = 'This URL is locked, to edit it modify the associated page'

    class Meta:
        model = Link
        fields = (
            'title',
            'url',
        )

class LinkAdmin(ModelAdmin):
    form = LinkAdminForm
    save_on_top = True
    list_display = ('url', 'title', 'creationdate', 'modifieddate')
    search_fields = ('url', 'title')

#-------------------------------------------------------------------------------
class MenuLinkInline(admin.TabularInline):
    model = MenuLink
    extra = 5

class MenuAdmin(ModelAdmin):
    save_on_top = True
    list_display = ('title',)
    list_display_links = ('title',)
    inlines = [
        MenuLinkInline,
    ]


#-------------------------------------------------------------------------------
class ArrangementAdminForm(forms.ModelForm):
    class Meta:
        model = Arrangement
        exclude = []

#-------------------------------------------------------------------------------
class ArrangementAdmin(ArrangementModelAdmin):
    form = ArrangementAdminForm


#-------------------------------------------------------------------------------
class PageAdminForm(forms.ModelForm):

    class Meta:
        model = Page
        exclude = []

    # Ensure that the path given doesn't match another page regardless of case
    def clean_path(self):
        path = self.cleaned_data['path']
        path_source_message = ""
        if not path:
            path = '/%s' % slugify(self.cleaned_data.get('title', ''))
            path_source_message = "No path was provided, so a path was "\
                    "generated from the title - %s. " % path

        path = "/%s" % path.strip('/').lower()

        if Page.objects.filter(path=path) \
                .exclude(id = self.instance.id).count():
            raise forms.ValidationError(
                '%sThere already exists a Page with the path of: "%s"' % (
                    path_source_message,
                    path,
                )
            )

        qs = ReservedPath.objects.all()
        if self.instance:
            ct = DjangoContentType.objects.get_for_model(self.instance)
            qs = qs.exclude(object_id=self.instance.pk, django_content_type=ct)

        if qs.filter(path=path, reservation_type='single').count() > 0:
            raise forms.ValidationError(
                "%sThere already exists a resource with the path of: %s." % (
                    path_source_message,
                    path,
                )
            )

        # There are a number of paths that might prevent us from putting a
        # resource here.  For example in the case of '/foo/index/shoo'
        # there could be reservations rooted at /foo, /foo/index, or /foo/index/shoo
        path_parts = path.strip("/").split("/")
        while path_parts:
            new_path = '/%s' % '/'.join(path_parts)
            if qs.filter(path=new_path, reservation_type='tree').count() > 0:
                raise forms.ValidationError(
                    "%sAll paths starting with %s are reserved." % (
                        path_source_message,
                        new_path,
                    )
                )
            path_parts.pop()

        return path

#-------------------------------------------------------------------------------
class PageAdmin(ResourceModelAdmin):
    form = PageAdminForm
    save_on_top = True
    list_display = ('admin_path_display', 'admin_add_child', 'resource_type', 'path')
    list_filter = (
        ('resource_type', admin.RelatedOnlyFieldListFilter),
    )
    search_fields = ('path', 'key', 'title', 'resource_type__title')

    fieldsets = (
        (None, {
            'fields': ('resource_type', 'title', 'path',)
        }),
        SEO_FIELDSET,
    )

    #--------------------------------------------------------------------------
    def admin_path_display(self, obj):
        base, leaf_atom = obj.path.rsplit("/", 1)
        part_length = len([x for x in base.strip("/").split("/") if x])

        base = '/&nbsp;&nbsp;'.join(['---&nbsp;&nbsp;']*part_length)
        return mark_safe(f'''
            <span class="pageSection">{base}</span>/
            <strong class="pageAtom">{obj.title}</strong>
        ''')
    admin_path_display.short_description = 'Page'
    admin_path_display.admin_order_field = 'path'

    #---------------------------------------------------------------------------
    def admin_add_child(self, obj):
        path = obj.path
        if not path.endswith('/'):
            path = path + '/'

        return mark_safe(f'''
            <a href="/admin/content/page/add/?path={path}">Add&nbsp;Child</a>
        ''')
    admin_add_child.short_description = 'Add Child'

    #--------------------------------------------------------------------------
    def admin_title(self, obj):
        base, leaf_atom = obj.path.rsplit("/", 1)
        return mark_safe(obj.title or "untitled")
    admin_title.short_description = 'Title'
    admin_title.admin_order_field = 'title'

#-------------------------------------------------------------------------------
class BasePageSlotInlineAdmin(object):

    #---------------------------------------------------------------------------
    def formfield_for_dbfield(self, db_field, **kwargs):
        """
        Filter the Page choices down by resource type.
        """

        if self.page_type:
            if db_field.name == 'page':
                kwargs.update({
                    'queryset': Page.objects.filter(
                        resource_type=self.page_type.resource_type
                    )
                })

        return ContentSlotInlineAdmin.formfield_for_dbfield(self, db_field, **kwargs)

    #---------------------------------------------------------------------------
    def edit_link(self, obj):
        return mark_safe(f'''
            <a href="/admin/content/page/{obj.page.id}/change/">Edit Page</a>
        ''')


#-------------------------------------------------------------------------------
class SinglePageSlotInlineAdmin(BasePageSlotInlineAdmin, SingleContentSlotInlineAdmin):
    model = PageSlot
    fields = ('page', 'edit_link')
    readonly_fields = ('edit_link', )

    #---------------------------------------------------------------------------
    def __init__(self, *args, page_type=None, **kwargs):
        self.page_type = page_type
        super(SinglePageSlotInlineAdmin, self).__init__(*args, **kwargs)

#-------------------------------------------------------------------------------
class ListPageSlotInlineAdmin(BasePageSlotInlineAdmin, ListContentSlotInlineAdmin):
    model = PageSlot
    fields = ('order', 'page', 'edit_link')
    readonly_fields = ('edit_link', )

    #---------------------------------------------------------------------------
    def __init__(self, *args, page_type=None, **kwargs):
        self.page_type = page_type
        super(ListPageSlotInlineAdmin, self).__init__(*args, **kwargs)

#-------------------------------------------------------------------------------
class UnusedPageSlotInlineAdmin(BasePageSlotInlineAdmin, UnusedContentSlotInlineAdmin):
    model = PageSlot

    #---------------------------------------------------------------------------
    def __init__(self, *args, page_type=None, **kwargs):
        self.page_type = page_type
        super(UnusedPageSlotInlineAdmin, self).__init__(*args, **kwargs)

#-------------------------------------------------------------------------------
register_content_slot_admin(
    'swim.content.Page',
    single=SinglePageSlotInlineAdmin,
    list=ListPageSlotInlineAdmin,
    unused=UnusedPageSlotInlineAdmin,
    can_delete=True,
    model=Page,
    storage_model=PageSlot,
)

#-------------------------------------------------------------------------------
def get_page_type_inline_admin(type_title):
    try:
        page_type = PageType.objects.get(_swim_content_type__title=type_title)
    except PageType.DoesNotExist:
        return None

    return {
        'single': ClassFactory(SinglePageSlotInlineAdmin, page_type=page_type),
        'list': ClassFactory(ListPageSlotInlineAdmin, page_type=page_type),
        'unused': ClassFactory(UnusedPageSlotInlineAdmin, page_type=page_type),
        'can_delete': True,
        'model': Page,
        'storage_model': PageSlot,
    }
register_content_slot_admin_generator(get_page_type_inline_admin)
register_model_generates_csm_types(PageType)


#-------------------------------------------------------------------------------
class PageTypeAdmin(admin.ModelAdmin):
    exclude = ['_swim_content_type',]
    search_fields = (
        'key', 'title',
    )
    list_display = (
        'title', 'key'
    )

#-------------------------------------------------------------------------------
class SiteWideContentAdmin(ResourceModelAdmin):
    save_on_top = True
    list_display = ('__str__',)
    search_fields = ('site__domain', 'site__name', )

# Content Models
admin.site.register(Link, LinkAdmin)
admin.site.register(Menu, MenuAdmin)
admin.site.register(Arrangement, ArrangementAdmin)
admin.site.register(Page, PageAdmin)
admin.site.register(PageType, PageTypeAdmin)
admin.site.register(SiteWideContent, SiteWideContentAdmin)

