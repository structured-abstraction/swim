"""
The basic website application for SWIM.
"""
import os
import string

from django.core.exceptions import ObjectDoesNotExist
from django.dispatch import Signal
from django.db import models
from django.db.models import query, Q

#-------------------------------------------------------------------------------
def path_resolution_order(
    get_function,
    path,
    http_content_type,
    swim_content_type,
    exception=ObjectDoesNotExist,
    *args,
    **kwargs
):
    # Match a template that is marked as 'exact'
    try:
        object = get_function(path, http_content_type, swim_content_type, *args, **kwargs)
        return object
    except exception as e:
        pass

    # Otherwise match the template based on 'tree'
    object = None
    branch = path
    parts = [branch, '']
    while True:
        branch = parts[0]
        if branch == '':
            break
        try:
            object = get_function(branch, http_content_type, swim_content_type, *args, **kwargs)
            break
        except exception as e:
            if len(parts) <= 1:
                break

        # remove the last "path part" and iterate
        parts = branch.rsplit('/', 1)

    if not object:
        object = get_function('/', http_content_type, swim_content_type, *args, **kwargs)
    return object

#-------------------------------------------------------------------------------
def query_object_by_potential_paths(Model, path, path_attr='path'):
    """
    Find the object with the most specific path that contains the given path.

    Start by using exact path matches and then break off path pieces until none
    are left, and end by trying the default path "/" - this object does a single query.
    """
    potential_paths = []
    if path != "/":
        branch = path
        parts = [branch, '']
        while True:
            branch = parts[0]
            if branch == '':
                break
            potential_paths.append(branch)
            # remove the last "path part" and iterate
            parts = branch.rsplit('/', 1)

    potential_paths.append('/')

    query_restrictions = Q(**{path_attr:potential_paths.pop(0)})
    for path in potential_paths:
        query_restrictions |= Q(**{path_attr:path})

    try:
        return Model.objects.filter(
            query_restrictions
        ).extra(
            select={'the_len': "length(%s)" % path_attr}
        ).extra(
            order_by = ['-the_len']
        )[0]
    except IndexError:
        return None



#-------------------------------------------------------------------------------
def get_object_by_path(get_function, path, exception=ObjectDoesNotExist, *args, **kwargs):
    """
    Find the object with the most specific path that contains the given path.

    Start by using exact path matches and then break off path pieces until none
    are left, and end by trying the default path "/".
    """
    if path == "/":
        return get_function('/')

    object = None
    branch = path
    parts = [branch, '']
    while True:
        branch = parts[0]
        if branch == '':
            break
        try:
            object = get_function(branch, *args, **kwargs)
            break
        except exception:
            if len(parts) <= 1:
                break
        # remove the last "path part" and iterate
        parts = branch.rsplit('/', 1)

    if not object:
        object = get_function('/')
    return object

#-------------------------------------------------------------------------------
# Only allows letters, digits, and _
def string_to_key(the_str):
    allowed_list = string.ascii_letters + string.digits + '_'
    new_name = ''
    for x in the_str:
        if x not in allowed_list:
             x = '_'
        new_name += x
    return "_".join([x for x in new_name.split("_") if x])


#-------------------------------------------------------------------------------
# Compares to see if the first path (sub path) is a parent container of the
# second path (path).
def is_subpath_on_path(subpath, path):
    subpath_parts = subpath.strip('/').lower().split('/')
    path_parts = path.strip('/').lower().split('/')
    path_subpath = '/'.join(path_parts[:len(subpath_parts)])
    subpath = '/'.join(subpath_parts)
    return subpath == path_subpath


#-------------------------------------------------------------------------------
# Context: the problem is that Django fires the post_init signal BEFORE it
# populates the ForeignKey fields that were specified by the select_related
# call.  In our case, this means that update_resource_copy_body_init ALWAYS generated
# an extra, un-needed query.
#
# To solve this, we monkey patch django to send ANOTHER signal that occurs
# AFTER the related fields have been populated.  We'll call this post_select_related.
#post_select_related = Signal(providing_args=["instance"])
#query.ModelIterable.__old_iter__ = query.ModelIterable.__iter__
#def __SA_iter__(self):
#    for obj in self.__old_iter__():
#        post_select_related.send(sender=obj.__class__, instance=obj)
#        yield obj
#query.ModelIterable.__iter__ = __SA_iter__

#-------------------------------------------------------------------------------
class WithRelated(models.Manager):
    """
    A query manager which minimizes query to 'get' the associated resource_type.
    """

    def __init__(self, args=None):
        super(WithRelated, self).__init__()
        self.args = args
        if isinstance(self.args, str):
            self.args = [self.args]

    def get_queryset(self):
        qs = super(WithRelated, self).get_queryset()
        if not self.args:
            return qs
        return qs.select_related(*self.args)

