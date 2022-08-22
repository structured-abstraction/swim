from datetime import datetime, date, time
from django.conf import settings
from django.utils import timezone
from django.db import models
from django.template.defaultfilters import slugify
from django.db.models.signals import post_save

from swim.core import modelfields, string_to_key, WithRelated
from swim.core.models import (
    RequestHandler,
    RequestHandlerMapping,
    Resource,
    ResourceType,
)
from swim.content.models import LinkResource, Page
from swim.core.content import register_content_object
from swim.chronology import Timeline, get_now
from swim.chronology.models import PublishedInstant, PublishedItemsManager
from swim.seo.models import HasSEOAttributes


#-------------------------------------------------------------------------------
class ActsLikeTimeline:
    """
    Mixin that allows an object to act like a given timeline.

    Override the get_timeline method - and provide a different timeline.
    """
    #--------------------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        super(ActsLikeTimeline, self).__init__(*args, **kwargs)
        self.timeline = self.get_timeline()

    #--------------------------------------------------------------------------
    def get_timeline(self):
        return Timeline(
            self.post_list.order_by('publish_timestamp'),
            'publish_timestamp',
            'publish_timestamp',
            'resource_type',
        )


#-------------------------------------------------------------------------------
class HasPublishedTimeline:
    """
    Mixin that provides a published_timeline property
    """

    #--------------------------------------------------------------------------
    def get_published_timeline(self):
        """
        Returns a published post timeline.
        """

        now = get_now()

        return Timeline(
            self.post_list.filter(
                    publish_timestamp__lte=now,
                ).order_by('-publish_timestamp'),
            'publish_timestamp',
            'publish_timestamp',
            'resource_type',
        )
    published_timeline = property(get_published_timeline)


#-------------------------------------------------------------------------------
class Blog(ActsLikeTimeline, LinkResource, HasPublishedTimeline):
    """
    A blog has a path, and title and is a resource.
    """
    path = modelfields.Path()
    key = modelfields.Key(max_length=200, editable=True, unique=True, blank=True)

    #--------------------------------------------------------------------------
    def get_parent(self):
        """
        A reference to the page who's path is the direct ancestor to this blog.

        returns:
            a reference to the parent page.
        """
        base, leaf_atom = self.path.rsplit("/", 1)
        return Page.objects.get(path=base)

    #--------------------------------------------------------------------------
    def get_post_list(self):
        return Post.published_objects.filter(**{
            'blog': self,
        }).order_by(
            '-publish_timestamp'
        )
    post_list = property(get_post_list)

    #---------------------------------------------------------------------------
    def get_path_reservation_type(self):
        return "tree"

    #---------------------------------------------------------------------------
    def get_request_method(self):
        return "GET"

    #--------------------------------------------------------------------------
    def get_request_handler(self):
        obj, _ = RequestHandler.objects.get_or_create(
                title = 'Blog PageView',
                function = 'swim.blog.views.BlogView',
            )
        return obj

    #--------------------------------------------------------------------------
    def url(self):
        if self.path.strip('/') == '':
            return '/'
        else:
            return '/%s' % self.path.strip('/')

    #--------------------------------------------------------------------------
    def __str__(self):
        return "%s (%s)" % (
                self.path,
                self.title or "untitled",
            )

    #--------------------------------------------------------------------------
    def get_absolute_url(self):
        return self.url()

    #--------------------------------------------------------------------------
    def save(self, *args, **kwargs):
        if not self.key:
           self.key = string_to_key(self.path)
        super(Blog, self).save(*args, **kwargs)

    #--------------------------------------------------------------------------
    class Meta:
        ordering = ('path',)

register_content_object('blog', Blog)


