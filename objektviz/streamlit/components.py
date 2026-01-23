import functools
from typing import Callable

import numpy as np
import streamlit as st
from matplotlib import pyplot as plt

from objektviz.backend.BackendConfig import (
    LayoutPreferences,
    BackendConfig,
    DFCPreferences,
    EventClassPreferences,
)


import objektviz.backend.filters as ov_filters
import objektviz.backend.shaders as ov_shaders
from objektviz.backend.adaptors.shared import AbstractEKGRepository
from objektviz.streamlit.utils import (
    DefaultConnectionPreferences,
    DefaultEventClassPreferences,
    DefaultLayoutPreferences,
    TokenReplayManager,
    assert_attribute_exists,
)

from objektviz.frontend import (
    TokenReplayPreferences,
    Token,
    interactive_proclet_graph,
    wire_graph_event,
    ReplayMetadata,
)


def setup_objektviz_page():
    if "selected_edge" not in st.session_state:
        st.session_state.selected_edge = None

    if "selected_node" not in st.session_state:
        st.session_state.selected_node = None

    if "selected_token" not in st.session_state:
        st.session_state.selected_token = None

    st.set_page_config(page_title="ObjektViz", page_icon="📦", layout="wide")

    with st.sidebar:
        st.title("📦 ObjektViz")
        objektviz_sidebar = st.container()
        # st.badge("ℹ️ ObjektViz | Year: 2025 | Author: Martin Miksik", color="blue")
        st.divider()
        st.markdown("Made with ❤️ by Martin Miksik")

    return objektviz_sidebar


def general_preferences(
    proclet_types: list[str],
) -> tuple[
    str,
    bool,
    bool,
    bool,
    Callable[["BackendConfig", str, str], ov_shaders.AbstractShader],
]:
    with st.expander("General preferences"):
        class_type = st.selectbox("Proclet class type", options=proclet_types, help="Select the proclet class type to visualize")

        is_process_start_end_visualized = st.toggle(
            "Show process start/end nodes", value=True, help="If enabled, nodes representing process start and end will be shown in the visualization. These are computed based on the 'StartCount' and 'EndCount' attributes of the event classes."
        )
        start_end_nodes_per_cluster = st.toggle(
            "Start and end nodes per cluster",
            value=True,
            disabled=not is_process_start_end_visualized,
            help="If enabled, each cluster will have its own virtual start and end node. This can help in visualizing the flow within clusters more clearly and reduce clutter in the overall graph.",
        )

        enable_path_effects_on_hover = st.toggle(
            "Enable path effects on hover", value=True,
            help="If enabled, when hovering over a DFC (edge) in the visualization, a dashed animation effect will be played along the path of the edge. This can help in visually tracing the flow of the process represented by the edge."
        )

        shader_factory = builtin_shader_selector()

        return (
            class_type,
            is_process_start_end_visualized,
            start_end_nodes_per_cluster,
            enable_path_effects_on_hover,
            shader_factory,
        )


def builtin_shader_selector() -> Callable[
    ["BackendConfig", str, str], ov_shaders.AbstractShader
]:
    shader_type = st.selectbox(
        "Shader type", options=["Percentile", "Normalized", "RobustScaler"],
        help="Select the shading algorithm used to map numeric attributes to visual properties like color and thickness. This helps to deal with outliers and varying data distributions effectively."
    )

    # We know assigning lambdas to variables is not best practice, but here its just more handy
    if shader_type == "Normalized":
        shader_factory = (  # noqa: E731
            lambda config, leading_attribute, cmap: ov_shaders.NormalizedShader(
                config=config, leading_attribute=leading_attribute, cmap=cmap
            )
        )
    elif shader_type == "Percentile":
        shader_range = st.slider(
            "Percentile range",
            min_value=0.0,
            max_value=100.0,
            value=(5.0, 95.0),
            step=2.5,
        )
        shader_factory = (  # noqa: E731
            lambda shader_range,
            config,
            leading_attribute,
            cmap: ov_shaders.PercentileShader(
                config=config,
                leading_attribute=leading_attribute,
                cmap=cmap,
                percentile_range=shader_range,
            )
        )
        shader_factory = functools.partial(shader_factory, shader_range)
    elif shader_type == "RobustScaler":
        shader_factory = (  # noqa: E731
            lambda config, leading_attribute, cmap: ov_shaders.RobustShader(
                config=config, leading_attribute=leading_attribute, cmap=cmap
            )
        )
    else:
        raise ValueError(f"Shader type {shader_type} not recognized")

    return shader_factory


