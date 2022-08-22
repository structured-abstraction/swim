# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import swim.media.fields
import swim.blog.models
import swim.core.modelfields
import swim.core.models


class Migration(migrations.Migration):

    dependencies = [
        ('membership', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Blog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('creationdate', models.DateTimeField(auto_now_add=True)),
                ('modifieddate', models.DateTimeField(auto_now=True)),
                ('sitemap_include', models.BooleanField(default=True, verbose_name='Include in Sitemap.xml')),
                ('sitemap_change_frequency', models.CharField(default='yearly', help_text='\n<p>How frequently the page is likely to change.\nThis value provides general information to search engines and may not correlate exactly to how often they crawl the page.</p>\n<p>The value "always" should be used to describe documents that change each time they are accessed.\nThe value "never" should be used to describe archived URLs.</p>\n\n<p>Please note that the value of this tag is considered a hint and not a command.\nEven though search engine crawlers consider this information when making decisions,\nthey may crawl pages marked "hourly" less frequently than that,\nand they may crawl pages marked "yearly" more frequently than that.\nIt is also likely that crawlers will periodically crawl pages marked "never"\nso that they can handle unexpected changes to those pages.</p>', max_length=10, verbose_name='Sitemap: Change Frequency', choices=[('always', 'Always'), ('hourly', 'Hourly'), ('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly'), ('yearly', 'Yearly'), ('never', 'Never')])),
                ('sitemap_priority', models.IntegerField(default=5, help_text="\n<p>The priority of this URL relative to other URLs on your site.\nValid values range from 0.0 to 1.0.\nThis value has no effect on your pages compared to pages on other sites,\nand only lets the search engines know which of your pages you deem most important\nso they can order the crawl of your pages in the way you would most like.</p>\n\n<p>The default priority of a page is 0.5.</p>\n\n<p>Please note that the priority you assign to a page has no influence on\nthe position of your URLs in a search engine's result pages.\nSearch engines use this information when selecting between URLs on the same\nsite, so you can use this tag to increase the likelihood that your more important\npages are present in a search index.</p>\n\n<p>Also, please note that assigning a high priority to all of the URLs on\nyour site will not help you. Since the priority is relative, it is only used\nto select between URLs on your site; the priority of your pages will not be\ncompared to the priority of pages on other sites.</p>", verbose_name='Sitemap: Priority', choices=[(0, '0.0'), (1, '0.1'), (2, '0.2'), (3, '0.3'), (4, '0.4'), (5, '0.5'), (6, '0.6'), (7, '0.7'), (8, '0.8'), (9, '0.9'), (10, '1.0')])),
                ('meta_no_follow', models.BooleanField(default=False, help_text='\n<p><b>Meta Robots No Follow</b>: Request that search engines (robots)\ndo not follow any links present on this page.\n            ', verbose_name='Meta: No Follow')),
                ('meta_no_index', models.BooleanField(default=False, help_text='\n<p><b>Meta Robots No Index</b>: Request that search engines (robots)\ndo not index any of the content on this page.\n            ', verbose_name='Meta: No Index')),
                ('meta_title', models.CharField(help_text='\n<p><b>Meta Title</b>: To give a title to the document.</p>\n\n<p>This tag should be used to briefly describe the page. This content will show up on the top of the browser window.</p>\n', max_length=255, null=True, verbose_name='Meta: Title', blank=True)),
                ('meta_description', models.TextField(help_text='\n<p><b>Meta Description</b>: To give a description of the document.</p>\n\n<p>This tag consists of a short, plain language description of the document, usually 20-25 words or less. Search engines that support this tag will use the information to publish on their search results page, normally below the Title of your site.</p>\n\n<p>Example: Citrus fruit wholesaler.</p>\n\n<p><b>Recommendation</b>: Always use this tag. Make your meta description as compelling as you can, as your description often is the difference between getting your listing clicked in the search results. This tag is particularly important if your document has very little text, is a frameset, or has extensive scripts at the top.</p>\n', null=True, verbose_name='Meta: Description', blank=True)),
                ('meta_keywords', models.TextField(help_text='\n<p><b>Meta Keywords</b>: To list keywords the define the content of your site.</p>\n\n<p>Keywords are used by search engines to properly index your site in addition to words from the title, document body and other areas. This tag is typically used for synonyms and alternates of title words.</p>\n\n<p>Example: oranges, lemons, limes</p>\n\n<p><b>Recommendation</b>: Use with caution. Make sure to only use keywords that are relevant to your site. Search engines are known to penalize or blacklist your site for abuse. This tag also exposes your keywords to your competitors. Five hours of keyword research can be hijacked within just a few minutes by your competitor.</p>\n', null=True, verbose_name='Meta: Keywords', blank=True)),
                ('facebook_title', models.CharField(help_text='\n<p><b>Facebook Title</b>: The title of the page when shared on Facebook</p>\n', max_length=255, null=True, verbose_name='Facebook: Title', blank=True)),
                ('facebook_description', models.TextField(help_text='\n<p><b>Facebook Description</b>: To give a description of the document when shared on Facebook.</p>\n', null=True, verbose_name='Facebook: Description', blank=True)),
                ('facebook_image', swim.media.fields.ImageField(help_text='\n<p><b>Facebook Image</b>: Set an image to use when this document is shared on Facebook.</p>\n', max_length=512, null=True, upload_to='content/facebook/', blank=True)),
                ('title', models.CharField(max_length=200)),
                ('path', swim.core.modelfields.Path(max_length=255)),
                ('key', swim.core.modelfields.Key(unique=True, max_length=200)),
            ],
            options={
                'ordering': ('path',),
            },
            bases=(swim.blog.models.ActsLikeTimeline, models.Model, swim.core.models.ClassIsContentType, swim.blog.models.HasPublishedTimeline),
        ),
        migrations.CreateModel(
            name='BlogDay',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('creationdate', models.DateTimeField(auto_now_add=True)),
                ('modifieddate', models.DateTimeField(auto_now=True)),
                ('day', models.IntegerField()),
            ],
            options={
                'abstract': False,
            },
            bases=(swim.blog.models.ActsLikeTimeline, models.Model, swim.core.models.ClassIsContentType, swim.blog.models.HasPublishedTimeline),
        ),
        migrations.CreateModel(
            name='BlogMonth',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('creationdate', models.DateTimeField(auto_now_add=True)),
                ('modifieddate', models.DateTimeField(auto_now=True)),
                ('month', models.IntegerField()),
            ],
            options={
                'abstract': False,
            },
            bases=(swim.blog.models.ActsLikeTimeline, models.Model, swim.core.models.ClassIsContentType, swim.blog.models.HasPublishedTimeline),
        ),
        migrations.CreateModel(
            name='BlogYear',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('creationdate', models.DateTimeField(auto_now_add=True)),
                ('modifieddate', models.DateTimeField(auto_now=True)),
                ('year', models.IntegerField()),
            ],
            options={
                'abstract': False,
            },
            bases=(swim.blog.models.ActsLikeTimeline, models.Model, swim.core.models.ClassIsContentType, swim.blog.models.HasPublishedTimeline),
        ),
        migrations.CreateModel(
            name='Post',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('creationdate', models.DateTimeField(auto_now_add=True)),
                ('modifieddate', models.DateTimeField(auto_now=True)),
                ('publish_date', models.DateField()),
                ('publish_time', models.TimeField()),
                ('publish_timestamp', models.DateTimeField(null=True, editable=False, blank=True)),
                ('sitemap_include', models.BooleanField(default=True, verbose_name='Include in Sitemap.xml')),
                ('sitemap_change_frequency', models.CharField(default='yearly', help_text='\n<p>How frequently the page is likely to change.\nThis value provides general information to search engines and may not correlate exactly to how often they crawl the page.</p>\n<p>The value "always" should be used to describe documents that change each time they are accessed.\nThe value "never" should be used to describe archived URLs.</p>\n\n<p>Please note that the value of this tag is considered a hint and not a command.\nEven though search engine crawlers consider this information when making decisions,\nthey may crawl pages marked "hourly" less frequently than that,\nand they may crawl pages marked "yearly" more frequently than that.\nIt is also likely that crawlers will periodically crawl pages marked "never"\nso that they can handle unexpected changes to those pages.</p>', max_length=10, verbose_name='Sitemap: Change Frequency', choices=[('always', 'Always'), ('hourly', 'Hourly'), ('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly'), ('yearly', 'Yearly'), ('never', 'Never')])),
                ('sitemap_priority', models.IntegerField(default=5, help_text="\n<p>The priority of this URL relative to other URLs on your site.\nValid values range from 0.0 to 1.0.\nThis value has no effect on your pages compared to pages on other sites,\nand only lets the search engines know which of your pages you deem most important\nso they can order the crawl of your pages in the way you would most like.</p>\n\n<p>The default priority of a page is 0.5.</p>\n\n<p>Please note that the priority you assign to a page has no influence on\nthe position of your URLs in a search engine's result pages.\nSearch engines use this information when selecting between URLs on the same\nsite, so you can use this tag to increase the likelihood that your more important\npages are present in a search index.</p>\n\n<p>Also, please note that assigning a high priority to all of the URLs on\nyour site will not help you. Since the priority is relative, it is only used\nto select between URLs on your site; the priority of your pages will not be\ncompared to the priority of pages on other sites.</p>", verbose_name='Sitemap: Priority', choices=[(0, '0.0'), (1, '0.1'), (2, '0.2'), (3, '0.3'), (4, '0.4'), (5, '0.5'), (6, '0.6'), (7, '0.7'), (8, '0.8'), (9, '0.9'), (10, '1.0')])),
                ('meta_no_follow', models.BooleanField(default=False, help_text='\n<p><b>Meta Robots No Follow</b>: Request that search engines (robots)\ndo not follow any links present on this page.\n            ', verbose_name='Meta: No Follow')),
                ('meta_no_index', models.BooleanField(default=False, help_text='\n<p><b>Meta Robots No Index</b>: Request that search engines (robots)\ndo not index any of the content on this page.\n            ', verbose_name='Meta: No Index')),
                ('meta_title', models.CharField(help_text='\n<p><b>Meta Title</b>: To give a title to the document.</p>\n\n<p>This tag should be used to briefly describe the page. This content will show up on the top of the browser window.</p>\n', max_length=255, null=True, verbose_name='Meta: Title', blank=True)),
                ('meta_description', models.TextField(help_text='\n<p><b>Meta Description</b>: To give a description of the document.</p>\n\n<p>This tag consists of a short, plain language description of the document, usually 20-25 words or less. Search engines that support this tag will use the information to publish on their search results page, normally below the Title of your site.</p>\n\n<p>Example: Citrus fruit wholesaler.</p>\n\n<p><b>Recommendation</b>: Always use this tag. Make your meta description as compelling as you can, as your description often is the difference between getting your listing clicked in the search results. This tag is particularly important if your document has very little text, is a frameset, or has extensive scripts at the top.</p>\n', null=True, verbose_name='Meta: Description', blank=True)),
                ('meta_keywords', models.TextField(help_text='\n<p><b>Meta Keywords</b>: To list keywords the define the content of your site.</p>\n\n<p>Keywords are used by search engines to properly index your site in addition to words from the title, document body and other areas. This tag is typically used for synonyms and alternates of title words.</p>\n\n<p>Example: oranges, lemons, limes</p>\n\n<p><b>Recommendation</b>: Use with caution. Make sure to only use keywords that are relevant to your site. Search engines are known to penalize or blacklist your site for abuse. This tag also exposes your keywords to your competitors. Five hours of keyword research can be hijacked within just a few minutes by your competitor.</p>\n', null=True, verbose_name='Meta: Keywords', blank=True)),
                ('facebook_title', models.CharField(help_text='\n<p><b>Facebook Title</b>: The title of the page when shared on Facebook</p>\n', max_length=255, null=True, verbose_name='Facebook: Title', blank=True)),
                ('facebook_description', models.TextField(help_text='\n<p><b>Facebook Description</b>: To give a description of the document when shared on Facebook.</p>\n', null=True, verbose_name='Facebook: Description', blank=True)),
                ('facebook_image', swim.media.fields.ImageField(help_text='\n<p><b>Facebook Image</b>: Set an image to use when this document is shared on Facebook.</p>\n', max_length=512, null=True, upload_to='content/facebook/', blank=True)),
                ('blog_path', swim.core.modelfields.Path(max_length=255)),
                ('title', models.CharField(max_length=200)),
                ('name', models.SlugField(null=True, max_length=200, blank=True, help_text='This will automatically be set from the title.', unique=True, verbose_name='Path Atom')),
                ('blog', models.ForeignKey(related_name='posts', to='blog.Blog', on_delete=models.CASCADE)),
                ('blogger', models.ForeignKey(related_name='blogs', to='membership.Member', on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ['-publish_date'],
                'verbose_name': 'Blog Post',
                'verbose_name_plural': 'Blog Posts',
            },
            bases=(models.Model, swim.core.models.ClassIsContentType),
        ),
    ]
