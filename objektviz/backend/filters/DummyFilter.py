import dataclasses

import typing

if typing.TYPE_CHECKING:
    from objektviz.backend.dot_elements import AbstractDotElement

from objektviz.backend.filters.AbstractFilter import AbstractFilter


@dataclasses.dataclass
class DummyFilter(AbstractFilter):
    _is_passing: bool

    @classmethod
    def new(cls, is_passing):
        return cls(_is_passing=is_passing)

    def is_passing(self, entity: 'AbstractDotElement'):
        return self._is_passing