#-------------------------------------------------------------------------------
class Tag(ActsLikeTimeline, Resource, HasPublishedTimeline):
    blog = models.ForeignKey(
        Blog,
        related_name='tags',
        on_delete=models.CASCADE,
    )
    order = models.IntegerField(default=0)
    title = models.CharField(max_length=64)
    slug = models.SlugField('Path Atom', **{
        'max_length': 200,
        'unique': True,
        'editable': False,
        'null': True,
    })

    #---------------------------------------------------------------------------
    def get_post_list(self):
        """
        Return a list of posts that are filtered by Tags.
        """

        try:
            return Post.published_objects.filter(**{
                'blog': self.blog,
                'tags__in': [self]
            })
        except Blog.DoesNotExist:
            return Post.objects.none()

    post_list = property(get_post_list)

    #---------------------------------------------------------------------------
    def get_parent(self):
        return self.blog

    #---------------------------------------------------------------------------
    def url(self):
        return '{}/tag/{}'.format(self.blog.url(), self.slug)

    #---------------------------------------------------------------------------
    def get_request_handler(self):
        obj, _ = RequestHandler.objects.get_or_create(**{
            'title': 'swim.blog.views.BlogTagView',
            'function': 'swim.blog.views.BlogTagView',
        })
        return obj

    #---------------------------------------------------------------------------
    def get_request_method(self):
        return "GET"

    #---------------------------------------------------------------------------
    def __str__(self):
        return self.title

    #---------------------------------------------------------------------------
    def position(self):
        """
        Return our position in a sorted list of all of our Blog's tags.
        """

        if not hasattr(self, '_position'):
            tags = list(self.blog.tags.all())
            try:
                self._position = tags.index(self)
            except ValueError:
                self._position = None

        return self._position

    #---------------------------------------------------------------------------
    def save(self, *args, **kwargs):
        super(Tag, self).save(*args, **kwargs)

        if not self.slug:
            self.slug = slugify('{} {}'.format(self.title, self.id))
            super(Tag, self).save(*args, **kwargs)

    #---------------------------------------------------------------------------
    class Meta:
        verbose_name = "Tag"
        verbose_name_plural = "Tags"
        ordering = ['order', 'title']


#-------------------------------------------------------------------------------
class BlogYear(ActsLikeTimeline, Resource, HasPublishedTimeline):
    blog = models.ForeignKey(
        Blog,
        related_name='year_set',
        on_delete=models.CASCADE,
    )
    year = models.IntegerField()

    #--------------------------------------------------------------------------
    def get_post_list(self):
        """
        Return a list of posts that occured for this blog on this year.
        """
        return Post.published_objects.filter(
                blog=self.blog,
                publish_date__year=self.year,
            )
    post_list = property(get_post_list)

    #--------------------------------------------------------------------------
    def delete_if_empty(self):
        # If there are NO posts on this month for this blog, delete myself.
        post_count = self.get_post_list().count()
        if post_count == 0:
            self.delete()

    #--------------------------------------------------------------------------
    def create_from_date(blog, date):
        year, created = BlogYear.objects.get_or_create(
                blog = blog,
                year=date.year
            )
        return year
    create_from_date = staticmethod(create_from_date)

    #--------------------------------------------------------------------------
    def url(self):
        return "%s/%s" % (self.blog.url(), self.year, )

    #--------------------------------------------------------------------------
    def get_request_handler(self):
        obj, _ = RequestHandler.objects.get_or_create(
                title = 'swim.blog.views.BlogYearView',
                function = 'swim.blog.views.BlogYearView',
            )
        return obj

    #---------------------------------------------------------------------------
    def get_request_method(self):
        return "GET"


