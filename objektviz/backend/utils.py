from matplotlib import pyplot as plt
import matplotlib as mplt

from objektviz.backend.BackendConfig import BackendConfig


def shader_factory(config: BackendConfig):
    """ Instantiate shaders for each element and entity type """

    node_shaders = {
        entity: config.shader_factory(config, config.event_class_preferences.shading_attr, config.shader_groups_color[entity])
        for entity in config.shader_groups_color.keys()
    }

    edge_shaders = {
        entity: config.shader_factory(config, config.connection_preferences.shading_attr, config.shader_groups_color[entity])
        for entity in config.shader_groups_color.keys()
    }

    return node_shaders, edge_shaders


def to_lbl(value) -> str:
    """ DOT language does not allow ':' in ID, so we need to replace all : in UUIDs with a valid char """
    return value.replace(':', '+')


def extrapolate_color(min_freq: int, max_freq: int, value: int, cmap: str):
    if max_freq == min_freq:
        normalized_value = 1
    else:
        normalized_value = (value - min_freq) / (max_freq - min_freq)

    normalized_value = min(max(0.3, normalized_value), 0.7) # clamp minimal value
    colormap = plt.get_cmap(cmap)
    color = colormap(normalized_value)
    return mplt.colors.rgb2hex(color)


def robust_scaler(iqr, median, value):
    return (value - median) / iqr
