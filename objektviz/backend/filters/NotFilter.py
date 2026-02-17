import dataclasses

import typing

if typing.TYPE_CHECKING:
    from objektviz.backend.dot_elements import AbstractDotElement
from objektviz.backend.filters.AbstractFilter import AbstractFilter


@dataclasses.dataclass
class NotFilter(AbstractFilter):
    filter: AbstractFilter

    @classmethod
    def new(cls, filter: AbstractFilter):
        return cls(filter=filter)

    def is_passing(self, entity: 'AbstractDotElement'):
        return not self.filter.is_passing(entity)