#-------------------------------------------------------------------------------
class BlogMonth(ActsLikeTimeline, Resource, HasPublishedTimeline):
    year = models.ForeignKey(
        BlogYear,
        related_name='month_set',
        on_delete=models.CASCADE
    )
    month = models.IntegerField()

    #--------------------------------------------------------------------------
    def get_blog(self):
        """
        Ensure that BlogMonth acts as if it is directly associated with a blog.
        """
        return self.year.blog
    blog = property(get_blog)

    #--------------------------------------------------------------------------
    def get_post_list(self):
        """
        Return a list of posts that occured for this blog on this year.
        """
        return Post.published_objects.filter(
            blog=self.year.blog,
            publish_date__year=self.year.year,
            publish_date__month=self.month,
        ).order_by(
            '-publish_timestamp'
        )
    post_list = property(get_post_list)

    #--------------------------------------------------------------------------
    def delete_if_empty(self):
        # If there are NO posts on this month for this blog, delete myself.
        post_count = self.get_post_list().count()
        self.year.delete_if_empty()
        if post_count == 0:
            self.delete()

    #--------------------------------------------------------------------------
    def create_from_date(blog, date):
        month, created = BlogMonth.objects.get_or_create(
                year = BlogYear.create_from_date(blog, date),
                month=date.month
            )
        return month
    create_from_date = staticmethod(create_from_date)

    #--------------------------------------------------------------------------
    def url(self):
        return "%s/%s" % (self.year.url(), self.month)

    #---------------------------------------------------------------------------
    def get_start_date(self):
        return date(self.year.year, self.month, 1)
    start_date = property(get_start_date)

    #--------------------------------------------------------------------------
    def get_request_handler(self):
        obj, _ = RequestHandler.objects.get_or_create(
                title = 'swim.blog.views.BlogMonthView',
                function = 'swim.blog.views.BlogMonthView',
            )
        return obj

    #---------------------------------------------------------------------------
    def get_request_method(self):
        return "GET"


#-------------------------------------------------------------------------------
class BlogDay(ActsLikeTimeline, Resource, HasPublishedTimeline):
    month = models.ForeignKey(
        BlogMonth,
        related_name='months',
        on_delete=models.CASCADE,
    )
    day = models.IntegerField()

    #--------------------------------------------------------------------------
    def get_blog(self):
        """
        Ensure that BlogDay acts as if it is directly associated with a blog.
        """
        return self.month.year.blog
    blog = property(get_blog)

    #--------------------------------------------------------------------------
    def create_from_date(blog, date):
        day, created = BlogDay.objects.get_or_create(
                month=BlogMonth.create_from_date(blog, date),
                day=date.day
            )
        return day
    create_from_date = staticmethod(create_from_date)

    #--------------------------------------------------------------------------
    def get_post_list(self):
        """
        Return a list of posts that occured for this blog on this year.
        """
        return Post.published_objects.filter(
                blog=self.month.year.blog,
                publish_date__year=self.month.year.year,
                publish_date__month=self.month.month,
                publish_date__day=self.day,
            )
    post_list = property(get_post_list)

    #--------------------------------------------------------------------------
    def delete_if_empty(self):
        # If there are NO posts on this day for this blog, delete myself.
        post_count = self.get_post_list().count()
        self.month.delete_if_empty()
        if post_count == 0:
            self.delete()

    #--------------------------------------------------------------------------
    def url(self):
        return "%s/%s" % (self.month.url(), self.day)

    #--------------------------------------------------------------------------
    def get_request_handler(self):
        obj, _ = RequestHandler.objects.get_or_create(
                title = 'swim.blog.views.BlogDayView',
                function = 'swim.blog.views.BlogDayView',
            )
        return obj

    #---------------------------------------------------------------------------
    def get_request_method(self):
        return "GET"


