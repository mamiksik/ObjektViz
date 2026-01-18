import os
import pathlib

import streamlit as st

import kuzu

import objektviz.streamlit.components as ov_components
import objektviz.backend.filters as ov_filters
import objektviz.backend.adaptors.kuzudb as ov_kuzu
from kuzu_example_helpers import generate_token_animation_segments

from objektviz.backend.BackendConfig import BackendConfig
from objektviz.streamlit.utils import (
    DefaultConnectionPreferences,
    DefaultEventClassPreferences,
    DefaultShadingPreferences,
    DefaultLayoutPreferences,
    TokenReplayManager,
)
from objektviz.backend.dot_graph_builder import generate_dot_source

from objektviz.frontend import GraphFrontendPayload

PATH = pathlib.Path(os.path.dirname(os.path.abspath(__file__)))
OCEL_DATASETS = PATH / "datasets" / "kuzudb"
DATASETS = {
    "Container Logistics": OCEL_DATASETS / "container_logistics.kuzu",
    "Order Management": OCEL_DATASETS / "order_managment.kuzu",
}

# ----------------------------------------------------------------------------
# DB Connection [EDIT AS NEEDED]
# ----------------------------------------------------------------------------
with st.sidebar:
    st.selectbox(
        label="Dataset",
        options=DATASETS.keys(),
        key="kuzu_dataset_selector",
    )

if "kuzu_dataset_selector" not in st.session_state:
    st.session_state.kuzu_dataset_selector = next(iter(DATASETS.keys()))

database_path = DATASETS[st.session_state.kuzu_dataset_selector]

db = kuzu.Database(database_path)
conn = kuzu.Connection(db)
queries = ov_kuzu.KuzuEKGRepository(conn)

# ----------------------------------------------------------------------------
# Stream lit UI boilerplate (DO NOT (LIKELY) MODIFY)
# ----------------------------------------------------------------------------
objektviz_sidebar = ov_components.setup_objektviz_page()

# Graph tab contains the main proclet graph
# EKG Stats tab contains statistics about EKG attributes
# Trace Variants tab contains trace variants for selected class type (TODO)
# Debug tab contains raw data for debugging purposes
# Sidebar contains all possible configuration options for the ObjektViz
process_model_tab, ekg_stats_tab, trace_variants_tab, debug_tab = st.tabs(
    ["📦 Process Model", "ℹ️ EKG Stats", "➡️ Trace Variants", "⚙️ Debug tab"]
)

# ----------------------------------------------------------------------------
# CONFIG SECTION [EDIT AS NEEDED]
# ----------------------------------------------------------------------------

# Available proclet types in the database
PROCLET_TYPES = ["EventType,EntityType"]

# To generalize to all entity types, we load the entity types from database
# and assign a color to each of them dynamically
# In real project, you might want to have more control over this mapping / manually define entity types
entity_types = queries.get_entity_types(None)
ENTITY_TYPES = entity_types

# The instances provide sensible defaults for the visualizer preferences in the sidebar
# but they may not fit your project needs, or they might not even work on your data at all
# (e.g., if the specified attributes do not exist), so feel free to modify them
DEFAULT_LAYOUT_PREFERENCES = DefaultLayoutPreferences()
DEFAULT_CONNECTION_PREFERENCES = DefaultConnectionPreferences()
DEFAULT_EVENT_CLASS_PREFERENCES = DefaultEventClassPreferences()

# st.write(entity_types)
avaible_colors = [
    "Blues",
    "Oranges",
    "Reds",
    "Greens",
    "Purples",
    "Greys",
    "YlGnBu",
    "YlOrRd",
    "PuRd",
]
color_map = {
    et: avaible_colors[i % len(avaible_colors)] for i, et in enumerate(entity_types)
}

SHADING_PREFERENCES = DefaultShadingPreferences(
    group_by="EntityType", color_map=color_map
)

TOKEN_UI_ANIMATION_PREFERENCES = TokenReplayManager(
    samplers={
        "All": lambda class_type, sample_size: queries.entity_sample(
            class_type, sample_size
        ),
    },
    token_animation_generator=generate_token_animation_segments,
)


# ----------------------------------------------------------------------------
# Stream lit UI [EDIT AS NEEDED]
# ----------------------------------------------------------------------------
# This can be edited to add project specific configuration options (especially in terms of filters)

with objektviz_sidebar:
    (
        class_type,
        is_process_start_end_visualized,
        start_end_nodes_per_cluster,
        enable_path_effects_on_hover,
        shader_factory,
    ) = ov_components.general_preferences(PROCLET_TYPES)

