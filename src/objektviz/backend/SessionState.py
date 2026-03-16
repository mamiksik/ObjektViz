import dataclasses


@dataclasses.dataclass
class SessionState:
    selected_edge: str = None
    selected_class: str = None

