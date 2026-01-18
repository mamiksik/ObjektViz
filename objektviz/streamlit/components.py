import functools
from typing import Callable

import streamlit as st

from objektviz.backend.BackendConfig import (
    LayoutPreferences,
    BackendConfig,
    ConnectionPreferences,
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
)
from objektviz.backend.dot_elements import DotNode, DotEdge
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
        class_type = st.selectbox("Proclet class type", options=proclet_types)

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
        "Shader type", options=["Percentile", "Normalized", "RobustScaler"]
    )

    # We know assigning lambdas to variables is not best practice, but here its just more handy
    if shader_type == "Normalized":
        shader_factory = (
            lambda config, leading_attribute, cmap: ov_shaders.NormalizedShader(
                config=config, leading_attribute=leading_attribute, cmap=cmap
            )
        )  # noqa: E731
    elif shader_type == "Percentile":
        shader_range = st.slider(
            "Percentile range",
            min_value=0.0,
            max_value=100.0,
            value=(5.0, 95.0),
            step=2.5,
        )
        shader_factory = (
            lambda shader_range,
            config,
            leading_attribute,
            cmap: ov_shaders.PercentileShader(
                config=config,
                leading_attribute=leading_attribute,
                cmap=cmap,
                percentile_range=shader_range,
            )
        )  # noqa: E731
        shader_factory = functools.partial(shader_factory, shader_range)
    elif shader_type == "RobustScaler":
        shader_factory = (
            lambda config, leading_attribute, cmap: ov_shaders.RobustShader(
                config=config, leading_attribute=leading_attribute, cmap=cmap
            )
        )  # noqa: E731
    else:
        raise ValueError(f"Shader type {shader_type} not recognized")

    return shader_factory


def edge_render_preference_input(
    edge_attributes: list[str], defaults: DefaultConnectionPreferences
) -> ConnectionPreferences:
    return ConnectionPreferences(
        pen_width_range=st.slider(
            "Pen with range", min_value=1, max_value=30, value=defaults.pen_range
        ),
        caption=st.selectbox(
            "Edge attr",
            options=edge_attributes,
            index=edge_attributes.index(defaults.title),
        ),
        shading_attr=st.selectbox(
            "Edge shading",
            options=edge_attributes,
            index=edge_attributes.index(defaults.shading),
        ),
        use_x_labels=st.toggle("Use xlabels [labels are ignored while routing]"),
    )


def node_render_preference_input(
    node_attributes: list[str], defaults: DefaultEventClassPreferences
) -> EventClassPreferences:
    return EventClassPreferences(
        shading_attr=st.selectbox(
            "Node shading",
            options=node_attributes,
            index=node_attributes.index(defaults.shading_attr),
        ),
        title=st.selectbox(
            "Node tile",
            options=node_attributes,
            index=node_attributes.index(defaults.title),
        ),
        caption_left=st.selectbox(
            "Node caption left",
            options=node_attributes,
            index=node_attributes.index(defaults.small_caption_left),
        ),
        caption_right=st.selectbox(
            "Node caption right",
            options=node_attributes,
            index=node_attributes.index(defaults.small_caption_right),
        ),
        icon_map=defaults.icon_map,
    )


