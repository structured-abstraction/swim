import itertools

from django.core import paginator


class DualPaginator(paginator.Paginator):
    """
    Extends django's paginator so that we can use two object_lists.
    """
    def __init__(self, first_list, second_list, per_page, orphans=0, allow_empty_first_page=True):
        self.first_list = first_list
        self.second_list = second_list
        self.per_page = per_page
        self.orphans = orphans
        self.allow_empty_first_page = allow_empty_first_page
        self._second_count = self._first_count = self._num_pages = self._count = None


    def page(self, number):
        "Returns a Page object for the given 1-based page number."
        number = self.validate_number(number)
        bottom = (number - 1) * self.per_page
        top = bottom + self.per_page
        if top + self.orphans >= self.count:
            top = self.count

        # At this point we have to split this range into two sections.
        # one for each list.
        first = []
        first_bottom = min(bottom, self.first_count)
        first_top = min(top, self.first_count)
        if first_bottom < self.first_count:
            first = self.first_list[first_bottom:first_top]

        second = []
        second_bottom = max(bottom - self.first_count, 0)
        second_top = max(top - self.first_count, 0)
        if second_top > 0:
            second = self.second_list[second_bottom:second_top]


        return paginator.Page(list(first) + list(second), number, self)


    def _get_individual_count(self, object_list):
        "Returns the total number of objects in a single list."
        try:
            return object_list.count()
        except (AttributeError, TypeError):
            # AttributeError if object_list has no count() method.
            # TypeError if object_list.count() requires arguments
            # (i.e. is of type list).
            return len(object_list)

    def _get_count(self):
        "Returns the total number of objects, across all pages."
        if self._count is None:
            self._count = self.first_count + self.second_count
        return self._count
    count = property(_get_count)

    def _get_first_count(self):
        "Returns the total number of objects in the first list."
        if self._first_count is None:
            self._first_count = self._get_individual_count(self.first_list)
        return self._first_count
    first_count = property(_get_first_count)

    def _get_second_count(self):
        "Returns the total number of objects in the second list."
        if self._second_count is None:
            self._second_count = self._get_individual_count(self.second_list)
        return self._second_count
    second_count = property(_get_second_count)
