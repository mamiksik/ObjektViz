import abc
from abc import abstractmethod
from datetime import datetime


class CypherQueries:
    """ This is a collection of selected queries that are vendor independent """
    @staticmethod
    def get_class_attributes() -> str:
        return """
            MATCH (c: Class {Type: $ClassType})
            UNWIND keys(c) as key
            RETURN collect(DISTINCT key)
        """

    @staticmethod
    def get_classes_count() -> str:
        return """
            MATCH (c: Class {Type: $ClassType})
            RETURN count(DISTINCT c) as Count
        """

    @staticmethod
    def get_dfc_attributes() -> str:
        return """
            MATCH (:Class {Type: $ClassType})-[r:DF_C]->(:Class {Type: $ClassType})
            UNWIND keys(r) as key
            RETURN collect(DISTINCT key)
        """


    @staticmethod
    def get_dfc_count() -> str:
        return """
            MATCH (: Class {Type: $ClassType})-[r:DF_C]->(: Class {Type: $ClassType})
            RETURN count(DISTINCT r) as Count
        """

    @staticmethod
    def get_end_class_count() -> str:
        return """
            MATCH (c: Class {Type: $ClassType})
            WHERE c.EndCount IS NOT NULL AND c.EndCount > 0
            RETURN count(DISTINCT c) as Count
        """

    @staticmethod
    def get_entity_types() -> str:
        return """
            MATCH (c: Class)
            WITH DISTINCT c.EntityType as entityType
            RETURN entityType
        """

    @staticmethod
    def get_entity_types_for_class() -> str:
        return """
            MATCH (c: Class {Type: $ClassType})
            WITH DISTINCT c.EntityType as entityType
            RETURN entityType
        """

    @staticmethod
    def get_start_class_count() -> str:
        return """
            MATCH (c: Class {Type: $ClassType})
            WHERE c.StartCount IS NOT NULL AND c.StartCount > 0
            RETURN count(DISTINCT c) as Count
        """

    @staticmethod
    def get_sync_edge_count() -> str:
        return """
            MATCH (:Class {Type: $ClassType})-[r:SYNC]->(: Class {Type: $ClassType})
            RETURN count(DISTINCT r) as Count
        """

    @staticmethod
    def get_proclet_types() -> str:
        return """
            MATCH (c: Class)
            RETURN collect(DISTINCT c.Type) as Types
        """


