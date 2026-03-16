import typing

from objektviz.backend.shaders.AbstractShader import ColorT
from objektviz.backend.shaders.PercentileShader import PercentileShader


if typing.TYPE_CHECKING:
    from objektviz.backend.BackendConfig import BackendConfig


def normalized_shader_factory():
    return NormalizedShader


class NormalizedShader(PercentileShader):
    def __init__(
        self,
        config: "BackendConfig",
        leading_attribute: str,
        color: ColorT,
    ):
        super().__init__(config, leading_attribute, color, (0, 100))

    def update_bounds(self, entity: typing.Mapping):
        # In case the attribute is not present, default to self.lower_bound to make the element visible
        value = self.get_attribute_value(entity, self.lower_bound)

        self.values.append(value)

        # For normalize shader, we don't use percental range and just use min max
        # This *might* yeiled better performance for very, very large graphs
        self.lower_bound = min(self.lower_bound, value)
        self.upper_bound = max(self.upper_bound, value)
