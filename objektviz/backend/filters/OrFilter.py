from typing import Mapping

from objektviz.backend.filters.AbstractFilter import AbstractFilter


class OrFilter(AbstractFilter):
    """ Combines multiple filters, passing elements that pass at least one of the filters """
    filters: list[AbstractFilter]

    def __init__(self, filters: list[AbstractFilter]):
        self.filters = filters

    def is_passing(self, entity: Mapping):
        for fltr in self.filters:
            # Skip disabled filters, this is kinda a hacky way to do it, but dataclasses inheritance is annoying
            if hasattr(fltr, "is_enabled") and fltr.is_enabled is False:
                continue

            if fltr.is_passing(entity):
                return True

        return False
