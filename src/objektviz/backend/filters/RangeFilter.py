import dataclasses

import typing

if typing.TYPE_CHECKING:
    from objektviz.backend.dot_elements import AbstractDotElement
from objektviz.backend.filters.AbstractFilter import AbstractFilter


@dataclasses.dataclass(kw_only=True)
class RangeFilter(AbstractFilter):
    is_enabled: bool
    attribute: str
    lower_bound: int | float
    upper_bound: int | float

    @classmethod
    def new(
        cls, attribute: str, is_enabled: bool, rng: tuple[int | float, int | float]
    ):
        return cls(
            is_enabled=is_enabled,
            attribute=attribute,
            lower_bound=rng[0],
            upper_bound=rng[1],
        )

    def is_passing(self, entity: 'AbstractDotElement'):
        if not self.is_enabled:
            return True

        value = entity.get(self.attribute, None)
        if value is None:
            raise ValueError(
                f"Expected value for attribute {self.attribute} but found Null [{entity} {self}]"
            )

        return self.lower_bound <= value <= self.upper_bound
