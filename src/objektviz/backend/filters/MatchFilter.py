import dataclasses

import typing

if typing.TYPE_CHECKING:
    from objektviz.backend.dot_elements import AbstractDotElement

from objektviz.backend.filters.AbstractFilter import AbstractFilter


@dataclasses.dataclass
class MatchFilter(AbstractFilter):
    is_enabled: bool
    attribute: str
    skip_on_empty: bool
    values: list[str]

    @classmethod
    def new(
        cls,
        attribute: str,
        values: list[str],
        is_enabled: bool = True,
        skip_on_empty: bool = True,
    ):
        return cls(
            attribute=attribute,
            is_enabled=is_enabled,
            values=values,
            skip_on_empty=skip_on_empty,
        )

    def is_passing(self, entity: 'AbstractDotElement'):
        if not self.is_enabled:
            return True

        if not self.values and self.skip_on_empty:
            return True

        if self.attribute == "element_id":
            value = entity.element_id
        else:
            value = entity.get(self.attribute, None)

        return value in self.values