class AbstractEKGRepository[NodeT, EdgeT](abc.ABC):
    """Abstract base class defining repository operations for Event Knowledge Graphs (EKG).

    Implementations of this repository provide vendor-specific access (e.g. Neo4j,
    KuzuDB) to retrieve classes, edges, entities and process execution data used by
    the ObjektViz backend.

    Type parameters:
        NodeT: concrete type used to represent nodes returned by the adaptor.
        EdgeT: concrete type used to represent edges returned by the adaptor.

    All methods raised here describe the contract (inputs, outputs and error modes)
    that concrete adaptors must follow.
    """

    @abstractmethod
    def get_class_attributes(self, class_type: str) -> list[str]:
        """ Return a list of attribute names available on Class nodes of the given type.

        Parameters
        - class_type: the :Class type

        Returns
        - A list of attribute (property) names as strings.
        """
        pass

    @abstractmethod
    def get_classes_count(self, class_type: str) -> int:
        """Return the number of distinct :Class nodes with the given type.

        Parameters
        - class_type: the :Class type

        Returns
        - Integer count (>= 0). If the class type is unknown, return 0.
        """
        pass

    def get_class_names(self, class_type: str) -> list[str]:
        """(Deprecated / optional) Return names/identifiers of Class nodes for a type.

        Historically used to fetch a list of class node identifiers. Current code
        base marks this as not used; concrete adaptors may choose to implement it.

        Parameters
        - class_type: the :Class type

        Returns
        - A list of class identifier strings. Default implementation raises
          NotImplementedError to indicate optional support.
        """
        raise NotImplementedError # Not used anymore?

    @abstractmethod
    def get_dfc(self, dfc_id: str) -> dict | None:
        """Fetch a single :DF_C element by its identifier.

        Parameters
        - dfc_id: identifier for the DF_C relationship or edge of interest.

        Returns
        - A dictionary representing the DF_C element (including properties). Return
          None when the requested dfc_id does not exist.
        """
        pass

    @abstractmethod
    def get_dfc_attributes(self, class_type: str) -> list[str]:
        """Return attribute names defined on :DF_C

        Parameters
        - class_type: the type of :Class

        Returns
        - List of distinct :DF_C  propert names
        """
        pass

    @abstractmethod
    def get_dfc_count(self, class_type: str) -> int:
        """Return the number of :DF_C edges between :Class nodes

        Parameters
        - class_type: :Class type

        Returns
        - Integer count (>= 0).
        """
        pass

    @abstractmethod
    def get_end_class_count(self, class_type: str) -> int:
        """ Return how many :Class nodes have 'EndCount' property > 0

        Parameters
        - class_type: Class.Type to query.

        Returns
        - Integer count (>= 0).
        """
        pass

    @abstractmethod
    def get_entity_sample(self, class_type: str, sample_size: int) -> list[str]:
        """ Return a random sample of :Entity nodes identifiers.

        Parameters
        - class_type: the :Class type
        - sample_size: maximum number of entities to return (implementation may return
          fewer if not enough entities exist).

        Returns
        - A list of entity identifiers (strings)
        """
        pass

    @abstractmethod
    def get_entity_trace(self, class_type: str, entity_element_id: str) -> dict | None:
        """ Retrieve the full trace (sequence of events/elements) for a single entity.
        TODO: More detail documentation (the output shape is quite complex)

        Parameters
        - class_type: Class.Type that scopes the trace (helps locate the entity).
        - entity_element_id: identifier of the entity whose trace is requested.
        """
        pass

    @abstractmethod
    def get_entity_types(self, class_type: str) -> list[str]:
        """Return distinct EntityType values for :Class nodes, optionally scoped.

        Parameters
        - class_type: when provided, restrict the lookup to that :Class type. If
          implementations ignore the parameter, they may return all entity types.

        Returns
        - A list of entity type strings.
        """
        pass

    @abstractmethod
    def get_entities_for_dfc(self, dfc_id: str, limit: int, skip: int) -> list[NodeT]:
        """ Return a page of entity nodes whose events traverse the given :DF_C edge.

        Parameters
        - dfc_id: identifier of the DF_C relationship to filter by.
        - limit: maximum number of results to return.
        - skip: number of results to skip (for pagination).

        Returns
        - A list of NodeT values representing the matching entities.
        """
        pass

    @abstractmethod
    def get_entities_for_dfc_count(self, dfc_id: str) -> int:
        """Return the total number of entities that traverse the given :DF_C edge.

        Parameters
        - dfc_id: identifier of the DF_C relationship.

        Returns
        - Integer count (>= 0)
        """
        pass

    @abstractmethod
    def get_entities_for_event_class(
        self, class_id: str, limit: int, skip: int
    ) -> list[dict]:
        """Return a page of entity representations for a specific :Class.

        Parameters
        - class_id: identifier (node id or Type) of the event class to query.
        - limit: maximum number of entities to return.
        - skip: number of entities to skip (pagination offset).

        Returns
        - A list of dictionaries describing entities
        """
        pass

    @abstractmethod
    def get_entities_for_event_class_count(self, class_id: str) -> int:
        """Return the total number of entities associated with an :Class

        Parameters
        - class_id: identifier of the event class.

        Returns
        - Integer count (>= 0).
        """
        pass

    @abstractmethod
    def get_event_class(self, event_class_id: str) -> NodeT | None:
        """ Fetch a single event :Class node by id.

        Parameters
        - event_class_id: :Class identifier.

        Returns
        - A NodeT representing the class or None if not found.
        """
        pass

    @abstractmethod
    def get_start_class_count(self, class_type: str) -> int:
        """Return how many :Class nodes of the given type have property StartCount > 0

        Parameters
        - class_type: :Class type

        Returns
        - Integer count (>= 0).
        """
        pass

    @abstractmethod
    def get_sync_edge_count(self, class_type: str) -> int:
        """Return the number of :SYNC edges between :Class nodes of the given type.

        Since :SYNC edges are stored 2x between one pair of :Class nodes, the implementation should
        divide the result by 2

        Parameters
        - class_type: :Class type

        Returns
        - Integer count (>= 0).
        """
        pass

    @abstractmethod
    def get_proclet(self, class_type: str) -> tuple[list[NodeT], list[EdgeT], list[EdgeT]]:
        """ Retrieve a proclet model for a class type

        The proclet should return a triple: (nodes, edges, sync_edges) representing
        the process models to visualize.

        Parameters
        - class_type: :Class type

        Returns
        - Tuple of three lists: ([:Class], [:DF_C], [:SYNC]).
        """
        pass

    @abstractmethod
    def get_proclet_types(self) -> list[str]:
        """ Return a list of unique proclet types

        Returns
        - A list of unique proclet types.
        """
        pass



    @abstractmethod
    def get_process_executions(
        self, class_type: str, entity_ids: list[str]
    ) -> tuple[list[dict], datetime, datetime]:
        """Return process execution data for a set of entities.
        TODO: Document
        """
        pass