#-------------------------------------------------------------------------------
class Post(Resource, PublishedInstant, HasSEOAttributes):
    """
    Blog Post is a dated post.
    """

    publish_date = models.DateField(null=True, blank=True)
    publish_time = models.TimeField(null=True, blank=True)

    blog = models.ForeignKey(
        Blog,
        related_name='posts',
        on_delete=models.CASCADE,
    )
    blog_path = modelfields.Path()

    title = models.CharField(max_length=200)
    name = models.SlugField('Path Atom', **{
        'max_length': 200,
        'unique': True,
        'blank': True,
        'null': True,
        'help_text': 'This will automatically be set from the title.'
    })
    tags = models.ManyToManyField(Tag, **{
        'blank': True,
        'related_name': 'posts',
        'help_text': 'A Post must be assigned to a Blog before you can add Tags.'
    })

    objects = WithRelated('resource_type')
    published_objects = PublishedItemsManager()

    #--------------------------------------------------------------------------
    def __str__(self) :
        if self.publish_date and self.publish_time:
            return '{} - {}'.format(self.title, self.date_string())
        else:
            return '{} - DRAFT'.format(self.title)

    #--------------------------------------------------------------------------
    def url(self):
        if self.publish_date:
            date_str = '{}/{}/{}'.format(
                self.publish_date.year,
                self.publish_date.month,
                self.publish_date.day,
            )
            return '{}/{}/{}'.format(self.blog_path, date_str, self.name)
        else:
            return '{}/draft/{}'.format(self.blog_path, self.name)

    #--------------------------------------------------------------------------
    def year_url(self):
        if self.publish_date:
            return '{}/{}'.format(self.blog_path, self.publish_date.year)
        else:
            return self.blog_path

    #--------------------------------------------------------------------------
    def month_url(self):
        if self.publish_date:
            return '{}/{}/{}'.format(
                self.blog_path, self.publish_date.year, self.publish_date.month
            )
        else:
            return self.blog_path

    #--------------------------------------------------------------------------
    def day_url(self):
        if self.publish_date:
            return '{}/{}/{}/{}'.format(
                self.blog_path,
                self.publish_date.year,
                self.publish_date.month,
                self.publish_date.day,
            )
        else:
            return self.blog_path

    #--------------------------------------------------------------------------
    def save(self, *args, **kwargs):
        self.blog_path = self.blog.path

        if not self.id:
            super(Post, self).save(*args, **kwargs)
            kwargs['force_insert'] = False

        if not self.name:
            self.name = '%s-%s' % (slugify(self.title), self.id)

        super(Post, self).save(*args, **kwargs)

        # When published, make sure there are appropriate handlers.
        if self.publish_date:
            BlogDay.create_from_date(self.blog, self.publish_date)

    #--------------------------------------------------------------------------
    def delete(self):
        if self.publish_date:
            day = BlogDay.create_from_date(self.blog, self.publish_date)

        super(Post, self).delete()

        if self.publish_date:
            day.delete_if_empty()

    #--------------------------------------------------------------------------
    def get_request_handler(self):
        obj, _ = RequestHandler.objects.get_or_create(**{
            'title': 'swim.blog.views.BlogPostView',
            'function': 'swim.blog.views.BlogPostView',
        })
        return obj

    #---------------------------------------------------------------------------
    def get_request_method(self):
        return "GET"

    #---------------------------------------------------------------------------
    def get_parent(self):
        return self.blog

    #---------------------------------------------------------------------------
    def get_similar_posts(self):
        qs = self.blog.post_list.filter(tags__in=self.tags.all())
        qs = qs.exclude(id=self.id)
        qs = qs.distinct()
        return qs

    #---------------------------------------------------------------------------
    class Meta:
        verbose_name = "Post"
        verbose_name_plural = "Posts"
        ordering = ['-publish_date']
        unique_together = (('blog', 'publish_date', 'title'),)

register_content_object('post', Post)


#-------------------------------------------------------------------------------
def update_blog_path(sender, instance, created, **kwargs):
    for post in instance.posts.all():
        post.save()

    for tag in instance.tags.all():
        tag.save()

post_save.connect(update_blog_path, sender=Blog)


#-------------------------------------------------------------------------------
class AllBlogPosts(Timeline):

    #--------------------------------------------------------------------------
    def __init__(self):
        # ensure we initialize the ranges mixin properly.
        super(AllBlogPosts, self).__init__(
            Post.objects.all(),
            'publish_timestamp',
            'publish_timestamp',
            'resource_type',
        )

