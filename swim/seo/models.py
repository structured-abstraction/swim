from django.db import models
from django.conf import settings
from django.dispatch import dispatcher
from swim.core import modelfields
from swim.media.fields import  ImageField

#-------------------------------------------------------------------------------
FREQUENCY_CHOICES = (
    ('always', 'Always'),
    ('hourly', 'Hourly'),
    ('daily', 'Daily'),
    ('weekly', 'Weekly'),
    ('monthly', 'Monthly'),
    ('yearly', 'Yearly'),
    ('never', 'Never'),
)
PRIORITY_CHOICES = [ ( f, '%0.1f' % (f /10.0)) for f in range(11) ]

#-------------------------------------------------------------------------------
class HasSEOAttributes(models.Model):
    """
    Common base class for models which have search engine optimization attributes.
    """

    sitemap_include = models.BooleanField("Include in Sitemap.xml", default=True)

    sitemap_change_frequency = models.CharField("Sitemap: Change Frequency",
        max_length=10,
        choices=FREQUENCY_CHOICES,
        default="yearly",
        help_text = """
<p>How frequently the page is likely to change.
This value provides general information to search engines and may not correlate exactly to how often they crawl the page.</p>
<p>The value "always" should be used to describe documents that change each time they are accessed.
The value "never" should be used to describe archived URLs.</p>

<p>Please note that the value of this tag is considered a hint and not a command.
Even though search engine crawlers consider this information when making decisions,
they may crawl pages marked "hourly" less frequently than that,
and they may crawl pages marked "yearly" more frequently than that.
It is also likely that crawlers will periodically crawl pages marked "never"
so that they can handle unexpected changes to those pages.</p>"""
    )
    sitemap_priority = models.IntegerField("Sitemap: Priority",
        choices=PRIORITY_CHOICES,
        default=5, # Default is 0.5
        help_text = """
<p>The priority of this URL relative to other URLs on your site.
Valid values range from 0.0 to 1.0.
This value has no effect on your pages compared to pages on other sites,
and only lets the search engines know which of your pages you deem most important
so they can order the crawl of your pages in the way you would most like.</p>

<p>The default priority of a page is 0.5.</p>

<p>Please note that the priority you assign to a page has no influence on
the position of your URLs in a search engine's result pages.
Search engines use this information when selecting between URLs on the same
site, so you can use this tag to increase the likelihood that your more important
pages are present in a search index.</p>

<p>Also, please note that assigning a high priority to all of the URLs on
your site will not help you. Since the priority is relative, it is only used
to select between URLs on your site; the priority of your pages will not be
compared to the priority of pages on other sites.</p>"""
    )


    meta_no_follow = models.BooleanField("Meta: No Follow",
            default=False,
            help_text="""
<p><b>Meta Robots No Follow</b>: Request that search engines (robots)
do not follow any links present on this page.
            """
    )

    meta_no_index = models.BooleanField("Meta: No Index",
            default=False,
            help_text="""
<p><b>Meta Robots No Index</b>: Request that search engines (robots)
do not index any of the content on this page.
            """
    )

    meta_title = models.CharField("Meta: Title",
        blank=True,
        null=True,
        max_length=255,
        help_text = """
<p><b>Meta Title</b>: To give a title to the document.</p>

<p>This tag should be used to briefly describe the page. This content will show up on the top of the browser window.</p>
"""
    )

    meta_description = models.TextField("Meta: Description",
        blank=True,
        null=True,
        help_text = """
<p><b>Meta Description</b>: To give a description of the document.</p>

<p>This tag consists of a short, plain language description of the document, usually 20-25 words or less. Search engines that support this tag will use the information to publish on their search results page, normally below the Title of your site.</p>

<p>Example: Citrus fruit wholesaler.</p>

<p><b>Recommendation</b>: Always use this tag. Make your meta description as compelling as you can, as your description often is the difference between getting your listing clicked in the search results. This tag is particularly important if your document has very little text, is a frameset, or has extensive scripts at the top.</p>
"""
    )

    meta_keywords = models.TextField("Meta: Keywords",
        blank=True,
        null=True,
        help_text = """
<p><b>Meta Keywords</b>: To list keywords the define the content of your site.</p>

<p>Keywords are used by search engines to properly index your site in addition to words from the title, document body and other areas. This tag is typically used for synonyms and alternates of title words.</p>

<p>Example: oranges, lemons, limes</p>

<p><b>Recommendation</b>: Use with caution. Make sure to only use keywords that are relevant to your site. Search engines are known to penalize or blacklist your site for abuse. This tag also exposes your keywords to your competitors. Five hours of keyword research can be hijacked within just a few minutes by your competitor.</p>
"""
    )

    facebook_title = models.CharField("Facebook: Title",
        blank=True,
        null=True,
        max_length=255,
        help_text = """
<p><b>Facebook Title</b>: The title of the page when shared on Facebook</p>
"""
    )

    facebook_description = models.TextField("Facebook: Description",
        blank=True,
        null=True,
        help_text = """
<p><b>Facebook Description</b>: To give a description of the document when shared on Facebook.</p>
"""
    )

    facebook_image = ImageField(
        upload_to=settings.SWIM_SEO_FACEBOOK_IMAGE_FOLDER,
        max_length=512,
        blank=True,
        null=True,
        help_text = """
<p><b>Facebook Image</b>: Set an image to use when this document is shared on Facebook.</p>
"""
    )

    #---------------------------------------------------------------------------
    def meta_robot(self):

        # indexing and following is the default, don't bother with the tag
        if not self.meta_no_follow and not self.meta_no_index:
            return ""

        elif self.meta_no_follow and not self.meta_no_index:
            return '<meta name="robots" content="index, nofollow">'

        elif not self.meta_no_follow and self.meta_no_index:
            return '<meta name="robots" content="noindex, follow">'

        elif self.meta_no_follow and self.meta_no_index:
            return '<meta name="robots" content="noindex, nofollow">'


        return "" # This fail case should never actually happen. But meh.

    class Meta:
        abstract = True

