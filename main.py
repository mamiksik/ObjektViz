import streamlit as st
from typing import Literal

import neo4j

import objektviz.streamlit.components as ov_components
import objektviz.backend.filters as ov_filters
import objektviz.backend.adaptors.neo4j as ov_neo4j

from objektviz.backend.BackendConfig import BackendConfig
from objektviz.backend.dot_graph_builder import generate_dot_source

from objektviz.frontend import (
    GraphFrontendPayload,
    Token,
    ReplaySegment,
    ReplayMetadata,
    TokenReplayPreferences,
)


# ----------------------------------------------------------------------------
# Stream lit UI boilerplate (DO NOT MODIFY)
# ----------------------------------------------------------------------------
if "selected_edge" not in st.session_state:
    st.session_state.selected_edge = None

if "selected_node" not in st.session_state:
    st.session_state.selected_node = None

st.set_page_config(page_title="ObjektViz", page_icon="📦", layout="wide")

# ----------------------------------------------------------------------------
# CONFIG
# ----------------------------------------------------------------------------

# Attribute used for shader grouping, e.g., to assign colors to different groups
SHADER_GROPING_ATTR = "EntityType"

# Assign matplotlib colormaps to attribute values (used in node/edge shading)
ATTR_VAL_TO_COLOR_MAP = {
    "Order": "Blues",
    "ATE_ABORT": "Oranges",
    "SupplierOrder": "Reds",
    "Item": "Greens",
    "Payment": "Oranges",
    "Invoice": "Purples",
    None: "Greys",
}

# Assign hex colors to attribute values (used in token animation)
ATTR_VAL_TO_COLOR = {
    "Order": "#0000FF",
    "ATE_ABORT": "#FFA500",
    "SupplierOrder": "#FF0000",
    "Item": "#00FF00",
    "Payment": "#FFA500",
    "Invoice": "#800080",
    None: "Greys",
}

# Available proclet types in the database
PROCLET_TYPES = ["Activity,EntityType"]

# What attributes can be used for clustering
CLUSTERING_ATTRS = ["EntityType", "Name"]

# Default clustering attributes
CLUSTERING_ATTRS_DEFAULT = ["EntityType"]

# Entity Types
ENTITY_TYPES = ["Order", "SupplierOrder", "Item", "Payment", "Invoice"]

# Functions to sample entity ids for animation (we can have multiple samplers, e.g., to select sample from particular sub population)
ENTITY_ID_SAMPLER = {
    "All": lambda class_type, sample_size: queries.entity_sample(
        class_type, sample_size
    ),
}

# Icons for particular attribute values (ATTR NAME -> ATTR VALUE -> ICON)
ATTRIBUTE_ICON_MAP = {
    "Name": {
        "Unpack": "📦 ",
        "Receive SO": "📥 ",
        "Ship": "🚚 ",
    }
}

# ----------------------------------------------------------------------------
# DB Connection
# ----------------------------------------------------------------------------

driver = neo4j.GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))
queries = ov_neo4j.Neo4JEKGRepository(driver)

# ----------------------------------------------------------------------------
# Helper Methods
# ----------------------------------------------------------------------------


def generate_token_animation_segments(
    data: list[dict],
    start_date,
    end_date,
    animation_preferences: TokenReplayPreferences,
):
    """Generates token animation segments from process execution data. This is default implementation, each project will probably needs its own version."""
    active_element_ids = []
    tokens = []
    max_duration_sec = 0

    for trace in data:
        active_element_ids.extend(trace.get("ActiveElementIds"))

        if animation_preferences.fixed_animation_duration:
            segments = [
                ReplaySegment(
                    dfc_element_id=x.get("DFCElementId"),
                    start_offset_sec=i,
                    duration_sec=1,
                    activity_duration_sec=x.get("DurationSec")
                    * 0,  # TODO: activity_animation
                    color="#3e9b0a ",
                )
                for i, x in enumerate(trace.get("TraceSegments"))
            ]
        elif animation_preferences.token_animation_alignment == "At-once":
            startOffset = trace.get("TraceSegments")[0].get("StartOffsetSec")
            segments = [
                ReplaySegment(
                    dfc_element_id=x.get("DFCElementId"),
                    start_offset_sec=x.get("StartOffsetSec") - startOffset,
                    duration_sec=x.get("DurationSec") * 1,
                    activity_duration_sec=x.get("DurationSec")
                    * 0,  # TODO: activity_animation
                    color="#3e9b0a ",
                )
                for x in trace.get("TraceSegments")
            ]
        else:
            segments = [
                ReplaySegment(
                    dfc_element_id=x.get("DFCElementId"),
                    start_offset_sec=x.get("StartOffsetSec"),
                    duration_sec=x.get("DurationSec") * 1,
                    activity_duration_sec=x.get("DurationSec")
                    * 0,  # TODO: activity_animation
                    # color="#3e9b0a ",
                    color=ATTR_VAL_TO_COLOR.get(trace.get("Entity").get("EntityType")),
                )
                for x in trace.get("TraceSegments")
            ]

        replay_duration = (
            segments[-1].start_offset_sec
            + segments[-1].duration_sec
            + segments[-1].activity_duration_sec
        )
        if replay_duration > max_duration_sec:
            max_duration_sec = replay_duration

        tokens.append(
            Token(
                element_id=trace.get("Entity").get("element_id"),
                entity_id=trace.get("Entity").get("ID"),
                entity_type=trace.get("EntityType"),
                segments=segments,
            )
        )

    replay_metadata = ReplayMetadata(
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat(),
        total_duration_sec=max_duration_sec,
    )

    return active_element_ids, tokens, replay_metadata


