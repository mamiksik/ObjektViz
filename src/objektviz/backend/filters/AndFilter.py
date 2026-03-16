import dataclasses

import typing

if typing.TYPE_CHECKING:
    from objektviz.backend.dot_elements import AbstractDotElement
from objektviz.backend.filters.AbstractFilter import AbstractFilter


@dataclasses.dataclass
class AndFilter(AbstractFilter):
    filters: list[AbstractFilter]

    @classmethod
    def new(cls, filters: list[AbstractFilter]):
        return cls(filters=filters)

    def is_passing(self, entity: 'AbstractDotElement'):
        for fltr in self.filters:
            if not fltr.is_passing(entity):
                return False

        return True
