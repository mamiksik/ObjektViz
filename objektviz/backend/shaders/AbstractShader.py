import abc
import dataclasses
import typing

import matplotlib
import neo4j.graph
from matplotlib import pyplot as plt

if typing.TYPE_CHECKING:
    from objektviz.backend.BackendConfig import BackendConfig


@dataclasses.dataclass
class AbstractShader:
    config: 'BackendConfig' = dataclasses.field(repr=False)
    cmap: str
    leading_attribute: str

    @abc.abstractmethod
    def pen_width(self, entity: neo4j.graph.Entity | dict):
        pass

    @abc.abstractmethod
    def shading_color(self, entity: neo4j.graph.Entity | dict):
        pass

    @abc.abstractmethod
    def update_bounds(self, entity: neo4j.graph.Entity):
        pass


    def get_color(self, normalized_value):
        colormap = plt.get_cmap(self.cmap)
        color = colormap(float(normalized_value))  # Ensure the value is int, int(1) will maps to 0.0 color equivalent
        return matplotlib.colors.rgb2hex(color)