from typing import Mapping

from objektviz.backend.filters.AbstractFilter import AbstractFilter


class NotFilter(AbstractFilter):
    """ A filter that negates the result of another filter, passing elements that
        fail the inner filter and failing elements that pass the inner filter
    """
    filter: AbstractFilter

    def __init__(self, filter: AbstractFilter):
        self.filter = filter

    def is_passing(self, entity: Mapping):
        return not self.filter.is_passing(entity)