@st.cache_data
def trace_variants(
    class_type: str,
    variant: Literal["DoA", "PreventedDoA", "DoAMaterialType"],
    limit: int,
    part_family_name: str | None,
):
    return []


# ----------------------------------------------------------------------------
# Stream lit UI
# ----------------------------------------------------------------------------

# Graph tab contains the main proclet graph
# EKG Stats tab contains statistics about EKG attributes (NOT IMPLEMENTED YET)
# Trace Variants tab contains trace variants for selected class type (TODO)
# Debug tab contains raw data for debugging purposes
ekg_stats = st.container()
graph_tab, trace_variants_tab, debug_tab = st.tabs(
    ["Graph", "Trace Variants", "Debug tab"]
)


# Sidebar contains all possible configuration options for the ObjektViz
# This can be edited to add project specific configuration options (especially in terms of filters)
with st.sidebar:
    st.title("📦 ObjektViz")
    with st.expander("General preferences"):
        class_type = st.selectbox("Proclet class type", options=PROCLET_TYPES)

        is_process_start_end_visualized = st.toggle(
            "Show process start/end nodes", value=True
        )
        start_end_nodes_per_cluster = st.toggle(
            "Start and end nodes per cluster",
            value=True,
            disabled=not is_process_start_end_visualized,
        )

        enable_path_effects_on_hover = st.toggle(
            "Enable path effects on hover", value=True
        )
        shader_factory = ov_components.builtin_shader_selector()

# This tab is defined in between to have access to the class_type variable
# but be rendered before we start querying the data, so that we can see it
# even if we encounter errors later on
with ekg_stats:
    class_attrs = set(queries.class_attributes(class_type=class_type))

    with st.expander("EKG Summary", expanded=True):
        col1, _, _ = st.columns(3)
        col1.metric(
            "Selected Proclet", class_type, help="The selected proclet class type"
        )

        col1, col2, col3 = st.columns(3)
        col1.metric(
            "Activity Classes Present",
            queries.count_classes(class_type),
            help="Number of distinct Activity classes in the selected proclet",
        )
        col2.metric(
            "Activity Connections Present",
            queries.count_dfc(class_type),
            help="Number of distinct Activity connections in the selected proclet",
        )
        col3.metric(
            "SYNC Edges Present",
            queries.count_sync(class_type),
            help="Number of SYNC edges in the selected proclet",
        )

        col1, col2, col3 = st.columns(3)
        col1.metric(
            "Process Start/End present",
            "StartCount" in class_attrs and "EndCount" in class_attrs,
            help="Whether at least some Activity nodes have **StartCount** and **EndCount** set",
        )
        col2.metric(
            "Start Activities",
            queries.count_start_activities(class_type),
            help="Number of distinct start Activity classes in the selected proclet",
        )
        col3.metric(
            "End Activities",
            queries.count_end_activities(class_type),
            help="Number of distinct end Activity classes in the selected proclet",
        )

        st.divider()
        col1, col2, col3 = st.columns(3)
        col1.write("Proclet Types Present:")
        col1.markdown(" ".join(f":blue-badge[{x}]" for x in queries.proclet_types()))

        col2.write("Class attributes present in the selected proclet:")
        col2.markdown(" ".join(f":blue-badge[{x}]" for x in class_attrs))

        dfc_attrs = set(queries.dfc_attributes(class_type=class_type))
        col3.write("Connection attributes present in the selected proclet:")
        col3.markdown(" ".join(f":blue-badge[{x}]" for x in dfc_attrs))

    # st.write(queries.check_attribute_type(class_type, 'EntityType'))