# This tab is defined in between to have access to the class_type variable
# but be rendered before we start querying the data, so that we can see it
# even if we encounter errors later on
with ekg_stats_tab:
    ov_components.ekg_stats(queries, class_type)

with objektviz_sidebar:
    (
        layout_preferences,
        connection_preferences,
        event_class_preferences,
        show_only_sampled_elements,
        token_replay_preferences,
    ) = ov_components.preferences_group(
        queries=queries,
        class_type=class_type,
        default_layout_preferences_input=DEFAULT_LAYOUT_PREFERENCES,
        default_connection_visuals=DEFAULT_CONNECTION_PREFERENCES,
        default_event_class_visuals=DEFAULT_EVENT_CLASS_PREFERENCES,
    )

    (
        active_element_trace_filter,
        token_animation_segments,
        replay_metadata,
        active_element_ids,
    ) = ov_components.token_replay_input(
        queries=queries,
        class_type=class_type,
        ui_preferences=TOKEN_UI_ANIMATION_PREFERENCES,
        token_replay_preferences=token_replay_preferences,
    )

    with debug_tab:
        st.write("Replay metadata:", replay_metadata)
        st.write("Process instances:", token_animation_segments)

    # Filters are quite project specific, so you will likely need to modify them
    # Below is just an example of how to add filters to the sidebar for frequency
    # Refer to the documentation for more information about available filters and how to compose them
    with st.expander("DFC Filters", expanded=False):
        root_edge_filter = ov_filters.RangeFilter.new(
            attribute="frequency",
            is_enabled=True,
            rng=st.slider(
                label="Frequency filter",
                min_value=1,
                max_value=10000,
                value=(1, 10000),
                label_visibility="collapsed",
            ),
        )

    with st.expander("Event Class Filters", expanded=True):
        node_filter_entity_type = ov_filters.MatchFilter.new(
            attribute="EntityType",
            is_enabled=True,
            skip_on_empty=True,
            values=st.pills(
                "Entity types to show",
                options=ENTITY_TYPES,
                default=ENTITY_TYPES,
                selection_mode="multi",
            ),
        )

        operator = st.pills(
            "Operator", options=["OR", "AND"], default="OR", selection_mode="single"
        )

        node_filter_frequency = ov_filters.RangeFilter.new(
            attribute="frequency",
            is_enabled=True,
            rng=st.slider(
                label="Event Class Frequency",
                min_value=1,
                max_value=10000,
                value=(1, 10000),
                # label_visibility="",
                key="node_frequency_filter",
            ),
        )
        # node_filter_frequency = ov_filters.MatchFilter.new(
        #     attribute="EntityType",
        #     is_enabled=True,
        #     skip_on_empty=True,
        #     values=st.pills("Entity types to show", options=ENTITY_TYPES, default=ENTITY_TYPES,selection_mode='multi')
        # )

        compound_filter = (
            ov_filters.OrFilter if operator == "OR" else ov_filters.AndFilter
        )
        root_node_filter = compound_filter.new(
            [node_filter_entity_type, node_filter_frequency]
        )


# Backend Visualizer Configuration
objektviz_config = BackendConfig(
    connection_preferences=connection_preferences,
    event_class_preferences=event_class_preferences,
    shader_groping_key=SHADING_PREFERENCES.group_by,
    shader_groups_color=SHADING_PREFERENCES.color_map,
    layout_preferences=layout_preferences,
    visualize_start_end_flag=is_process_start_end_visualized,
    start_end_nodes_per_cluster=start_end_nodes_per_cluster,
    event_class_root_filter=root_node_filter,
    connection_root_filter=root_edge_filter,
    shader_factory=shader_factory,
)

# Generate the dot source from the proclet data
nodes, edges = queries.proclet(class_type)
wrapped_values = ov_kuzu.from_kuzu_to_dot_elements(nodes, edges, objektviz_config)
dot_src, edge_node_map, node_edge_map, node_node_map = generate_dot_source(
    *wrapped_values
)

# Log the raw data in the debug tab
with debug_tab:
    ov_components.debug_objektviz_backend(objektviz_config, nodes, edges, dot_src)

# Prepare the payload for the frontend graph component
graphviz_payload = GraphFrontendPayload(
    dot_source=dot_src,
    active_element_ids=active_element_ids,
    enable_path_effects_on_hover=enable_path_effects_on_hover,
    animation_preferences=token_replay_preferences,
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
    st.write(graphviz_payload)

with process_model_tab:
    ov_components.full_proclet_view(
        graph_payload=graphviz_payload,
        nodes=wrapped_values[0],
        edges=wrapped_values[1],
        queries=queries,
        class_type=class_type,
        token_animation_segments=token_animation_segments,
    )

with trace_variants_tab:
    ov_components.trace_variants(class_type=class_type)
