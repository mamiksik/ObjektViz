from typing import Mapping

from objektviz.backend.filters.AbstractFilter import AbstractFilter


class AndFilter(AbstractFilter):
    """ Combines multiple filters, only passing elements that pass all the filters """
    filters: list[AbstractFilter]

    def __init__(self, filters: list[AbstractFilter]):
        self.filters = filters

    def is_passing(self, entity: Mapping):
        for fltr in self.filters:
            if not fltr.is_passing(entity):
                return False

        return True
