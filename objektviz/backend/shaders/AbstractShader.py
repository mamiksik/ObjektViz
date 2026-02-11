import abc
import colorsys
import functools
import typing
from typing import Literal

import matplotlib
from matplotlib import pyplot as plt

if typing.TYPE_CHECKING:
    from objektviz.backend.BackendConfig import BackendConfig


type ColorT = tuple[Literal["hex", "cmap"], str]

class AbstractShader(abc.ABC):
    config: "BackendConfig"
    leading_attribute: str
    color: ColorT

    def __init__(
        self,
        config: "BackendConfig",
        leading_attribute: str,
        color: ColorT,
    ):
        self.config = config
        self.leading_attribute = leading_attribute
        self.color = color

    def get_attribute_value(self, entity: typing.Mapping, default=None):
        value = entity.get(self.leading_attribute, default)
        if not isinstance(value, (float, int)):
            raise ValueError(
                f"Attribute {self.leading_attribute} must be float or int, not {type(value)}"
            )

        return value


    @staticmethod
    def clamp(_min, value, _max):
        return max(_min, min(_max, value))

    def get_color(self, normalized_value):
        color_type, color_value = self.color
        if color_type == "hex":
            # 0 is white, 1 is black, so we clamp to 0.7 to avoid too dark colors
            normalized_value = self.clamp(0.3, normalized_value, 0.7)
            return get_hex_color(color_value, normalized_value)

        if color_type == "cmap":
            # 0 is white, so we clamp to 0.3 to avoid too light colors, but we allow 1 to show the full range of the colormap
            normalized_value = self.clamp(0.3, normalized_value, 1)  # clamp minimal value
            return get_cmap_color(color_value, normalized_value)

        raise ValueError(f"Invalid color type: {color_type}")

    @abc.abstractmethod
    def pen_width(self, entity: typing.Mapping):
        pass

    @abc.abstractmethod
    def shading_color(self, entity: typing.Mapping):
        pass


    @abc.abstractmethod
    def update_bounds(self, entity: typing.Mapping):
        pass


def get_hex_color(hex_color: str, luminosity: float) -> str:
    if not (0.0 <= luminosity <= 1.0):
        raise ValueError("luminosity must be between 0 and 1")

    # Remove '#' if present
    hex_color = hex_color.lstrip('#')
    if len(hex_color) != 6:
        raise ValueError("hex_color must be a 6-character hex string")

    # Convert hex to RGB (0–255)
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)

    # Normalize RGB to 0–1
    r_norm, g_norm, b_norm = r / 255.0, g / 255.0, b / 255.0

    # Convert to HLS (Hue, Lightness, Saturation)
    h, l, s = colorsys.rgb_to_hls(r_norm, g_norm, b_norm)

    # Replace lightness with desired luminosity
    r_new, g_new, b_new = colorsys.hls_to_rgb(h, 1 - luminosity, s)

    # Convert back to 0–255
    r_out = int(round(r_new * 255))
    g_out = int(round(g_new * 255))
    b_out = int(round(b_new * 255))

    return f"#{r_out:02X}{g_out:02X}{b_out:02X}"


def get_cmap_color(cmap: str, normalized_value: float):
    colormap = plt.get_cmap(cmap)
    color = colormap(normalized_value)
    return matplotlib.colors.rgb2hex(color)