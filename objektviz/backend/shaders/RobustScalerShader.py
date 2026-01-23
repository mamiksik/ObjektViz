from dataclasses import dataclass, field

import matplotlib
import neo4j.graph
from matplotlib import pyplot as plt
from sklearn.preprocessing import RobustScaler

from objektviz.backend.shaders.AbstractShader import AbstractShader


@dataclass(kw_only=True)
class RobustShader(AbstractShader):
    values: list = field(default_factory=lambda: [])
    scaler = None

    def pen_width(self, entity: neo4j.graph.Entity | dict):
        pen_min, pen_max = (
            self.config.dfc_preferences.pen_width_range[0],
            self.config.dfc_preferences.pen_width_range[1],
        )
        value = entity.get(self.leading_attribute, pen_min)
        if self.scaler is None:
            self.scaler = RobustScaler().fit(self.values)

        _value = self.scaler.transform([[value]])[0] + 0.5

        return max(pen_min, min(pen_max, (pen_max - pen_min) * _value))

    def shading_color(self, entity: neo4j.graph.Entity | dict):
        # In case the attribute is not present, default to self.lower_bound to make the element visible

        if self.scaler is None:
            self.scaler = RobustScaler().fit(self.values)

        value = entity.get(self.leading_attribute, 0)  # Dist is centered around 0
        normalized_value = self.scaler.transform([[value]])[0] + 0.5

        normalized_value = min(max(0.3, normalized_value), 0.7)  # clamp minimal value
        colormap = plt.get_cmap(self.cmap)
        color = colormap(normalized_value)
        return matplotlib.colors.rgb2hex(color)

    def update_bounds(self, entity: neo4j.graph.Entity):
        # In case the attribute is not present, default to self.lower_bound to make the element visible
        value = entity.get(self.leading_attribute, 0)  # Dist is centered around 0
        if not (isinstance(value, float) or isinstance(value, int)):
            raise ValueError(
                f"Attribute {self.leading_attribute} must be float or int, not {type(value)}"
            )

        self.values.append([value])
