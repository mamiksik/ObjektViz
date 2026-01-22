from objektviz.frontend import (
    ReplayMetadata,
    Token,
    ReplaySegment,
    TokenReplayPreferences,
)

color_map = {
    "Invoice": "Blues",
    "Item": "Greens",
    "Order": "Purples",
    "Payment": "Oranges",
    "SupplierOrder": "Reds",
}

ATTR_VAL_TO_COLOR = {

    "Invoice": "#1f77b4",
    "Item": "#2ca02c",
    "Order": "#9467bd",
    "Payment": "#ff7f0e",
    "SupplierOrder": "#d62728",
}

def generate_token_animation_segments(
    data: list[dict],
    start_date,
    end_date,
    animation_preferences: TokenReplayPreferences,
) -> tuple[list[str], list[Token], ReplayMetadata]:
    """Generates token animation segments from process execution data. This is default implementation, each project will probably needs its own version."""
    active_element_ids = []
    tokens = []
    max_duration_sec = 0

    for trace in data:
        print(trace)
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
                element_id=trace.get("EntityElementId"),
                entity_id=trace.get("Entity").get("ID"),
                entity_type=trace.get("Entity").get("EntityType"),
                segments=segments,
                replay_duration_sec=replay_duration,
            )
        )

    replay_metadata = ReplayMetadata(
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat(),
        total_duration_sec=max_duration_sec,
    )

    return active_element_ids, tokens, replay_metadata
