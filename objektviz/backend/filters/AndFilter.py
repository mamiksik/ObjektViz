import dataclasses

import neo4j.graph

from objektviz.backend.filters.AbstractFilter import AbstractFilter


@dataclasses.dataclass
class AndFilter(AbstractFilter):
    filters: list[AbstractFilter]

    @classmethod
    def new(cls, filters: list[AbstractFilter]):
        return cls(filters=filters)

    def is_passing(self, entity: neo4j.graph.Entity):
        for fltr in self.filters:
            if not fltr.is_enabled:
                continue

            if not fltr.is_passing(entity):
                return False

        return True
