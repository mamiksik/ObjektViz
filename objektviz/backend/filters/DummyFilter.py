from typing import Mapping

from objektviz.backend.filters.AbstractFilter import AbstractFilter


class DummyFilter(AbstractFilter):
    """A dummy filter that can be used for testing purposes, it either passes all elements or none of them based on the is_passing parameter"""
    _is_passing: bool

    def __init__(self, is_passing: bool):
        self._is_passing = is_passing

    def is_passing(self, entity: Mapping):
        return self._is_passing
