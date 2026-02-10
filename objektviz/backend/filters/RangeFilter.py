from typing import Mapping

from objektviz.backend.filters.AbstractFilter import AbstractFilter


class RangeFilter(AbstractFilter):
    """ A filter that checks if a given attribute of an element is
        within a specified range, it can be enabled or disabled \
    """
    is_enabled: bool
    attribute: str
    lower_bound: int | float
    upper_bound: int | float


    def __init__(
        self, attribute: str, is_enabled: bool, rng: tuple[int | float, int | float]
    ):
        self.is_enabled = is_enabled
        self.attribute = attribute
        self.lower_bound, self.upper_bound = rng

    def is_passing(self, entity: Mapping):
        if not self.is_enabled:
            return True

        value = entity.get(self.attribute, None)
        if value is None:
            raise ValueError(
                f"Expected value for attribute {self.attribute} but found Null [{entity} {self}]"
            )

        return self.lower_bound <= value <= self.upper_bound
