import neo4j
import streamlit as st


import objektviz.streamlit.components as ov_components
import objektviz.backend.filters as ov_filters
from token_replay_helper import generate_token_animation_segments

from objektviz.backend.BackendConfig import BackendConfig
from objektviz.backend.adaptors.neo4j import (
    Neo4JEKGRepository,
    from_neo4j_to_dot_elements,
)
from objektviz.streamlit.utils import (
    DefaultConnectionPreferences,
    DefaultEventClassPreferences,
    DefaultShadingPreferences,
    DefaultLayoutPreferences,
    TokenReplayManager,
)
from objektviz.backend.dot_graph_builder import generate_dot_source

from objektviz.frontend import GraphFrontendPayload

# PATH = pathlib.Path(os.path.dirname(os.path.abspath(__file__)))
# OCEL_DATASETS = PATH / "datasets" / "kuzudb"
# DATASETS = {
#     "Container Logistics": OCEL_DATASETS / "container_logistics.kuzu",
#     "Order Management": OCEL_DATASETS / "order_managment.kuzu",
# }

# ----------------------------------------------------------------------------
# DB Connection [EDIT AS NEEDED]
# ----------------------------------------------------------------------------
# with st.sidebar:
#     st.selectbox(
#         label="Dataset",
#         options=DATASETS.keys(),
#         key="kuzu_dataset_selector",
#     )
#
# if "kuzu_dataset_selector" not in st.session_state:
#     st.session_state.kuzu_dataset_selector = next(iter(DATASETS.keys()))

# database_path = DATASETS[st.session_state.kuzu_dataset_selector]

driver = neo4j.GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))
queries = Neo4JEKGRepository(driver)

# conn = connection(database_path)
# queries = ov_kuzu.KuzuEKGRepository(conn)

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
ENTITY_TYPES = ["Invoice", "Item", "Order", "Payment", "SupplierOrder"]

# The instances provide sensible defaults for the visualizer preferences in the sidebar
# but they may not fit your project needs, or they might not even work on your data at all
# (e.g., if the specified attributes do not exist), so feel free to modify them
DEFAULT_LAYOUT_PREFERENCES = DefaultLayoutPreferences()
DEFAULT_CONNECTION_PREFERENCES = DefaultConnectionPreferences()
DEFAULT_EVENT_CLASS_PREFERENCES = DefaultEventClassPreferences()

color_map = {
    "Invoice": "Blues",
    "Item": "Greens",
    "Order": "Purples",
    "Payment": "Oranges",
    "SupplierOrder": "Reds",
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

# ----------------------------------------------------------------------------
# Query the data from the database (We fetch the data here, so we can use the values to populate the sidebar filters)
event_classes_db, dfc_db, sync_db = queries.proclet(class_type)

# ----------------------------------------------------------------------------

# This tab is defined in between to have access to the class_type variable
# but be rendered before we start querying the data, so that we can see it
# even if we encounter errors later on
with ekg_stats_tab:
    ov_components.ekg_stats(queries, class_type)

with objektviz_sidebar:
    (
        layout_preferences,
        dfc_preferences,
        event_class_preferences,
        show_only_sampled_elements_filter,
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

    # This filter will be used to ensure that DFC_C and EventClass of the sampled traces are always visible
    token_replay_element_filter = ov_filters.AndFilter.new(
        [
            show_only_sampled_elements_filter,
            ov_filters.MatchFilter.new(
                attribute="element_id",
                values=active_element_ids,
                skip_on_empty=True,
            ),
        ]
    )

    with debug_tab:
        st.write("Replay metadata:", replay_metadata)
        st.write("Process instances:", token_animation_segments)

    # Filters are quite project specific, so you will likely need to modify them
    # Below is just an example of how to add filters to the sidebar for frequency
    # Refer to the documentation for more information about available filters and how to compose them
    with st.expander("DFC Filters", expanded=False):
        dfc_frequency_filter = ov_components.frequency_filter_per_entity_type(
            queries.get_entity_types(class_type),
            dfc_db,
            key_prefix="dfc",
        )

        root_edge_filter = ov_filters.OrFilter.new(
            [token_replay_element_filter, dfc_frequency_filter]
        )

    with st.expander("Event Class Filters", expanded=True):
        node_filter_entity_type = ov_filters.NotFilter.new(
            ov_filters.MatchFilter.new(
                attribute="EntityType",
                is_enabled=True,
                skip_on_empty=False,  # If no entity types are selected, filter should return false for all items
                values=st.pills(
                    "Hide selected entity types",
                    options=ENTITY_TYPES,
                    default=[],
                    selection_mode="multi",
                ),
            )
        )

        event_class_frequency_filter = ov_components.frequency_filter_per_entity_type(
            queries.get_entity_types(class_type),
            event_classes_db,
            key_prefix="event_class",
        )

        root_node_filter = ov_filters.OrFilter.new(
            [
                token_replay_element_filter,
                ov_filters.AndFilter.new(
                    [node_filter_entity_type, event_class_frequency_filter]
                ),
            ]
        )


# Backend Visualizer Configuration
objektviz_config = BackendConfig(
    dfc_preferences=dfc_preferences,
    event_class_preferences=event_class_preferences,
    shader_groping_key=SHADING_PREFERENCES.group_by,
    shader_groups_color=SHADING_PREFERENCES.color_map,
    layout_preferences=layout_preferences,
    show_start_end_nodes=is_process_start_end_visualized,
    show_start_end_nodes_per_cluster=start_end_nodes_per_cluster,
    event_class_root_filter=root_node_filter,
    dfc_root_filter=root_edge_filter,
    shader_factory=shader_factory,
)

# Generate the dot source from the proclet data
wrapped_values = from_neo4j_to_dot_elements(
    event_classes_db, dfc_db + sync_db, objektviz_config
)
dot_src, edge_node_map, node_edge_map, node_node_map = generate_dot_source(
    *wrapped_values
)

# Log the raw data in the debug tab
with debug_tab:
    # TODO: I when this is split on multiple linces I get:
    # "line 1 ov_components.debug_objektviz_backend( ^ SyntaxError: '(' was never closed"
    ov_components.debug_objektviz_backend(objektviz_config, event_classes_db, dfc_db, dot_src)

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
        queries=queries,
        class_type=class_type,
        token_animation_segments=token_animation_segments,
    )

with ekg_stats_tab:
    ov_components.entity_distribution_plot(
        event_classes_db, dfc_db, entity_types=queries.get_entity_types(class_type)
    )


with trace_variants_tab:
    ov_components.trace_variants(class_type=class_type)


# conn.close()