def dfc_appearance_input(
    edge_attributes: list[str], defaults: DefaultConnectionPreferences
) -> DFCPreferences:
    return DFCPreferences(
        pen_width_range=st.slider(
            "DFC width range", min_value=1, max_value=30, value=defaults.pen_range,
            help="Defines the minimal and maximal line thickness used during rendering based on the shading attribute.",
        ),
        caption=st.selectbox(
            "DFC label",
            options=edge_attributes,
            index=edge_attributes.index(defaults.title),
            help="Attribute used to display value on top of the edge",
        ),
        shading_attr=st.selectbox(
            "DFC shading attribute",
            options=edge_attributes,
            index=edge_attributes.index(defaults.shading),
            help="Numeric attribute used for edge shading (e.g., frequency or average transition duration)",
        ),
        use_x_labels=st.toggle("Use xlabels", help="If true, xlabels are used for caption, this means the labels are not taking into account while computing layout. It might produce more compact and less convoluted routes for edges, but labels might not be visible."),
    )


def event_class_appearance_input(
    node_attributes: list[str], defaults: DefaultEventClassPreferences
) -> EventClassPreferences:
    container_top = st.container()
    col1, col2 = st.columns(2)
    container_bottom = st.container()
    return EventClassPreferences(
        title=container_top.selectbox(
            "Event class title",
            options=node_attributes,
            index=node_attributes.index(defaults.title),
            help="Attribute to be displayed as the node title",
        ),
        caption_left=col1.selectbox(
            "Caption left",
            options=node_attributes,
            index=node_attributes.index(defaults.small_caption_left),
            help="Which attribute is used to display value on the left of the node",
        ),
        caption_right=col2.selectbox(
            "Caption right",
            options=node_attributes,
            index=node_attributes.index(defaults.small_caption_right),
            help="Which attribute is used to display value on the right of the node",
        ),
        shading_attr=container_bottom.selectbox(
            "Event class shading attribute",
            options=node_attributes,
            index=node_attributes.index(defaults.shading_attr),
            help="Numeric attribute used for node shading (e.g., frequency or number of associated entities)",
        ),
        icon_map=defaults.icon_map,
    )


