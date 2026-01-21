import dataclasses

import neo4j.graph

from objektviz.backend.filters.AbstractFilter import AbstractFilter


@dataclasses.dataclass
class OrFilter(AbstractFilter):
    filters: list[AbstractFilter]

    @classmethod
    def new(cls, filters: list[AbstractFilter]):
        return cls(filters=filters)

    def is_passing(self, entity: neo4j.graph.Entity):
        for fltr in self.filters:
            # Skip disabled filters, this is kinda a hacky way to do it, but dataclasses inheritance is annoying
            if hasattr(fltr, "is_enabled") and fltr.is_enabled is False:
                continue

            if fltr.is_passing(entity):
                return True

        return False
