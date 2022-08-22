# Django settings.
import os.path
import sys
import stat

relative_path_to_this_module = os.path.dirname(os.path.abspath(sys.modules[__name__].__file__))
absolute_path_to_project = os.path.abspath(os.path.join(relative_path_to_this_module, '..'))
sys.path = [absolute_path_to_project] + sys.path

DEBUG = False

ADMINS = (
     ('BAZ', 'webmaster@example.com'),
)


MANAGERS = ADMINS

DATABASES = {
    'default': {
        'NAME': os.path.join(absolute_path_to_project, 'database.sqlite3'),
        'ENCODING': 'utf8',
        'ENGINE': 'django.db.backends.sqlite3',
    },
}

# Local time zone for this installation. All choices can be found here:
# http://www.postgresql.org/docs/current/static/datetime-keywords.html#DATETIME-TIMEZONE-SET-TABLE
TIME_ZONE = 'Canada/Mountain'

# Language code for this installation. All choices can be found here:
# http://www.w3.org/TR/REC-html40/struct/dirlang.html#langcodes
# http://blogs.law.harvard.edu/tech/stories/storyReader$15
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = os.path.join(absolute_path_to_project, 'htdocs')
FILE_UPLOAD_PERMISSIONS = stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH

# URL that handles the media served from MEDIA_ROOT.
# Example: "http://media.lawrence.com"
#MEDIA_URL = 'http://swim.dev.structuredabstraction.com/'
MEDIA_URL = 'http://localhost:8000/'

# Ensure that our progress handler is in place.
FILE_UPLOAD_HANDLERS = (
    "django.core.files.uploadhandler.MemoryFileUploadHandler",
    "django.core.files.uploadhandler.TemporaryFileUploadHandler",
)

SECURE_FILE_SECRET = '----------'
SECURE_FILE_EXPIRES = 60  # Number of seconds a secure download file link is valid for
SECURE_FILE_ROOT = os.path.join('content', 'secure')

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/adminmedia/'

PREPEND_WWW = False
APPEND_SLASH = False

# List of callables that know how to import templates from various sources.
TEMPLATES = [
    {
        "BACKEND": "django_jinja.backend.Jinja2",
        "APP_DIRS": True,
        "OPTIONS": {
            "match_extension": None,
            "match_regex": r".*\.jinja\..*",
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.request',
                'swim.context.processor',
            ],
            "globals": {
                "is_subpath_on_path": "swim.core.is_subpath_on_path",
            },
            "loader": "swim.design.loader.jinja2_loader",
        }
    },
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            # This template is necessary for the security app, but that app isn't
            # really used in many places, and I don't like the idea of a PHP template
            # being active by default.
            # os.path.join(absolute_path_to_project, 'swim', 'security', 'templates'),
            os.path.join(absolute_path_to_project, 'swim', 'templates'),
        ],
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.request',
                'swim.context.processor',
            ],
            'loaders': [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
                'swim.design.loader.DjangoStyleLoadDesignTemplate',
            ]
        },
    },
]

MIDDLEWARE = (
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'swim.core.middleware.RequestThreadLocal',
    'swim.middleware.AdminRedirect',
    'swim.security.middleware.EnforceAccessRestriction',
)


SWIM_RUN_MIDDLEWARE = True
SWIM_RUN_RESPONSE_PROCESSOR = True
SWIM_ENABLE_ADMIN = True

SWIM_MIDDLEWARE_MODULES = (
    'swim.membership.swimmiddleware',
    'swim.blog.swimmiddleware',
    'swim.event.swimmiddleware',
)
SWIM_CONTEXT_PROCESSOR_MODULES = (
    'swim.membership.swimresponseprocessor',
)
SWIM_FORM_HANDLER_MODULES = (
    'swim.membership.swimformhandler',
)

SWIM_IMAGE_BACKEND = 'swim.media.image.PILWrapper'

SWIM_SEO_FACEBOOK_IMAGE_FOLDER = 'content/facebook/'

ROOT_URLCONF = 'swim.urls'
DEFAULT_VIEW = 'swim.core.views.default'
DEFAULT_PAGE_VIEW = 'swim.content.views.PageView'

MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'


# When using swimtest skip all of the django tests.
SKIP_TESTS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.messages',
    'django.contrib.sessions',
    'django.contrib.sitemaps',
    'django.contrib.sites',
    #'django.contrib.redirects',
    'django_extensions',
)

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.messages',
    'django.contrib.sessions',
    'django.contrib.sitemaps',
    'django.contrib.sites',
    'django.contrib.staticfiles',
    #'django.contrib.redirects',
    'django_extensions',

    'ckeditor',
    'ckeditor_uploader',
    'django_jinja',

    # The order of these is important and represents the dependencies
    'swim.core',
    'swim.content',
    'swim.media',
    'swim.form',
    'swim.design',
    'swim.redirect',

    # membership depends on swim.form so it must come after it.
    'swim.membership',
    'swim.blog',
    'swim.event',
    'swim.syndication',
    'swim.security',
    'swim.mobile',
    'swim.static',
)

