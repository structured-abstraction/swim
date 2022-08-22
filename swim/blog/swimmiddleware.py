"""
Blog related middleware.
"""
from swim.blog.models import Post, AllBlogPosts
from swim.content.models import Page

#-------------------------------------------------------------------------------
def blog_context(request, context, resource, template):
    """
    Ensure that the blog post for the blog is put in the context.
    """
    if 'blog' not in context:
        # If one of the views didn't jam a blog into the context, let's assume
        # the page _IS_ the blog!
        context['blog'] = context['resource']

#-------------------------------------------------------------------------------
def all_blog_posts(request, context, resource, template):
    """
    Update the context to include an 'all_calendar_events' entry.
    """
    context['all_blog_posts'] = AllBlogPosts()
