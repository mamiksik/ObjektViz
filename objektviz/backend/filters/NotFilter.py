import dataclasses

import neo4j.graph

from objektviz.backend.filters.AbstractFilter import AbstractFilter


@dataclasses.dataclass
class NotFilter(AbstractFilter):
    filter: AbstractFilter

    @classmethod
    def new(cls, filter: AbstractFilter):
        return cls(filter=filter)

    def is_passing(self, entity: neo4j.graph.Entity):
        return not self.filter.is_passing(entity)
