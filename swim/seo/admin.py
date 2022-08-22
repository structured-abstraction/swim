"""
SWIM's Search Engine Optimization app's administration setup.
"""
from django.contrib import admin

# The only thing we actually need to provide is a re-usable fieldset
# for the SEO_FIELDSET

SEO_FIELDSET = ('Search Engine Optimization Options', {
    'classes': ('collapse',),
    'fields': (
        'sitemap_include',
        'sitemap_change_frequency',
        'sitemap_priority',
        'meta_no_follow',
        'meta_no_index',
        'meta_title',
        'meta_keywords',
        'meta_description',
        'facebook_title',
        'facebook_description',
        'facebook_image',
    ),
})

