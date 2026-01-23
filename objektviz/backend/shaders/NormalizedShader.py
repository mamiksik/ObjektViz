from dataclasses import field, dataclass
from math import isclose

import matplotlib
import neo4j.graph
from matplotlib import pyplot as plt

from objektviz.backend.shaders.AbstractShader import AbstractShader


@dataclass(kw_only=True)
class NormalizedShader(AbstractShader):
    upper_bound: int | float = float("-inf")
    lower_bound: int | float = float("inf")
    values: list = field(default_factory=lambda: [])

    @staticmethod
    def clamp(_min, value, _max):
        return max(_min, min(_max, value))

    def pen_width(self, entity: neo4j.graph.Entity | dict):
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

    def shading_color(self, entity: neo4j.graph.Entity | dict):
        # In case the attribute is not present, default to self.lower_bound to make the element visible
        if isclose(self.lower_bound, self.upper_bound, rel_tol=0.01):
            normalized_value = 1.0
        else:
            value = entity.get(self.leading_attribute, self.lower_bound)
            value = self.clamp(self.lower_bound, value, self.upper_bound)
            normalized_value = (value - self.lower_bound) / (
                self.upper_bound - self.lower_bound
            )

        normalized_value = self.clamp(0.3, normalized_value, 1.0)  # clamp minimal value
        colormap = plt.get_cmap(self.cmap)
        color = colormap(
            float(normalized_value)
        )  # Ensure the value is int, int(1) will maps to 0.0 color equivalent
        return matplotlib.colors.rgb2hex(color)

    def update_bounds(self, entity: neo4j.graph.Entity):
        # In case the attribute is not present, default to self.lower_bound to make the element visible
        value = entity.get(self.leading_attribute, self.lower_bound)

        if not (isinstance(value, float) or isinstance(value, int)):
            raise ValueError(
                f"Attribute {self.leading_attribute} must be float or int, not {type(value)}"
            )

        self.values.append(value)
        self.lower_bound = min(self.lower_bound, value)
        self.upper_bound = max(self.upper_bound, value)
