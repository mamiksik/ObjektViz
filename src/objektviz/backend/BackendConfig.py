import dataclasses
from typing import Callable, Self, Literal

from objektviz.backend.filters import AbstractFilter
from objektviz.backend.shaders import AbstractShader


@dataclasses.dataclass
class LayoutPreferences:
    """Subset of settings related to dot node and edge layout"""

    # All classes with the same activity string are put on the same level
    force_same_rank_for_event_class: bool = False

    # Make rank exclusive
    exclusive_event_class_ranks_experimental: bool = False

    # Force that start/end nodes are on same rank (diff for start and end)
    force_process_start_end_same_rank: bool = False

    # How to sort events before adding them into the dot source code, this influences the layout heuristics
    # to be used in combination with manual_class_sorting in BackendConfig
    sort_event_classes_by: Literal["Frequency", "Avg. Activity Order", "None"] = "Frequency"

    # Sort nodes based on frequency, this influences the order in which they are
    # declared in the dot source code (this then influences the layout heuristics)
    # sort_event_classes_by_frequency: bool = True

    # How to sort groups before adding them into the dot source code, this influences the layout heuristics
    sort_groups_by: Literal["Frequency", "Alphabetical"] = "Frequency"

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

    # If true, the start/end edges will have lower opacity to not overpower the nodes and other edges
    lower_start_end_edge_opacity: bool = False

    # If true, the :SYNC edges will be hidden, this is useful when there are too many :SYNC edges that make the graph unreadable
    hide_sync_edges: bool = False


@dataclasses.dataclass
class BackendConfig:
    """Configuration of ObjektViz backend, used to generate dot source based"""

    # What attribute is used group shaders
    shader_cluster_key: str

    # Mapping of shader_cluster_key attr values to color map name (matplotlib.colors.Colormap) or hex color
    # Matplot lib color maps are safer option since the luminosity change is precised uniformly,
    # but that also means that there is only very few of them.
    # e.g. {'Loan Application': ("hex", "#FF00FF"), "Workflow": ("cmap", "Reds")}
    shader_cluster_color: dict[str, tuple[str, str]]

    # If true, process start/end nodes will be computed and visualized
    # This requires that the :Class nodes have "StartCount" and "EndCount" attributes defined
    show_start_end_nodes: bool

    # If true, each cluster will have its own virtual start/end node
    show_start_end_nodes_per_cluster: bool

    # Root filter used to filter :Class nodes (to include all nodes, just pass instance of DummyFilter)
    event_class_root_filter: AbstractFilter

    # Root filter used to filter :DF_C edges (to include all edges, just pass instance of DummyFilter)
    dfc_root_filter: AbstractFilter

    # Global filter is applied to all elements including :SYNC edges
    # this is useful for instance for element_id filter to remove any elements based on their id
    # Also take into account not all elements have to have the same attribute, so use with caution
    root_element_filter: AbstractFilter | None

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

    # This is used to manually specify the order of event classes in the layout
    # i.e. when class sorting is set to avg. activity order, then we have to precompute the order of classes based,
    # it has no effect if class sorting is set to frequency or none
    explicit_event_class_order: dict | None

    # This is used to sort the clusters, index of the clustering key in the list
    # corresponds to render order of the cluster in the graph.
    explicit_cluster_order: list | None