def layout_preferences_input(
    defaults: DefaultLayoutPreferences,
    dfc_attributes: list[str],
) -> LayoutPreferences:
    rank_direction = ["TB", "LR"]

    cont = st.container()
    col1, col2, col3 = st.columns(3)
    return LayoutPreferences(
        force_same_rank_for_event_class=cont.checkbox(
            "Force same rank per activity", value=defaults.force_same_rank_for_event_class, help="If enabled, all nodes of the same EventType will be on the same rank/level. (The rank is not exlusively reserved for that EventType though, which is limitation of the underlying graphviz engine.)"
        ),
        force_process_start_end_same_rank=cont.checkbox(
            "Force same rank for process estart/end", value=False, help="If enabled, all start nodes will be on the same rank, and all end nodes will be on the same rank."
        ),
        sort_event_classes_by_frequency=cont.checkbox(
            "Sort nodes by frequency", value=True, help="Influences the layout heuristics"
        ),
        sort_connections_by_frequency=cont.checkbox(
            "Sort edges by frequency", value=True, help="Influences the layout heuristics"
        ),
        rank_direction=col1.selectbox(
            "Graph direction",
            options=rank_direction,
            index=rank_direction.index(defaults.rank_direction),
            help="Direction of the graph layout: Top to Bottom (TB), Left to Right (LR)",
        ),
        weight_attribute=(
            st.selectbox("Weight attribute", options=dfc_attributes, index=dfc_attributes.index(defaults.weight_attribute))
            if st.toggle("Set edge weight", value=(defaults.weight_attribute is not None), help="Used during layout computation, higher weight means 'shorter' and 'straighter' edge. Should be nummeric attribute.")
            else None
        ),
        node_separation=col2.number_input(
            "Node separation", min_value=0.1, max_value=5.0, step=0.1, value=0.5, help="Minimal horizontal spacing between nodes on the same rank/level"
        ),
        rank_separation=col3.number_input(
            "Rank separation", min_value=0.1, max_value=5.0, step=0.1, value=0.5, help="Minimal vertical spacing between ranks/levels"
        ),
        clustering_keys=(
            st.multiselect(
                "Clustering attributes [ordered]",
                options=defaults.allowed_clustering_attributes,
                default=defaults.clustering_attribute,
                help="Select attributes used to create subgraph clusters, order matters (e.g. ['EntityType', 'Location'] will create big clusters for each entity type and within each it will create sub-clusters for each location)",
            )
            if st.toggle("Enable clustering", value=True, help="Create subgraph clusters based on selected attributes")
            else []
        ),
    )


def preferences_group(
    *,
    queries: AbstractEKGRepository,
    class_type: str,
    default_layout_preferences_input: DefaultLayoutPreferences,
    default_connection_visuals: DefaultConnectionPreferences,
    default_event_class_visuals: DefaultEventClassPreferences,
) -> tuple[
    LayoutPreferences,
    DFCPreferences,
    EventClassPreferences,
    ov_filters.AbstractFilter,
    TokenReplayPreferences,
]:
    with st.expander("Layout preferences", expanded=False):
        dfc_attributes = queries.dfc_attributes(class_type)
        layout_preferences = layout_preferences_input(default_layout_preferences_input, dfc_attributes)

    with st.expander("DFC Appearance", expanded=False):
        edge_vis_preferences = dfc_appearance_input(
            queries.dfc_attributes(class_type), defaults=default_connection_visuals
        )

    with st.expander("Event Class Appearance", expanded=False):
        node_vis_preferences = event_class_appearance_input(
            queries.class_attributes(class_type), defaults=default_event_class_visuals
        )

    with st.expander("Animation preferences", expanded=False):
        show_only_sampled_elements_filter = ov_filters.DummyFilter.new(
            is_passing=not st.toggle(
                "Hide connections and classes not contained in the sample",
                help="If enabled, only the elements (nodes and edges) that are part of the sampled token traces will be shown in the visualization.",
            )
        )
        animation_preferences = animation_preferences_input()

    return (
        layout_preferences,
        edge_vis_preferences,
        node_vis_preferences,
        show_only_sampled_elements_filter,
        animation_preferences,
    )


def animation_preferences_input() -> TokenReplayPreferences:
    result = TokenReplayPreferences(
        animate_active_elements_flag=st.toggle("Animate process flow", value=False, help="If enabled, the active paths will play dashed animation to indicate the process flow."),
        animate_tokens_flag=st.toggle("Animate tokens", value=True, help="If enabled, tokens representing process instances will be animated along their paths in the process model."),
        token_animation_speed=25.5
        - st.slider(
            "Token replay speed", value=5.0, min_value=0.1, max_value=25.0, step=0.1, help="Controls how fast the tokens move along their paths. Higher values result in faster animations."
        ),
        token_animation_alignment=(
            alignment := st.segmented_control(
                "Token replay alignment",
                options=["At-once", "Real-time"],
                default="Real-time",
                help="Determines how the start times of token animations are aligned. 'At-once' means all tokens start simultaneously, while 'Real-time' staggers the start times based on their actual occurrence times."
            )
        ),
        fixed_animation_duration=st.toggle(
            "Fixed transition duration", value=False, disabled=(alignment != "At-once"),
            help="If enabled, all transitions will have the same duration regardless of their actual process duration. This is only applicable when 'At-once' alignment is selected."
        ),
    )
    if alignment != "At-once":
        result.fixed_animation_duration = False

    return result


