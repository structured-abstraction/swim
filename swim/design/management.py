from django.db import IntegrityError

from swim.core import signals
from swim.core.models import (
    Resource,
    ResourceType,
)
from swim.design import models
from swim.design.models import Template
from swim.media.models import Image, File
from swim.content.models import (
    CopySlot,
    Page,
    Link,
    Menu,
    Arrangement,
)
from swim.design.models import (
    ResourceTypeTemplateMapping,
)

#-------------------------------------------------------------------------------
_404_BODY = '<html><body><p>{{ message_404|safe }}</p></body></html>'

#-------------------------------------------------------------------------------
_500_BODY = """
<html><body><p>
An internal server error occured.  The administrators have been informed.
</p></body></html>
"""

#-------------------------------------------------------------------------------
COPY_BODY = """
{% load swim_tags %}
{% editobject target %}
    <div class="copy copy_{{ target.id }}">
    {{ target.body|safe }}
    </div>
{% endeditobject %}
"""

#-------------------------------------------------------------------------------
IMAGE_BODY = """
{% load swim_tags %}
{% editobject target %}
    <div class="image image_{{ target.id }}">
    <img src="{{ target.url }}" alt="{{ target.alt }}" />
    </div>
{% endeditobject %}
"""

#-------------------------------------------------------------------------------
FILE_BODY = """
{% load swim_tags %}
{% editobject target %}
    <div class="file file_{{ target.id }}">
    <a href="{{ target.url }}">{{ target.filename }}</a>
    </div>
{% endeditobject %}
"""

#-------------------------------------------------------------------------------
LINK_BODY = """
{% load swim_tags %}
{% editobject target %}
    <div class="link link_{{ target.id }}">
    <a href="{{ target.url }}" alt="{{ target.alt }}">{{ target.title }}</a>
    </div>
{% endeditobject %}
"""

#-------------------------------------------------------------------------------
# TODO: This doesn't use our fancy new template tag, why not?
MENU_BODY = """
{% load swim_tags %}
{% editobject target %}
    <ul>
    {% for link in target.links %}
    {% if resource.get_absolute_url == link.url %}
    <strong>
    <li>{% render link %}</li>
    </strong>
    {% else %}
    <li>{% render link %}</li>
    {% endif %}
    {% endfor %}
    </ul>
{% endeditobject %}
"""




#-------------------------------------------------------------------------------
ARRANGEMENT_BODY = """
{% load swim_tags %}
{% for copy in target.copy_list %}
<p>{% render copy %}</p>
{% endfor %}
{% for image in target.image_list %}
{% render image %}
{% endfor %}
{% for file in target.file_list %}
{% render file %}
{% endfor %}
{% for menu in target.menu_list %}
{% render menu }}
{% endfor %}
{% for gallery in target.gallery_list %}
{% render gallery %}
{% endfor %}
{% for arrangement in target.arrangement_list %}
{% render arrangement %}
{% endfor %}
"""

