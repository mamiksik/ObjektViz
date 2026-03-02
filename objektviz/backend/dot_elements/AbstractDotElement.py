import abc
from typing import TYPE_CHECKING, Literal, Mapping

if TYPE_CHECKING:
    from objektviz.backend.BackendConfig import BackendConfig
    from objektviz.backend.shaders.AbstractShader import AbstractShader

CROSS_CLUSTER_SENTINEL = object()


class AbstractDotElement[EntityT: Mapping](abc.ABC):
    """
    Shared representation of edge or node that is going to be parsed into a dot descriptor.
    It's a middle layer between the database and dot representation of node/edge
    [database query output]  --->     [AbstractDotElement]    --->     [dot descriptor]
    neo4j.graph.Relationship ---> DotEdge<AbstractDotElement> ---> "A -> B [label='A to B']"

    The two child classes DotNode and DotEdge take care of producing the final descriptor string,
    the included implementation internally holds the associated neo4j.graph.Entity from which
    the values for attributes are derived.

    the main function **to_dot** expects to receive lists of the DotNode and DotEdge, this is handy,
    if you want to adjust how the elements are rendered, since you can subclass the
    DotNode/DotEdge and pass instances of your subclass instead

    """

    fontname = "Helvetica"

    def __init__(
        self,
        entity: EntityT,
        shaders: dict[str, 'AbstractShader'],
        config: 'BackendConfig',
    ):
        self.entity = entity
        self.shaders = shaders
        self.config = config


    @property
    @abc.abstractmethod
    def dot_element_type(self) -> Literal["node", "edge"]:
        pass

    @property
    @abc.abstractmethod
    def element_id(self) -> str:
        pass

    @property
    @abc.abstractmethod
    def descriptive_label(self) -> str:
        pass

    @property
    @abc.abstractmethod
    def dot_descriptor(self) -> str:
        pass

    @property
    @abc.abstractmethod
    def is_visible(self) -> bool:
        pass

    @property
    def shader_key(self) -> str:
        return self.get(self.config.shader_groping_key)

    @property
    def frequency(self) -> int:
        # -1 is sentinel value meaning the frequency is undefined
        return self.get("frequency", -1)

    def get(self, name, default=None):
        return self.entity.get(name, default)

    def get_nesting_attr(self, name, default=None):
        return self.get(name, default)
