import typing

from sklearn.preprocessing import RobustScaler

from objektviz.backend.shaders.AbstractShader import AbstractShader, ColorT

if typing.TYPE_CHECKING:
    from objektviz.backend.BackendConfig import BackendConfig


def robust_shader_factory():
    return RobustShader


class RobustShader(AbstractShader):
    scaler: None | RobustScaler
    values: list

    def __init__(
        self,
        config: "BackendConfig",
        leading_attribute: str,
        color: "ColorT",
    ):
        super().__init__(config, leading_attribute, color)
        self.values = []
        self.scaler = None

    def pen_width(self, entity: typing.Mapping):
        pen_min, pen_max = (
            self.config.dfc_preferences.pen_width_range[0],
            self.config.dfc_preferences.pen_width_range[1],
        )
        value = entity.get(self.leading_attribute, pen_min)
        if self.scaler is None:
            self.scaler = RobustScaler().fit(self.values)

        _value = float(self.scaler.transform([[value]])[0]) + 0.5

        return max(pen_min, min(pen_max, (pen_max - pen_min) * _value))

    def shading_color(self, entity: typing.Mapping):
        # In case the attribute is not present, default to self.lower_bound to make the element visible

        if self.scaler is None:
            self.scaler = RobustScaler().fit(self.values)

        value = entity.get(self.leading_attribute, 0)  # Dist is centered around 0
        normalized_value = float(self.scaler.transform([[value]])[0] + 0.5)

        normalized_value = min(max(0.3, normalized_value), 0.7)  # clamp minimal value
        return self.get_color(normalized_value)

    def update_bounds(self, entity: typing.Mapping):
        # In case the attribute is not present, default to self.lower_bound to make the element visible
        value = self.get_attribute_value(entity, 0)  # Dist is centered around 0
        self.values.append([value])
