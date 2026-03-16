from objektviz.backend.BackendConfig import BackendConfig


def shader_factory(config: BackendConfig):
    """Instantiate shaders for each element and entity type"""

    node_shaders = {
        entity: config.shader_factory(
            config,
            config.event_class_preferences.shading_attr,
            config.shader_groups_color[entity],
        )
        for entity in config.shader_groups_color.keys()
    }

    edge_shaders = {
        entity: config.shader_factory(
            config,
            config.dfc_preferences.shading_attr,
            config.shader_groups_color[entity],
        )
        for entity in config.shader_groups_color.keys()
    }

    return node_shaders, edge_shaders


def uuid_to_lbl(value) -> str:
    """DOT language does not allow ':' in ID, so we need to replace all : in UUIDs with a valid char"""
    return value.replace(":", "+")

