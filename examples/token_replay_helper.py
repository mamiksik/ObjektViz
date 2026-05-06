from objektviz.backend.utils import get_dominant_color
from objektviz.frontend import (
    ReplayMetadata,
    Token,
    ReplaySegment,
    TokenReplayPreferences,
)

def generate_token_animation_segments(
    process_traces: list[dict],
    start_date,
    end_date,
    color_map: dict[str, tuple[str, str]],
    token_replay_preferences: TokenReplayPreferences,
) -> tuple[list[str], list[Token], ReplayMetadata]:
    """Generates token animation segments from process execution data. This is default implementation, each project will probably needs its own version."""
    active_element_ids = []
    tokens = []
    max_duration_sec = 0

    for trace in process_traces:
        active_element_ids.extend(trace.get("ActiveElementIds"))

        if token_replay_preferences.fixed_animation_duration:
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

        elif token_replay_preferences.token_animation_alignment == "At-once":
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
                    color=get_dominant_color(color_map[trace.get("Entity").get("type")]),
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
                entity_id=trace.get("Entity").get("id"),
                entity_type=trace.get("Entity").get("type"),
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
