from typing import Mapping

from objektviz.backend.filters.AbstractFilter import AbstractFilter


class MatchFilter(AbstractFilter):
    """ A filter that checks if the value of a given attribute matches any of the values in a provided list.
        If the list is empty, it can be configured to either pass all elements or fail all elements based on the
        skip_on_empty parameter.
    """

    is_enabled: bool
    attribute: str
    skip_on_empty: bool
    values: list[str]

    def __init__(
        self,
        attribute: str,
        is_enabled: bool,
        values: list[str],
        skip_on_empty: bool = True,
    ):
        self.is_enabled = is_enabled
        self.attribute = attribute
        self.values = values
        self.skip_on_empty = skip_on_empty

    def is_passing(self, entity: Mapping):
        if not self.is_enabled:
            return True

        if not self.values and self.skip_on_empty:
            return True

        # TODO: This is a bit of a hack, we should probably have
        #  a more generic way of handling the element_id attribute
        if self.attribute == "element_id":
            value = entity.element_idFF
        else:
            value = entity.get(self.attribute, None)

        return value in self.values