def token_replay_input(
    queries: AbstractEKGRepository,
    class_type,
    ui_preferences: TokenReplayManager,
    token_replay_preferences: TokenReplayPreferences,
) -> tuple[
    ov_filters.AbstractFilter,
    list[Token] | None,
    ReplayMetadata | None,
    list[str] | None,
]:
    with st.expander("Entities to animate", expanded=True):
        sampled_entity_ids = []
        st.text("Sample properties")
        for name, callback in ui_preferences.samplers.items():
            (
                col1,
                col2,
            ) = st.columns([0.5, 0.5], vertical_alignment="center")
            enabled = col1.checkbox(f"{name}", value=False)
            sample_size = col2.number_input(
                "No. Samples",
                value=10,
                min_value=1,
                max_value=2500,
                key=f"{name}_sample",
                label_visibility="collapsed",
            )
            if enabled:
                samples = callback(class_type, sample_size)
                st.write(f"Found samples: {len(samples)}")
                sampled_entity_ids.extend(samples)

        if sampled_entity_ids:
            st.write(f"Found samples total: {len(sampled_entity_ids)}")

        if len(sampled_entity_ids) == 0:
            return ov_filters.DummyFilter.new(is_passing=False), None, None, None

        sampled_traces = queries.get_process_executions(class_type, sampled_entity_ids)
        active_element_ids, token_animation_segments, replay_metadata = (
            ui_preferences.token_animation_generator(
                sampled_traces[0],
                sampled_traces[1],
                sampled_traces[2],
                token_replay_preferences,
            )
        )
        element_filter = ov_filters.MatchFilter.new(
            attribute="element_id",
            is_enabled=True,
            skip_on_empty=True,
            values=active_element_ids,
        )

        return (
            element_filter,
            token_animation_segments,
            replay_metadata,
            active_element_ids,
        )


def attribute_range_filter_input(
    label: str,
    for_entity_type: str,
    on_attribute: str,
    min_value: int | float,
    max_value: int | float,
    is_enabled_by_default: bool = False,
    value: tuple[int | float, int | float] | None = None,
    key: str = None,
):
    is_enabled = st.checkbox(
        label,
        value=is_enabled_by_default,
        key=None if key is None else f"{key}_enabled",
    )
    if min_value == max_value:
        range_filter = ov_filters.DummyFilter.new(is_passing=True)
    else:
        range_filter = ov_filters.RangeFilter.new(
            attribute=on_attribute,
            is_enabled=is_enabled,
            rng=st.slider(
                label=label,
                disabled=not is_enabled,
                min_value=max(0, min_value),
                max_value=max_value,
                value=value,
                label_visibility="collapsed",
                key=key,
            ),
        )

    return ov_filters.AndFilter.new(
        [
            ov_filters.MatchFilter.new(
                attribute="EntityType", values=[for_entity_type]
            ),
            range_filter,  # if is_enabled else ov_filters.DummyFilter.new(is_passing=True)
        ]
    )


def animation_segments(token_animation_segments: list[Token]):
    entity_selector = st.selectbox(
        "Select animation entity",
        options=map(lambda value: value.entity_id, token_animation_segments),
        index=0,
    )
    detail = next(x for x in token_animation_segments if x.entity_id == entity_selector)
    st.dataframe(detail.segments)


