from dataclasses import dataclass, field
from typing import Dict, Literal
import streamlit as st

from objektviz.backend.adaptors.shared import AbstractEKGRepository
from objektviz.frontend import TokenReplayPreferences, Token, ReplayMetadata

# (class_type, sample_size) -> entity IDs
type TokenAnimationSamplerT = callable[[str, str], list[str]]

# (token traces, start_date, end_date, animation_preferences) -> active element IDs, tokens, replay metadata
# active element IDs -> what ActivityClasses and DFCs are involved in the token flows
# TODO define traces format
type TokenAnimationGeneratorT = callable[
    [list[dict], str, str, TokenReplayPreferences],
    tuple[list[str], list[Token], ReplayMetadata],
]


@dataclass
class TokenReplayManager:
    # We can define different samplers for different subpopulations of cases
    # E.g. base on EntityType or case outcome
    samplers: Dict[str, TokenAnimationSamplerT]
    token_animation_generator: TokenAnimationGeneratorT


@dataclass
class DefaultLayoutPreferences:
    allowed_clustering_attributes: list[str] = field(
        default_factory=lambda: ["EntityType", "EventType"]
    )
    clustering_attribute: str = "EntityType"
    weight_attribute: str | None = "frequency"  # If set to none, there is no weighting
    rank_direction: str = "TB"  # Top to Bottom
    force_same_rank_for_event_class: bool = True
    force_process_start_end_same_rank: bool = True


@dataclass
class DefaultShadingPreferences:
    # Group by EntityType by default
    group_by: str

    # For each value of the grouping attribute, specify a color map to use (matplotlib colormap names)
    # There is no sensible default here, as it depends on the data
    color_map: dict[str, tuple[str, str]]


@dataclass
class DefaultConnectionPreferences:
    pen_range: tuple[int, int] = (2, 10)  # Edge line thickness range
    title: str = "frequency"  # Title shows DFC Type by default
    shading: str = "frequency"  # Attributes used for edge shading (must be numeric)
    hide_sync_edges: bool = False  # Whether to hide edges that represent synchronous relationships (e.g. between an event and its entity)


@dataclass
class DefaultEventClassPreferences:
    title: str = "EventType"  # Title shows EventType by default
    shading_attr: str = (
        "frequency"  # Attributes used for node shading (must be numeric)
    )
    small_caption_left: str = "EntityType"  # Left caption shows EntityType by default
    small_caption_right: str = "frequency"  # Right caption shows frequency by default
    icon_map: Dict[str, Dict[str, str]] = field(
        default_factory=dict
    )  # ATTR NAME -> ATTR VALUE -> ICON


def assert_attribute_exists(lst: list[dict], attribute_name: str):
    if not all(attribute_name in item for item in lst):
        raise AttributeError(
            f"Attribute '{attribute_name}' not found in all items. "
            f"This attribute is required for the component to render correctly."
        )


@st.cache_data
def get_class_ordering(_queries: AbstractEKGRepository, class_type: str , entity_types: list[str]):
    eager_sorting:dict[str, list] = dict()
    for entity_type in entity_types:
        eager_sorting[entity_type] = _queries.get_avg_class_order(class_type, entity_type)
        if not eager_sorting[entity_type]: # if there is no order information, we provide a fallback (no specific order)
            eager_sorting[entity_type] = _queries.get_all_activity_names(class_type, entity_type)

    return eager_sorting


@st.cache_data
def get_cluster_ordering(_queries: AbstractEKGRepository, class_type: str, sort_groups_by: Literal['Alphabetical', 'Frequency']):
    if sort_groups_by == "Alphabetical":
        return sorted(_queries.get_entity_types(class_type))
    elif sort_groups_by == "Frequency":
        return sorted(
            _queries.get_entity_types(class_type),
            key=lambda item: _queries.get_entity_type_frequency(class_type, item),
            reverse=True,
        )
    elif isinstance(sort_groups_by, tuple) and len(sort_groups_by) == 2:
        attribute_name, desired_order = sort_groups_by
        if attribute_name != "EntityType":
            raise ValueError("Currently only sorting by EntityType is supported.")

        entity_types = _queries.get_entity_types(class_type)

        # Ensure all entity types are included in the desired order list
        if not all(et in desired_order for et in entity_types):
            raise ValueError("All entity types must be included in the desired order list.")

        # Sort based on the index in the desired order list
        return sorted(entity_types, key=lambda et: desired_order.index(et))

    raise ValueError(f"Invalid value for sort_groups_by: {sort_groups_by}")