#-------------------------------------------------------------------------------
DEFAULT_BASE_TEMPLATE = """
{% load swim_tags %}
<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01//EN"
   "http://www.w3.org/TR/html4/strict.dtd">

<html lang="en">{% block html %}
<head>{% block head %}
    {# TODO: make the content type dynamic #}
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
	<title>{% block head-title %}{{ resource.title }}{% endblock head-title %}</title>


    {% block head-default-css %}
        <!-- BLUEPRINT CSS -->
        <link rel="stylesheet" href="/static/swim/css/blueprint/screen.css" type="text/css" media="screen, projection">
        <link rel="stylesheet" href="/static/swim/css/blueprint/print.css" type="text/css" media="print">
        <!--[if IE]><link rel="stylesheet" href="/static/swim/css/blueprint/ie.css" type="text/css" media="screen, projection"><![endif]-->
        <link rel="stylesheet" href="/static/swim/css/blueprint/plugins/fancy-type/screen.css" type="text/css" media="screen, projection">


        <!-- SWIM DEFAULT CSS -->
        <link rel="stylesheet" href="/static/swim/css/default.css" type="text/css" media="screen, projection">
    {% endblock head-default-css %}

    <!-- SWFOBJECT -->
    <script type="text/javascript" src="/static/swim/js/swfobject.js"></script>

    {% block head-admin-js %}
        <script type="text/javascript" src="http://ajax.googleapis.com/ajax/libs/dojo/1.1.1/dojo/dojo.xd.js">
        </script>
        <script type="text/javascript" src="/static/swim/js/frontend-admin.js"></script>
        {% if request.user.is_authenticated and request.user.is_staff %}
            <!-- SWIM FRONT-END-ADMIN JS -->
            <script type="text/javascript" src="/static/swim/js/aiki.js"></script>
            <script type="text/javascript">
                dojo.addOnLoad(function() {
                    swim_createAdminBar(false, false);
                });
            </script>
            {% if messages %}
                <script type="text/javascript">
                    dojo.addOnLoad(function() {
                        var smoke = new aiki.Smoke();
                        {% for message in messages %}
                            smoke.show({
                                image: "/static/swim/images/aiki.png",
                                title: "",
                                text: "{{message}}",
                                gravity: "topleft",
                                edge: 75
                            });
                        {% endfor %}
                    });
                </script>
            {% endif %}
        {% endif %}
    {% endblock head-admin-js %}
{% endblock head %}</head>
<body>{% block body %}

    {% block container-container %}
        <div class="container">{% block container %}
            {% block logo-container %}
                <div id="logo">
                    {% if not content.images.site_logo %}
                        <img alt="Structured Abstraction" src="/static/swim/images/sa-logo.png"/>
                    {% else %}
                        {% render content.images.site_logo %}
                    {% endif %}
                </div>
            {% endblock logo-container %}

            <hr class="space">
            {% block content-container %}
                <div class="span-15 prepend-1 colborder">
                    {% block header-container %}
                        {% if resource.copy.header %}
                            <h3 class="top alt">{% block header %}{% render resource.copy.header %}{% endblock header %}</h3>
                        {% endif %}
                    {% endblock header-container %}
                    {% block content %}
                        {% render resource.copy.body %}
                    {% endblock content %}
                </div>
                {% block sidebar-container %}
                    <div class="span-7 last">
                        {% block side-bar %}
                            {% block menu %}
                                <h3>A <span class="alt">Simple</span> Navigation</h3>
                                    {% render content.menu.site_nav %}
                                {% if resource.menu.submenu %}
                                    <h5>Submenu</h5>
                                    {% render resource.menu.submenu %}
                                {% endif %}
                            {% endblock menu %}
                            {% block file-list %}
                                {% if resource.file.file_list %}
                                    <h5>Documents</h5>
                                    {% render resource.file.file_list %}
                                {% endif %}
                            {% endblock file-list %}
                        {% endblock side-bar %}
                    </div>
                {% endblock sidebar-container %}
                <hr class="space">
                <hr>
            {% endblock content-container %}
            {% block footer-container %}
                <div class="span-22 prepend-1 append-1">
                    {% if resource.copy.footer %}
                        <h2 class="bottom alt">{% block footer %}{% render resource.copy.footer %}{% endblock %}</h2>
                    {% endif %}
                </div>
            {% endblock footer-container %}

        {% block credits %}
            <div class="span-22 prepend-1 append-1" id="credits">
                <div>
                    <span class="bug">Designed by
                        <a href="http://www.structuredabstraction.com/" target="_blank">
                            <b>Structured Abstraction</b>
                        </a>
                    </span>
                    {% if content.copy.copyright %}
                        {% render content.copy.copyright %}
                    {% endif %}
                </div>
            </div>
        {% endblock credits %}
        {% endblock container%}</div>
    {% endblock container-container %}
    {% block end-javascript %}
            {% if not content.images.site_logo %}
                <script type="text/javascript">
                        var flashVars={dotsPath:'/static/swim/files/sa-logo-dots.txt'};
                                        var params = {wmode: "transparent"}
                        swfobject.embedSWF("/static/swim/files/SALogo.swf", "logo", "950", "254", "9.0.0", '/static/swim/files/expressInstall.swf', flashVars, params);
                </script>
            {% endif %}
    {% endblock end-javascript %}
{% endblock body %}</body>
{% endblock html %}</html>
"""


