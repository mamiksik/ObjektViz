import dataclasses
from abc import ABC, abstractmethod


@dataclasses.dataclass(kw_only=True)
class AbstractFilter(ABC):
    """
    This is a based class for declarative filtering DSL
    With the subclasses you can define arbitrary filtering logic for the
    nodes and edges. These filters are then applied when generating the
    dot source code.

    Prefer using these filters over manually filtering the elements, since
    they play nicer with streamlit declarative API and in general make
    your life easier once you learn them

    e.g.
    root_node_filter = DummyFilter.new() # Dummy filter is always passing
    if st.checkbox("Filtering is enabled"):
        root_node_filter = AndFilter.new([
            MatchFilter.new(attribute="EntityType", ["Equipment"]),
            RangeFilter.new(
                attribute="EntityType",
                rng=st.slider("Freq. range", min_value=0.0, max_value=100.0),
            )
        ])


    """

    is_enabled: bool = True

    @abstractmethod
    def is_passing(self, entity):
        raise NotImplementedError
