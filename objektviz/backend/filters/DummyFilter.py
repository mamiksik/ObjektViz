import dataclasses

import neo4j.graph

from objektviz.backend.filters.AbstractFilter import AbstractFilter


@dataclasses.dataclass
class DummyFilter(AbstractFilter):
    _is_passing: bool

    @classmethod
    def new(cls, is_passing):
        return cls(_is_passing=is_passing)

    def is_passing(self, entity: neo4j.graph.Entity):
        return self._is_passing
