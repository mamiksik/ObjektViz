import dataclasses
from typing import Callable, Self, Literal

from objektviz.backend.filters import AbstractFilter
from objektviz.backend.shaders import AbstractShader


@dataclasses.dataclass
class LayoutPreferences:
    """Subset of settings related to dot node and edge layout"""

    # All classes with the same activity string are put on the same level
    force_same_rank_for_event_class: bool = False

    # Force that start/end nodes are on same rank (diff for start and end)
    force_process_start_end_same_rank: bool = False

    # Sort nodes based on frequency, this influences the order in which they are
    # declared in the dot source code (this then influences the layout heuristics)
    sort_event_classes_by_frequency: bool = True

    # Sort edges based on frequency, this influences the order in which they are
    # declared in the dot source code (this then influences the layout heuristics)
    sort_connections_by_frequency: bool = True

    # If set to an attribute name, the attribute values will be used as edge weights
    # during layout computation. Higher weight means that the edge is "shorter" and "straighter"
    weight_attribute: str | None = None

    # List of keys used to create subgraph clusters, order matters!
    # e.g. ['EntityType', 'Location'] will create big clusters for
    # each entity type and within each it will create sub-clusters
    # for each location
    clustering_keys: list = dataclasses.field(default_factory=list)

    # Minimal (horizontal) spacing between nodes on the same rank/level
    node_separation: float = 0.5

    # Minimal vertical spacing between ranks/levels
    rank_separation: float = 0.5

    # Direction of the graph layout
    rank_direction: Literal["TB", "BT", "LR", "RL"] = "TB"  # Top to Bottom


@dataclasses.dataclass
class EventClassPreferences:
    """Subset of settings related to dot node appearance and content"""

    # Which (numeric) attributes is used to compute the shading range
    shading_attr: str

    # Attribute to be displayed as the node title
    title: str

    # Which attribute is used to display value on the left of the node
    caption_left: str

    # Which attribute is used to display value on the right of the node
    caption_right: str

    # In case the attribute value matches the value in the dict, the item
    # will be used as prefix
    # e.g. {"EntityType": {"Package": "📦","Contract": "📝"}}
    icon_map: dict[str, dict[str, str]]


@dataclasses.dataclass
class DFCPreferences:
    """Subset of settings related to dot edge appearance and content"""

    # Which attribute is used to display value on top of the edge
    caption: str

    # Which (numeric) attributes is used to compute the shading range
    shading_attr: str

    # If true, xlabels are used for caption, this means the labels are not taking into account while computing layout
    # It might prodice more compact and less convoluted routes for edges, but labels might not be visible
    use_x_labels: bool

    # Minimal and maximal edge line thickens. e.g (1, 15)
    pen_width_range: tuple[int, int]

    # If true, the edge will be shaded with the same color as the connected nodes,
    # else plain green/red color will be used for start/end edges respectively
    use_shading_color_on_start_end_edge: bool = False


@dataclasses.dataclass
class BackendConfig:
    """Configuration of ObjektViz backend, used to generate dot source based"""

    # What attribute is used group shaders
    shader_groping_key: str

    # Mapping of shader_grouping_key attr values to color map name (matplotlib.colors.Colormap)
    # e.g. {'Loan Application': "Blues", "Workflow": "Reds"}
    shader_groups_color: dict[str, str]

    # If true, process start/end nodes will be computed and visualized
    # This requires that the :Class nodes have "StartCount" and "EndCount" attributes defined
    show_start_end_nodes: bool

    # If true, each cluster will have its own virtual start/end node
    show_start_end_nodes_per_cluster: bool

    # Root filter used to filter :Class nodes (to include all nodes, just pass instance of DummyFilter)
    event_class_root_filter: AbstractFilter

    # Root filter used to filter :DF_C edges (to include all edges, just pass instance of DummyFilter)
    dfc_root_filter: AbstractFilter

    layout_preferences: LayoutPreferences
    dfc_preferences: DFCPreferences
    event_class_preferences: EventClassPreferences

    # Factory that creates the shader instances for event classes and connections
    # The parameters are:
    #   1) config (instance of this class),
    #   2) leading_attribute (shading attributed),
    #   3) cmap (matplotlib.colors.Colormap)
    # The factory must return an instance of AbstractShader subclass
    # e.g.
    #
    # lambda config, leading_attribute, cmap: NormalizedShader(
    #   config=config, leading_attribute=leading_attribute, cmap=cmap
    # )
    shader_factory: Callable[[Self, str, str], AbstractShader]
