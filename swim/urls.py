import os.path
import sys

from django.conf import settings
from django.urls import re_path, include

from django.contrib.sitemaps.views import sitemap
from django.contrib import admin
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.sitemaps.views import sitemap
from django.utils.module_loading import import_string
import django.views.static
from django.urls import path

from swim.seo import sitemaps
from swim.django_admin import *
from swim.core import views as core_views
from swim.media import views as media_views
from swim.security import views as security_views

relative_path_to_this_module = os.path.dirname(os.path.abspath(sys.modules[__name__].__file__))
absolute_path_to_project = os.path.abspath(relative_path_to_this_module)

# admin rules
#(r'^r/', include( 'django.conf.urls.shortcut' )),
admin_rule = path('admin/', admin.site.urls)
admin_redirect_rule = re_path('^admin$', core_views.admin_redirect)
admin_ff_bug_rule = re_path(r'^admin/.+/.+/(img/admin/.*\.gif)/', core_views.firefox_35_tinymce_bug_view)

# FIXME: serving static content through django is inefficient.
# For instruction on serving static content see:
# http://www.djangoproject.com/documentation/modpython/#serving-media-files
static_content_rule = re_path(r'^(.*\.\w+)$', django.views.static.serve, {'document_root': settings.MEDIA_ROOT})

sitemaps_rule = re_path(r'^sitemap\.xml$', sitemap, {'sitemaps': sitemaps.sitemap_dict})
default_view = import_string(settings.DEFAULT_VIEW)
default_rule = re_path(r'^.*$', default_view)
css_rule = re_path(r'^css/(?P<path>.*)$', core_views.css)
javascript_rule = re_path(r'^js/(?P<path>.*)$', core_views.javascript)
admin_image_thumb = re_path(r'^admin/content/image/(?P<image_id>\d+)/thumb$', media_views.image_thumb, name='swim.media.views.image_thumb')
admin_browser = re_path(r'^admin/content/browser/$', media_views.browser, name='swim.media.views.browser')
admin_image_upload = re_path(r'^admin/content/browser/image/upload$', media_views.image_upload, name='swim.media.views.image_upload')
admin_image_browser = re_path(r'^admin/content/browser/image/$', media_views.image_browser, name='swim.media.views.image_browser')
admin_image_folder_browser = re_path(r'^admin/content/browser/image/(?P<folder_id>\d+)$', media_views.image_browser, name='swim.media.views.image_browser')
admin_image_view = re_path(r'^admin/content/browser/image/variants/(?P<image_id>\d+)$', media_views.image_view, name='swim.media.views.image_view')

admin_file_upload = re_path(r'^admin/content/browser/file/upload$', media_views.file_upload, name='swim.media.views.file_upload')
admin_file_browser = re_path(r'^admin/content/browser/file/$', media_views.file_browser, name='swim.media.views.file_browser')
admin_file_folder_browser = re_path(r'^admin/content/browser/file/(?P<folder_id>\d+)$', media_views.file_browser, name='swim.media.views.file_browser')
secure_file_rule = re_path(r'^securedownload/(?P<file_id>.*)$', security_views.secure_file_download)

if not getattr(settings, 'SWIM_DISABLE_404', False):
    handler404 = 'swim.content.views.view404'
if not getattr(settings, 'SWIM_DISABLE_500', False):
    handler500 = 'swim.content.views.view500'

pattern_set_without_default = (
    sitemaps_rule, # Sitemaps rule _MUST_ go before static content rule.
)
if settings.SWIM_ENABLE_ADMIN:
    pattern_set_without_default = pattern_set_without_default + (
        admin_ff_bug_rule,
        admin_browser,
        admin_image_upload,
        admin_image_thumb,
        admin_image_browser,
        admin_image_view,
        admin_image_folder_browser,
        admin_file_upload,
        admin_file_browser,
        admin_file_folder_browser,
        admin_rule,
        admin_redirect_rule,
    )
if settings.DEBUG:
    pattern_set_without_default = pattern_set_without_default + (
        static_content_rule,
    )
pattern_set_without_default = pattern_set_without_default + (
    secure_file_rule,
    css_rule,
    javascript_rule,
    re_path(r'^ckeditor/upload/', staff_member_required(views.upload), name='ckeditor_upload'),
    re_path(r'^ckeditor/', include('ckeditor_uploader.urls')),
)
pattern_set = pattern_set_without_default + (
    default_rule,
)
urlpatterns = pattern_set