def layout_preferences_input(
    default_layout_preferences_input: DefaultLayoutPreferences,
) -> LayoutPreferences:
    cont = st.container()
    col1, col2 = st.columns(2)
    return LayoutPreferences(
        force_same_rank_for_event_class=cont.checkbox(
            "Force same rank per activity", value=False
        ),
        force_process_start_end_same_rank=cont.checkbox(
            "Force same rank for process estart/end", value=False
        ),
        sort_event_classes_by_frequency=cont.checkbox(
            "Sort nodes by frequency", value=True
        ),
        sort_connections_by_frequency=cont.checkbox(
            "Sort edges by frequency", value=True
        ),
        node_separation=col1.number_input(
            "Node separation", min_value=0.1, max_value=5.0, step=0.1, value=0.5
        ),
        rank_separation=col2.number_input(
            "Rank separation", min_value=0.1, max_value=5.0, step=0.1, value=0.5
        ),
        clustering_keys=(
            st.multiselect(
                "Clustering attrs [ordered]",
                options=default_layout_preferences_input.allowed_clustering_attributes,
                default=default_layout_preferences_input.default_clustering_attribute,
            )
            if st.toggle("Enable clustering", value=True)
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
    ConnectionPreferences,
    EventClassPreferences,
    ov_filters.AbstractFilter,
    TokenReplayPreferences,
]:
    with st.expander("Layout preferences", expanded=False):
        layout_preferences = layout_preferences_input(default_layout_preferences_input)

    with st.expander("DFC Appearance", expanded=False):
        edge_vis_preferences = edge_render_preference_input(
            queries.dfc_attributes(class_type), defaults=default_connection_visuals
        )

    with st.expander("Event Class Appearance", expanded=False):
        node_vis_preferences = node_render_preference_input(
            queries.class_attributes(class_type), defaults=default_event_class_visuals
        )

    with st.expander("Animation preferences", expanded=False):
        show_only_sampled_elements = ov_filters.DummyFilter.new(
            is_passing=not st.toggle(
                "Hide connections and classes not contained in the sample"
            )
        )
        animation_preferences = animation_preferences_input()

    return (
        layout_preferences,
        edge_vis_preferences,
        node_vis_preferences,
        show_only_sampled_elements,
        animation_preferences,
    )


def animation_preferences_input() -> TokenReplayPreferences:
    result = TokenReplayPreferences(
        animate_active_elements_flag=st.toggle("Animate process flow", value=False),
        animate_tokens_flag=st.toggle("Animate tokens", value=True),
        token_animation_speed=25.5
        - st.slider(
            "Animation speed", value=5.0, min_value=0.1, max_value=25.0, step=0.1
        ),
        token_animation_alignment=(
            alignment := st.segmented_control(
                "Animation time alignment",
                options=["At-once", "Real-time"],
                default="Real-time",
            )
        ),
        fixed_animation_duration=st.toggle(
            "Fixed transition duration", value=False, disabled=(alignment != "At-once")
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
    entity_type: str,
    attr: str,
    rng: tuple[int, int],
    default_is_enabled=False,
):
    range_filter = ov_filters.DummyFilter.new(is_passing=False)
    if rng[0] is not None and rng[1] is not None and rng[0] != rng[1] and rng[1] != 1:
        is_enabled = st.checkbox(label, value=default_is_enabled)

        default = int((rng[1] - rng[0]) / 2)
        range_filter = ov_filters.RangeFilter.new(
            attribute=attr,
            is_enabled=is_enabled,
            rng=st.slider(
                label=label,
                disabled=not is_enabled,
                min_value=1,
                max_value=max(0, rng[0]),
                value=(default, rng[1]),
                label_visibility="collapsed",
            ),
        )

    return ov_filters.OrFilter.new(
        [
            ov_filters.NotFilter.new(
                ov_filters.MatchFilter.new(attribute="EntityType", values=[entity_type])
            ),
            range_filter,
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
    nodes: list[DotNode], class_attributes: list[str], selected_element_id: str
):
    node = next(
        (node for node in nodes if node.element_id == selected_element_id), None
    )
    if node is None:
        return

    st.write("### Class detail")
    data = {key: node.entity[key] for key in class_attributes}
    data["ElementId"] = node.element_id
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
    edges: list[DotEdge], dfc_attributes: list[str], selected_element_id: str
):
    edge = next(
        (edge for edge in edges if edge.element_id == selected_element_id), None
    )
    if edge is None:
        return

    st.write("### DFC Detail")
    data = {key: edge.entity[key] for key in dfc_attributes}
    data["ElementId"] = edge.element_id
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
    *, graph_payload, nodes, edges, queries, class_type, token_animation_segments
):
    event = interactive_proclet_graph(graph_payload)
    wire_graph_event(event)

    tab1, tab2 = st.tabs(["Selection details", "Animation segments"])
    with tab1:
        if not st.session_state.selected_node and not st.session_state.selected_edge:
            st.info("Select a class or a path to see details")

        if st.session_state.selected_node:
            event_class_detail(
                nodes,
                queries.class_attributes(class_type),
                st.session_state.selected_node,
            )
            event_class_related_entities(queries, st.session_state.selected_node)

        if st.session_state.selected_edge:
            dfc_detail(
                edges,
                queries.dfc_attributes(class_type),
                st.session_state.selected_edge,
            )
            dfc_related_entities(queries, st.session_state.selected_edge)

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