CODEPRESS_ENABLE = False
EDITAREA_JS_NO_AJAX_SAVE_ENABLE = False

EMAIL_HOST = ''
EMAIL_PORT = 0
EMAIL_HOST_PASSWORD = ''
EMAIL_HOST_USER = 'webmaster@example.com'
EMAIL_USE_TLS = True

SERVER_EMAIL = 'webmaster@example.com'
DEFAULT_FROM_EMAIL = 'webmaster@example.com'

TIME_INPUT_FORMATS = (
    '%I:%M %p',     # '2:30 PM'
    '%I:%M%p',     # '2:30PM'
    '%I:%M:%S %p',     # '2:30:59 PM'
    '%I:%M:%S%p',     # '2:30:59PM'
    '%H:%M',        # '14:30'
    '%H:%M:%S',     # '14:30:59'
)

TIME_HELP_STRING = """
Examples: 14:50 or 2:50 PM
"""

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(os.path.dirname(__file__), 'htdocs', 'static')


# Resource JS
DOJO_JS = 'https://ajax.googleapis.com/ajax/libs/dojo/1.4.1/dojo/dojo.xd.js'
EDITAREA_JS = '/static/swim/js/edit_area/edit_area_full.js'
RESOURCE_TEXTAREA_JS = '/static/swim/js/resource_textareas.js'

# CKEDITOR
CKEDITOR_JQUERY_URL = '//ajax.googleapis.com/ajax/libs/jquery/2.1.1/jquery.min.js'
CKEDITOR_CONFIGS = {
    'default': {
        'allowedContent': True,
        'forcePasteAsPlainText': True,
        'pasteFromWordRemoveStyles': True,
        'pasteFromWordRemoveFontStyles': True,
        'pasteFromWordNumberedHeadingToList': True,
        'pasteFromWordPromptCleanup': True,
        'startupOutlineBlocks': True,
        'filebrowserBrowseUrl': '/admin/content/browser/file/',
        'filebrowserImageBrowseLinkUrl': '/admin/content/browser/file/',
        'filebrowserImageBrowseUrl': '/admin/content/browser/image/',
        'filebrowserFlashBrowseUrl': '/admin/content/browser/file/',
        'toolbar': [
            [
                'Format', '-',
                'Bold','Italic','Underline','Strike','-',
                'Subscript','Superscript', '-'
            ],
            ['Link','Unlink','Anchor'],
            ['Cut','Copy','Paste','PasteText','PasteFromWord','-','Print', 'SpellChecker', 'Scayt'],
            ['Undo','Redo','-','Find','Replace','-','SelectAll','RemoveFormat'],
            '/',
            ['NumberedList','BulletedList','-','Outdent','Indent','Blockquote'],
            ['JustifyLeft','JustifyCenter','JustifyRight','JustifyBlock'],
            ['Image','Flash','Table','HorizontalRule','SpecialChar','PageBreak'],
            ['Source', 'Maximize', 'ShowBlocks'],
        ]
    },
    'default_admin': {
        'admin_inline': True,
    },
}
CKEDITOR_IMAGE_BACKEND = 'pillow'
CKEDITOR_IMAGE_QUALITY = 80
CKEDITOR_IMAGE_MAX_SIZE = (600, 600)

# Logging everything from WARNING and above
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
}

# WARNING: Nothing should go after this!
#-------------------------------------------------------------------------------
# Host specific settings.
import socket
hostname = socket.gethostname().replace(".", "_").replace("-", "_")

def import_host_settings(settings_module, host_settings_to_try=None):
    #-------------------------------------------------------------------------------
    # And now try to import the project specific host settings.
    if not host_settings_to_try:
        host_settings_to_try = [
            'swim.host_settings',
        ]

    importing_errors = ''
    found_settings = []
    for host_settings in host_settings_to_try:
        host_settings = host_settings + "." + hostname
        try:
            host_settings_module = __import__(host_settings, globals(), locals(), ['*'])
            override = getattr(host_settings_module, 'override', None)
            if override:
                override(settings_module)
            else:
                for key in host_settings_module.__dict__.keys():
                    if key.startswith('_'): continue
                    settings_module.__dict__[key] = host_settings_module.__dict__[key]
            # TODO: we can't deploy SWIM with prints to stdout using mod_wsgi. :/
            #print "Using host_specific settings from for: %s" % (host_settings,)
            found_settings.append(host_settings)
        except Exception as e:
            import traceback
            importing_errors += "**** Warning: host specific settings (%s) import failed: ****\n" % (
                    host_settings,
                )
            importing_errors += "\t" + host_settings + "\n\t"
            importing_errors += "\n\t".join(traceback.format_exc().split("\n")) + "\n"

    if not found_settings:
        # TODO: we can't deploy SWIM with prints to stdout using mod_wsgi. :/
        sys.stderr.write(importing_errors)
    else:
        SWIM_CRON = os.environ.get('SWIM_CRON')
        if not SWIM_CRON or SWIM_CRON == '0':
            message = "Using: %s\n" % ", ".join(found_settings)
            sys.stderr.write(message)