#-------------------------------------------------------------------------------
def create_default_system_templates(**kwargs):
    """Inserts the System Templates that come with SWIM.
    """

    #---------------------------------------------------------------------------
    HTTP_CONTENT_TYPE = 'text/html; charset=utf-8'

    #---------------------------------------------------------------------------
    # The following definitions MUST not be run at the module level otherwise
    # they'll cause an IntegrityError because the database won't have been
    # created yet.
    RESOURCE_SCO = Resource.swim_content_type()
    PAGE_SCO = Page.swim_content_type()
    COPY_SCO = CopySlot.swim_content_type()
    IMAGE_SCO = Image.swim_content_type()
    FILE_SCO = File.swim_content_type()
    LINK_SCO = Link.swim_content_type()
    MENU_SCO = Menu.swim_content_type()
    ARRANGEMENT_SCO = Arrangement.swim_content_type()

    #---------------------------------------------------------------------------
    DEFAULT_PAGE_TYPE = ResourceType.objects.get(key='default')
    _404_PAGE_TYPE = ResourceType.objects.get(title='404 Not Found')
    _500_PAGE_TYPE = ResourceType.objects.get(title='500 Internal Server Error')

    #---------------------------------------------------------------------------
    SYSTEM_TEMPLATES = (
        #(path, http_content_type, swim_content_type, body, resource_type)
        ('/system/default/404',
            HTTP_CONTENT_TYPE, RESOURCE_SCO, _404_BODY, _404_PAGE_TYPE),
        ('/system/default/500',
            HTTP_CONTENT_TYPE, RESOURCE_SCO, _500_BODY, _500_PAGE_TYPE),
        ('/system/default/copy',
            HTTP_CONTENT_TYPE, COPY_SCO, COPY_BODY, DEFAULT_PAGE_TYPE),
        ('/system/default/image',
            HTTP_CONTENT_TYPE, IMAGE_SCO, IMAGE_BODY, DEFAULT_PAGE_TYPE),
        ('/system/default/file',
            HTTP_CONTENT_TYPE, FILE_SCO, FILE_BODY, DEFAULT_PAGE_TYPE),
        ('/system/default/link',
            HTTP_CONTENT_TYPE, LINK_SCO, LINK_BODY, DEFAULT_PAGE_TYPE),
        ('/system/default/menu',
            HTTP_CONTENT_TYPE, MENU_SCO, MENU_BODY, DEFAULT_PAGE_TYPE),
        ('/system/default/arrangement',
            HTTP_CONTENT_TYPE, ARRANGEMENT_SCO, ARRANGEMENT_BODY, DEFAULT_PAGE_TYPE),
        ('/system/default/base',
            HTTP_CONTENT_TYPE, RESOURCE_SCO, DEFAULT_BASE_TEMPLATE, DEFAULT_PAGE_TYPE),
    )

    for path, http_content_type, swim_content_type, body, resource_type in SYSTEM_TEMPLATES:
        template, created = Template.objects.get_or_create(
            path = path,
            http_content_type = http_content_type,
            swim_content_type = swim_content_type
        )

        if created:
            template.body = body
            template.save()

        ResourceTypeTemplateMapping.objects.get_or_create(
            resource_type=resource_type,
            template=template
        )



signals.initialswimdata.connect(create_default_system_templates)

