from dataclasses import dataclass, field
from typing import Dict

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
    default_clustering_attribute: str = "EntityType"


@dataclass
class DefaultShadingPreferences:
    # Group by EntityType by default
    group_by: str

    # For each value of the grouping attribute, specify a color map to use (matplotlib colormap names)
    # There is no sensible default here, as it depends on the data
    color_map: dict[str, str]


@dataclass
class DefaultConnectionPreferences:
    pen_range: tuple[int, int] = (2, 10)  # Edge line thickness range
    title: str = "frequency"  # Title shows DFC Type by default
    shading: str = "frequency"  # Attributes used for edge shading (must be numeric)


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