def event_class_detail(
    queries: AbstractEKGRepository, class_type, selected_element_id: str
):
    event_class = queries.get_event_class(selected_element_id)
    if event_class is None:
        return

    st.write("### Class Detail")
    event_class_attributes = queries.class_attributes(class_type)
    data = {key: event_class[key] for key in event_class_attributes}
    data["ElementId"] = selected_element_id
    st.table(data)


def event_class_related_entities(
    queries: AbstractEKGRepository,
    selected_element_id: str,
):
    entity_count = queries.get_entities_for_event_class_count(selected_element_id)

    # Make this pagination
    st.metric("Related entities", entity_count)

    # Pagination inputs
    col1, col2 = st.columns([0.8, 0.2])
    limit = col2.number_input(
        "Entities per page",
        min_value=1,
        max_value=100,
        value=100,
        step=1,
        key="entities_per_page_ec",
    )
    options = [
        f"{limit * (x - 1)}-{x * limit + 1}"
        for x in range(1, entity_count // limit + 2)
    ]
    selection = col1.segmented_control(
        "Select page", options=options, default=options[0]
    )
    offset = int(selection.split("-")[0])

    entities = queries.get_entities_for_event_class(selected_element_id, limit, offset)
    st.dataframe(entities)


def dfc_detail(
    queries: AbstractEKGRepository, class_type: str, selected_element_id: str
):
    edge = queries.get_dfc(selected_element_id)
    if edge is None:
        return

    st.write("### DFC Detail")
    dfc_attributes = queries.dfc_attributes(class_type)
    data = {key: edge["dfc_relation"][key] for key in dfc_attributes}
    data["ElementId"] = selected_element_id
    st.table(data)


def dfc_related_entities(queries: AbstractEKGRepository, selected_element_id: str):
    entity_count = queries.get_entities_for_dfc_count(selected_element_id)

    # Make this pagination
    st.metric("Related entities", entity_count)

    # Pagination inputs
    col1, col2 = st.columns([0.8, 0.2])
    limit = col2.number_input(
        "Entities per page",
        min_value=1,
        max_value=100,
        value=100,
        step=1,
        key="entities_per_page_dfc",
    )
    options = [
        f"{limit * (x - 1)}-{x * limit + 1}"
        for x in range(1, entity_count // limit + 2)
    ]
    selection = col1.segmented_control(
        "Select page", options=options, default=options[0]
    )
    offset = int(selection.split("-")[0])

    entities = queries.get_entities_for_dfc(selected_element_id, limit, offset)
    st.dataframe(entities)


def full_proclet_view(
    *, graph_payload, queries, class_type, token_animation_segments
):
    event = interactive_proclet_graph(graph_payload)
    wire_graph_event(event)

    tab1, tab2 = st.tabs(["Selection details", "Animation segments"])
    with tab1:
        if not st.session_state.selected_node and not st.session_state.selected_edge:
            st.info("Select a class or a path to see details")

        if st.session_state.selected_node:
            event_class_detail(
                queries,
                class_type,
                st.session_state.selected_node,
            )
            event_class_related_entities(queries, st.session_state.selected_node)

        if st.session_state.selected_edge:
            dfc_detail(queries, class_type, st.session_state.selected_edge)
            dfc_related_entities(queries, st.session_state.selected_edge)

        if st.session_state.selected_token:
            st.write("### Token Detail")
            st.write(f"Selected token: {st.session_state.selected_token}")
            trace = queries.get_entity_trace(class_type, st.session_state.selected_token)
            st.write(trace)

    with tab2:
        if token_animation_segments:
            animation_segments(token_animation_segments)


def ekg_stats(queries: AbstractEKGRepository, class_type: str):
    class_attrs = set(queries.class_attributes(class_type=class_type))
    col1, _, _ = st.columns(3)
    col1.metric("Selected Proclet", class_type, help="The selected proclet class type")

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


def debug_objektviz_backend(
    config: BackendConfig, db_nodes: list, db_edges: list, final_dot_source: str
):
    st.write(config)
    st.write("Node data coming from database")
    st.json(db_nodes, expanded=False)
    st.write("Edges data coming from database")
    st.json(db_edges, expanded=False)
    with st.expander("Dot source"):
        st.text_area(final_dot_source, disabled=True)


@st.cache_data
def _cached_histogram(
    values: list[float], bins: int, color: str, title: str, use_log: bool
):
    fig, ax = plt.subplots(figsize=(6, 3))
    ax.hist(values, bins=bins, color=color, edgecolor="black", alpha=0.8)
    if use_log:
        ax.set_yscale("log")
    ax.set_title(title)
    ax.set_xlabel("Frequency")
    ax.set_ylabel("Count")
    return fig


def entity_distribution_plot(
    nodes: list[dict],
    edges: list[dict],
    entity_types: list[str],
):
    st.write("## Entity Type Distributions")
    st.info("Is looks like caching so many figures causes issues for the process model rendering, disable this component if you face such problems.", icon="⚠️")
    # Validate edges have required attributes for this component to work
    assert_attribute_exists(nodes, "EntityType")
    assert_attribute_exists(nodes, "frequency")

    assert_attribute_exists(edges, "EntityType")
    assert_attribute_exists(edges, "frequency")

    def _display_stats(stats: dict):
        st.write(f"Count: {stats['count']}")
        st.write(f"Mean: {stats['mean']:.2f}")
        st.write(f"Median: {stats['median']:.2f}")
        st.write(f"Min: {stats['min']:.0f}  Max: {stats['max']:.0f}")

    def _stats(values: list[float]):
        n = len(values)
        if n == 0:
            return {"count": 0, "mean": 0, "median": 0, "min": 0, "max": 0}
        s = sum(values)
        sv = sorted(values)
        mean = s / n
        median = sv[n // 2] if n % 2 == 1 else (sv[n // 2 - 1] + sv[n // 2]) / 2
        return {"count": n, "mean": mean, "median": median, "min": sv[0], "max": sv[-1]}

    bins = st.slider(
        "Histogram bins", min_value=5, max_value=200, value=50, step=1, key="dist_bins"
    )
    log_scale = st.checkbox("Use log scale for y axis", value=False, key="dist_log")

    # Nodes / EventType distributions
    for entity_type in entity_types:
        event_class_col, dfc_col = st.columns(2)
        with event_class_col:
            type_nodes = [node for node in nodes if node["EntityType"] == entity_type]
            values = [float(x["frequency"]) for x in type_nodes]
            stats = _stats(values)

            col_hist, col_stats = st.columns([3, 1])
            with col_hist:
                fig = _cached_histogram(
                    values, bins, "tab:blue", f"EventType for {entity_type}", log_scale
                )
                st.pyplot(fig, clear_figure=True)
                plt.close(fig)
            with col_stats:
                _display_stats(stats)

        with dfc_col:
            type_edges = [edge for edge in edges if edge["EntityType"] == entity_type]
            values = [float(x["frequency"]) for x in type_edges]
            stats = _stats(values)

            col_hist, col_stats = st.columns([3, 1])
            with col_hist:
                fig = _cached_histogram(
                    values, bins, "tab:green", f"DFC for {entity_type}", log_scale
                )
                st.pyplot(fig, clear_figure=True)
                plt.close(fig)
            with col_stats:
                _display_stats(stats)


@st.cache_data
def plot_frequency_distribution(values: list[int | float]):
    fig, ax = plt.subplots(figsize=(6, 3), constrained_layout=True)
    ax.hist(values, bins=100, color="tab:blue", edgecolor="black", alpha=0.8)
    return fig


def frequency_filter_per_entity_type(
    entity_types: list[str],
    elements: list[dict],
    key_prefix: str = None,
) -> ov_filters.AbstractFilter:
    # Validate edges have required attributes for this component to work
    assert_attribute_exists(elements, "EntityType")
    assert_attribute_exists(elements, "frequency")

    entity_types = sorted(entity_types)
    filters = []

    for entity_type in entity_types:
        elements_of_type = [
            element for element in elements if element["EntityType"] == entity_type
        ]
        if not elements_of_type:
            continue

        max_freq = max(elements["frequency"] for elements in elements_of_type)
        min_freq = min(elements["frequency"] for elements in elements_of_type)
        values = [elements["frequency"] for elements in elements_of_type]

        # fig, ax = plt.subplots(figsize=(6, 3), constrained_layout=True)
        # ax.hist(values, bins=100, color='tab:blue', edgecolor='black', alpha=0.8)
        fig = plot_frequency_distribution(values)
        st.pyplot(fig)
        plt.close(fig)

        filter_label = f"{entity_type}"
        range_filter = attribute_range_filter_input(
            label=filter_label,
            for_entity_type=entity_type,
            on_attribute="frequency",
            min_value=min_freq,
            max_value=max_freq,
            value=(int(np.median(values)), max_freq),
            is_enabled_by_default=True,
            key=None
            if key_prefix is None
            else f"{key_prefix}_{entity_type}_frequency_filter",
        )

        filters.append(range_filter)

    return ov_filters.OrFilter.new(filters)


def trace_variants(*, class_type):
    pass
    # raise NotImplementedError("Is this usefull to reiplment")
    # st.write("Trace variants for in scope events (START  ↦ ...  ↦ Shipped To Customer)")
    # st.write("For class type: ", class_type)
    # col0, col1, col2, col3 = st.columns(4)
    # with col0:
    #     part_family = st.text_input("For part family", value=None)
    #
    # with col1:
    #     limit = st.slider("Top N traces (DoA): ", value=10, min_value=1, max_value=100, key='doa_material_slider')
    #
    # with col2:
    #     limit_prevented_doa = st.slider("Top N traces (Prevented DoA): ", value=10, min_value=1, max_value=100,
    #                                     key='prevented_doa_material_slider')
    # with col3:
    #
    #     limit_doa_material = st.slider("Top N traces (DoA Material Type): ", value=10, min_value=1, max_value=100,
    #                                    key='doa_material_type_slider')
    #
    # def map_trace_variant(x):
    #     variant = "Empty"
    #     if x['TraceVariant']:
    #         variant = '  ↦  '.join([y[0] for y in x['TraceVariant']] + [x['TraceVariant'][-1][1]])
    #
    #     return {
    #         'Freq': x['Frequency'],
    #         'No. Activities': x['NumberOfActivities'],
    #         'TraceVariant': variant,
    #         'Cases': x['Cases']
    #     }
    #
    #
    # column_config = {
    #     'Freq': st.column_config.NumberColumn(width='small'),
    #     'No. Activities': st.column_config.NumberColumn(width='small'),
    #     'TraceVariant': st.column_config.TextColumn(width='large'),
    #     'Cases': st.column_config.ListColumn(),
    # }
    #
    # st.write("Doa Trace Variants")
    # doa_trace_variants = trace_variants(class_type,'DoA', limit, part_family)
    # doa_trace_variants = map(map_trace_variant, doa_trace_variants)
    # st.dataframe(doa_trace_variants, column_config=column_config)
    #
    # st.write("PreventedDoA Trace Variants")
    # doa_trace_variants = trace_variants(class_type,'PreventedDoA', limit_prevented_doa, part_family)
    # doa_trace_variants = map(map_trace_variant, doa_trace_variants)
    # st.dataframe(doa_trace_variants, column_config=column_config)
    #
    # st.write("DoAMaterialType Trace Variants")
    # doa_trace_variants = trace_variants(class_type,'DoAMaterialType', limit_doa_material, part_family)
    # doa_trace_variants = map(map_trace_variant, doa_trace_variants)
    # st.dataframe(doa_trace_variants, column_config=column_config)
    # st.divider()
