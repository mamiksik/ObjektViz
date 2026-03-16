import abc


class AbstractProxyNode(abc.ABC):
    @abc.abstractmethod
    @property
    def id(self) -> str:
        pass

    @abc.abstractmethod
    def get[T](self, attr: str, default: None) -> T:
        pass


class AbstractProxyEdge(abc.ABC):
    @abc.abstractmethod
    @property
    def id(self) -> str:
        pass

    @abc.abstractmethod
    @property
    def source_id(self) -> str:
        pass

    @abc.abstractmethod
    @property
    def target_id(self) -> str:
        pass



from neo4j.graph import Node, Relationship


class Neo4jProxyNode(AbstractProxyNode):
    def __init__(self, raw_node: Node):
        self.raw_node = raw_node


    @property
    def id(self) -> str:
        return self.raw_node.element_id


class Neo4jProxyEdge(AbstractProxyEdge):
    def __init__(self, raw_edge: Relationship):
        self.edge = raw_edge

    @property
    def id(self) -> str:
        return self.edge.element_id

    @abc.abstractmethod
    @property
    def source_id(self) -> str:
        return self.edge.start_node.element_id

    @abc.abstractmethod
    @property
    def target_id(self) -> str:
        return self.edge.end_node.element_id
