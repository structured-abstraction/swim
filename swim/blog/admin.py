
import datetime

from django.conf import settings
from django.contrib import admin
from django import forms
from django.urls import reverse
from django.utils import timezone, safestring

from swim.django_admin import ResourceModelAdmin
from swim.core.models import ResourceType, ReservedPath
from swim.blog.models import Post, Tag, Blog
from swim.content.models import Page
from swim.seo.admin import SEO_FIELDSET


#-------------------------------------------------------------------------------
class PostAdminForm(forms.ModelForm):

    blog = forms.ModelChoiceField(queryset=Blog.objects.all())

    #---------------------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        super(PostAdminForm, self).__init__(*args, **kwargs)

        instance = kwargs.get('instance')
        self.fields['tags'].queryset = Tag.objects.none()
        if instance and instance.blog:
            self.fields['tags'].queryset = Tag.objects.filter(blog=instance.blog)

    #---------------------------------------------------------------------------
    class Meta:
        model = Post
        exclude = []


#-------------------------------------------------------------------------------
class PublishedFilter(admin.filters.SimpleListFilter):

    title = 'Published'
    parameter_name = 'published_date'

    #---------------------------------------------------------------------------
    def lookups(self, request, model_admin):
        return (
            ('1', 'Published'),
            ('0', 'Draft'),
        )

    #---------------------------------------------------------------------------
    def queryset(self, request, queryset):
        if self.value() == '1':
            queryset = queryset.filter(publish_date__isnull=False)
        elif self.value() == '0':
            queryset = queryset.filter(publish_date__isnull=True)
        return queryset


#-------------------------------------------------------------------------------
class PostAdmin(ResourceModelAdmin):
    form = PostAdminForm
    save_on_top = True
    list_display = (
        'title', 'url',
        'publish_date', 'creationdate', 'modifieddate',
        'blog', 'tag_list',
    )
    list_filter = ('tags', 'blog', PublishedFilter)
    prepopulated_fields = {"name": ("title",)}
    filter_horizontal = ('tags', )

    fieldsets = (
        (None, {
            'fields': (
                'resource_type',
                'blog',
                'title',
                'publish_date',
                'publish_time',
            ),
        }),
        ('Tags', {
            'classes': ('collapse',),
            'fields': ('tags',),
        }),
        ('Linking options', {
            'classes': ('collapse',),
            'fields': ('name', )
        }),
        SEO_FIELDSET,
    )
    inlines = []

    #---------------------------------------------------------------------------
    def tag_list(self, obj):
        return ', '.join([str(x) for x in obj.tags.all()])

admin.site.register(Post, PostAdmin)

#-------------------------------------------------------------------------------
class TagAdmin(ResourceModelAdmin):
    fields = ('resource_type', 'blog', 'order', 'title')
    list_display = ('title', 'blog', 'order', 'admin_posts_link', 'admin_url_link')
    list_filter = ('blog', )

    #---------------------------------------------------------------------------
    def admin_url_link(self, obj):
        url = obj.url()
        return safestring.mark_safe(f'<a href="{url}">{url}</a>')
    admin_url_link.short_description = 'View on site'

    #---------------------------------------------------------------------------
    def admin_posts_link(self, obj):
        url = '{}?tags__id__exact={}'.format(
            reverse('admin:blog_post_changelist'),
            obj.id
        )
        return safestring.mark_safe(f'<a href="{url}">Edit Posts</a>')
    admin_posts_link.short_description = 'Posts'

admin.site.register(Tag, TagAdmin)


#-------------------------------------------------------------------------------
class BlogAdminForm(forms.ModelForm):

    class Meta:
        model = Blog
        exclude = []

#-------------------------------------------------------------------------------
class BlogAdmin(ResourceModelAdmin):
    form = BlogAdminForm
    save_on_top = True
    list_display = ('__str__', 'resource_type')

    fieldsets = (
        (None, {
            'fields': ('resource_type', 'path', 'title',)
        }),
        SEO_FIELDSET,
        ('Advanced Path Options', {
            'classes': ('collapse',),
            'fields': ('key', )
        }),
    )


    inlines = []

admin.site.register(Blog, BlogAdmin)
