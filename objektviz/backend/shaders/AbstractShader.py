import abc
import typing

import matplotlib
import neo4j.graph
from matplotlib import pyplot as plt

if typing.TYPE_CHECKING:
    from objektviz.backend.BackendConfig import BackendConfig


class AbstractShader(abc.ABC):
    config: "BackendConfig"
    cmap: str
    leading_attribute: str

    def __init__(self, config: "BackendConfig", cmap: str, leading_attribute: str):
        self.config = config
        self.cmap = cmap
        self.leading_attribute = leading_attribute

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
        color = colormap(
            float(normalized_value)
        )  # Ensure the value is int, int(1) will maps to 0.0 color equivalent
        return matplotlib.colors.rgb2hex(color)
