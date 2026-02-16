import functools
import typing

import numpy as np
from math import isclose

from objektviz.backend.shaders.AbstractShader import AbstractShader, ColorT

if typing.TYPE_CHECKING:
    from objektviz.backend.BackendConfig import BackendConfig


def percentile_shader_factory(percentile_range: tuple[int, int]):
    return functools.partial(PercentileShader, percentile_range=percentile_range)


class PercentileShader(AbstractShader):
    upper_bound: int | float = float("-inf")
    lower_bound: int | float = float("inf")
    percentile_range: tuple[int, int]
    values: list

    def __init__(
        self,
        config: "BackendConfig",
        leading_attribute: str,
        color: ColorT,
        percentile_range: tuple[int, int] = (0, 100),
    ):
        super().__init__(config, leading_attribute, color)
        self.percentile_range = percentile_range
        self.values = []

    def pen_width(self, entity: typing.Mapping):
        pen_min, pen_max = (
            self.config.dfc_preferences.pen_width_range[0],
            self.config.dfc_preferences.pen_width_range[1],
        )
        if isclose(self.lower_bound, self.upper_bound, rel_tol=0.01):
            return (pen_max - pen_min) / 2

        value = entity.get(self.leading_attribute, pen_min)
        value = self.clamp(self.lower_bound, value, self.upper_bound)

        # In case the attribute is not present, default to self.pen_min to make the element visible
        try:
            return int(
                (pen_max - pen_min)
                * ((value - self.lower_bound) / (self.upper_bound - self.lower_bound))
                + pen_min
            )
        except (ZeroDivisionError, ValueError):
            return 1

    def shading_color(self, entity: typing.Mapping):
        # In case the attribute is not present, default to self.lower_bound to make the element visible
        if isclose(self.lower_bound, self.upper_bound, rel_tol=0.01):
            normalized_value = 1.0
        else:
            value = entity.get(self.leading_attribute, self.lower_bound)
            value = self.clamp(self.lower_bound, value, self.upper_bound)
            normalized_value = (value - self.lower_bound) / (
                self.upper_bound - self.lower_bound
            )

        normalized_value = self.clamp(0.3, normalized_value, 0.7)  # clamp minimal value
        return self.get_color(normalized_value)

    def update_bounds(self, entity: typing.Mapping):
        # In case the attribute is not present, default to self.lower_bound to make the element visible
        value = self.get_attribute_value(entity, self.lower_bound)

        self.values.append(value)
        self.lower_bound = float(np.percentile(self.values, self.percentile_range[0]))
        self.upper_bound = float(np.percentile(self.values, self.percentile_range[1]))
