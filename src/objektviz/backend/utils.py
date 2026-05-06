from typing import Literal

from objektviz.backend.BackendConfig import BackendConfig


def shader_factory(config: BackendConfig):
    """Instantiate shaders for each element and entity type"""

    node_shaders = {
        entity: config.shader_factory(
            config,
            config.event_class_preferences.shading_attr,
            config.shader_cluster_color[entity],
        )
        for entity in config.shader_cluster_color.keys()
    }

    edge_shaders = {
        entity: config.shader_factory(
            config,
            config.dfc_preferences.shading_attr,
            config.shader_cluster_color[entity],
        )
        for entity in config.shader_cluster_color.keys()
    }

    return node_shaders, edge_shaders


def uuid_to_lbl(value) -> str:
    """DOT language does not allow ':' in ID, so we need to replace all : in UUIDs with a valid char"""
    return value.replace(":", "+")


def get_dominant_color(color: tuple[Literal["cmap"], str] | tuple[Literal["hex"], str]) -> str:
    """Get the dominant color from a color specification, which can be either a hex color or a colormap specification

    Args:
        color: A tuple specifying the color. It can be either ("hex", hex_color) or ("cmap", cmap_name)
    Returns:
        A hex color string representing the dominant color
    """
    match color:
        case ("hex", hex_color):
            return hex_color
        case ("cmap", cmap_name):
            import matplotlib.pyplot as plt
            value = plt.get_cmap(cmap_name)(0.5)
            return f"#{int(value[0]*255):02x}{int(value[1]*255):02x}{int(value[2]*255):02x}"
        case _:
            raise ValueError(f"Invalid color specification: {color}")