with st.sidebar:
    with st.expander("Layout preferences", expanded=False):
        layout_preferences = ov_components.layout_preferences_input(
            CLUSTERING_ATTRS, CLUSTERING_ATTRS_DEFAULT
        )

    with st.expander("Connection preferences", expanded=False):
        edge_vis_preferences = ov_components.edge_render_preference_input(
            queries.dfc_attributes(class_type), default="count"
        )

    with st.expander("Activity preferences", expanded=False):
        node_vis_preferences = ov_components.node_render_preference_input(
            queries.class_attributes(class_type),
            icon_map=ATTRIBUTE_ICON_MAP,
            default_right_attr="count",
            default_left_attr="count",
        )

    with st.expander("Animation preferences", expanded=False):
        show_only_required_elements = ov_filters.DummyFilter.new(
            is_passing=not st.toggle(
                "Hide connections and classes not contained in the sample"
            )
        )
        animation_preferences = ov_components.animation_preferences_input()

    with st.expander("Entities to animate", expanded=True):
        element_id_filter, active_element_ids, token_animation_segments = (
            ov_filters.DummyFilter.new(is_passing=False),
            None,
            None,
        )
        selected_entity_ids = ov_components.token_replay_input(
            class_type, ENTITY_ID_SAMPLER
        )

        replay_metadata = None
        if len(selected_entity_ids) != 0:
            result = queries.get_process_executions(class_type, selected_entity_ids)
            active_element_ids, token_animation_segments, replay_metadata = (
                generate_token_animation_segments(
                    result[0], result[1], result[2], animation_preferences
                )
            )
            element_id_filter = ov_filters.MatchFilter.new(
                attribute="element_id",
                is_enabled=True,
                skip_on_empty=True,
                values=active_element_ids,
            )
        with debug_tab:
            st.write("Selected entities:")
            st.write(selected_entity_ids)
            st.write("Process instances:")
            st.write(token_animation_segments)

    with st.expander("Connection Filters", expanded=True):
        attribute_range_filter_input = ov_filters.RangeFilter.new(
            attribute="count",
            is_enabled=True,
            rng=st.slider(
                label="Frequency filter",
                min_value=1,
                max_value=1000000,
                value=(1, 1000000),
                label_visibility="collapsed",
            ),
        )

    with st.expander("Activity filters", expanded=False):
        root_node_filter = ov_filters.MatchFilter.new(
            attribute="EntityType",
            is_enabled=True,
            skip_on_empty=True,
            values=st.multiselect(
                "Entity types to show", options=ENTITY_TYPES, default=ENTITY_TYPES
            ),
        )

    st.badge("ℹ️ ObjektViz | Year: 2025 | Author: Martin Miksik", color="blue")


# Backend Visualizer Configuration
dot_visualizer_config = BackendConfig(
    edge_preferences=edge_vis_preferences,
    node_preferences=node_vis_preferences,
    shader_groping_key=SHADER_GROPING_ATTR,
    shader_groups_color=ATTR_VAL_TO_COLOR_MAP,
    layout_preferences=layout_preferences,
    visualize_start_end_flag=is_process_start_end_visualized,
    start_end_nodes_per_cluster=start_end_nodes_per_cluster,
    node_filter=root_node_filter,
    # edge_filter=DummyFilter.new(is_passing=True),
    edge_filter=attribute_range_filter_input,
    shader_factory=shader_factory,
)

# Generate the proclet graph from Neo4j data
nodes, edges = queries.proclet(class_type)
wrapped_values = ov_neo4j.from_neo4j_to_dot_elements(
    nodes, edges, dot_visualizer_config
)
dot_src, edge_node_map, node_edge_map, node_node_map = generate_dot_source(
    *wrapped_values
)

# Log the raw data in the debug tab
with debug_tab:
    st.write(dot_visualizer_config)
    st.write("Node data coming from Neo4j")
    st.json(nodes, expanded=False)
    st.write("Edges data coming from Neo4j")
    st.json(edges, expanded=False)
    with st.expander("Dot source"):
        st.text_area(dot_src, disabled=True)

# Prepare the payload for the frontend graph component
graph_payload = GraphFrontendPayload(
    dot_source=dot_src,
    active_element_ids=active_element_ids,
    enable_path_effects_on_hover=enable_path_effects_on_hover,
    animation_preferences=animation_preferences,
    tokens=token_animation_segments,
    replay_metadata=replay_metadata,
    edge_node_map=edge_node_map,
    node_edge_map=node_edge_map,
    node_node_map=node_node_map,
    selected_element_id=st.session_state.selected_edge
    if st.session_state.selected_node is None
    else st.session_state.selected_node,
)

# Log the raw data in the debug tab
with debug_tab:
    st.write(graph_payload)

with graph_tab:
    ov_components.full_proclet_view(
        graph_payload=graph_payload,
        nodes=nodes,
        edges=edges,
        queries=queries,
        class_type=class_type,
        token_animation_segments=token_animation_segments,
    )

with trace_variants_tab:
    ov_components.trace_variants(class_type=class_type)
