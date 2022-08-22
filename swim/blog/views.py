
from datetime import datetime

from django.http import Http404

from swim.content.views import PageView
from swim.blog.models import (
    Blog,
    BlogDay,
    BlogMonth,
    BlogYear,
    Post,
    Tag,
)

#-------------------------------------------------------------------------------
class BlogView(PageView):

    #---------------------------------------------------------------------------
    def get_context(self, request):
        """
        Add in the blog to the context of any blog page.
        """
        context = super(BlogView, self).get_context(request)
        context['blog'] = request.resource
        return context

    #---------------------------------------------------------------------------
    def match_resource(self, path, request):
        """Override the page matching algorithm to ensure the year isn't used.
        """
        try:
            return Blog.objects.get(path=path.lower())
        except Blog.DoesNotExist as e:
            raise Http404()


#-------------------------------------------------------------------------------
class BlogTagView(BlogView):

    #---------------------------------------------------------------------------
    def get_context(self, request):
        """
        Add in the blog to the context of any blog page.
        """
        context = super(BlogTagView, self).get_context(request)
        context['blog'] = request.resource.blog
        return context

    #---------------------------------------------------------------------------
    def match_resource(self, path, request):
        path, slug = self.get_last_path_atom(path)
        path, _sentinel = self.get_last_path_atom(path)

        blog = super(BlogTagView, self).match_resource(path, request)
        try:
            return Tag.objects.get(blog=blog, slug=slug)
        except Blog.DoesNotExist as e:
            raise Http404()


#-------------------------------------------------------------------------------
class BlogYearView(BlogView):

    #---------------------------------------------------------------------------
    def get_context(self, request):
        """
        Add in the blog to the context of any blog page.
        """
        context = super(BlogYearView, self).get_context(request)
        context['blog'] = request.resource.blog
        return context

    #---------------------------------------------------------------------------
    def match_resource(self, path, request):
        """Override the page matching algorithm to ensure the year isn't used.
        """
        path, year = self.get_last_path_atom(path)
        try:
            year = int(year)
            blog = super(BlogYearView, self).match_resource(path, request)
            return BlogYear.objects.get(blog=blog, year=year)
        except (BlogYear.DoesNotExist, ValueError, TypeError) as e:
            raise Http404()


#-------------------------------------------------------------------------------
class BlogMonthView(BlogYearView):

    #---------------------------------------------------------------------------
    def match_resource(self, path, request):
        """Override the page matching algorithm to ensure the year isn't used.
        """
        path, month = self.get_last_path_atom(path)
        try:
            month = int(month)
            year = super(BlogMonthView, self).match_resource(path, request)
            return BlogMonth.objects.get(year=year, month=month)
        except (BlogMonth.DoesNotExist, ValueError, TypeError) as e:
            raise Http404()


#-------------------------------------------------------------------------------
class BlogDayView(BlogMonthView):

    #---------------------------------------------------------------------------
    def match_resource(self, path, request):
        """Override the page matching algorithm to ensure the year isn't used.
        """
        path, day = self.get_last_path_atom(path)
        try:
            day = int(day)
            month = super(BlogDayView, self).match_resource(path, request)
            return BlogDay.objects.get(month=month, day=day)
        except (BlogDay.DoesNotExist, ValueError, TypeError) as e:
            raise Http404()


#-------------------------------------------------------------------------------
class BlogPostView(BlogDayView):

    #---------------------------------------------------------------------------
    def match_resource(self, path, request):
        """Override the page matching algorithm to ensure the year isn't used.
        """
        path, name = self.get_last_path_atom(path)
        subpath, sentinel = self.get_last_path_atom(path)

        try:
            if sentinel == 'draft':
                blog = Blog.objects.get(path=subpath.lower())
                return Post.objects.get(**{
                    'blog': blog,
                    'publish_date__isnull': True,
                    'name': name,
                })

            else:
                blog_day = super(BlogPostView, self).match_resource(path, request)
                day = datetime(**{
                    'year': blog_day.month.year.year,
                    'month': blog_day.month.month,
                    'day': blog_day.day
                })
                return Post.objects.get(**{
                    'blog': blog_day.blog,
                    'publish_date': day,
                    'name': name,
                })
        except Post.DoesNotExist as e:
            raise Http404()

