import abc
from abc import ABCMeta, abstractmethod
from datetime import datetime
from typing import Any


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
    @abstractmethod
    def get_class_attributes(self, class_type: str) -> list[str]:
        pass

    @abstractmethod
    def get_classes_count(self, class_type: str) -> int:
        pass

    def get_class_names(self, class_type: str) -> list[str]:
        raise NotImplementedError # Not used anymore?

    @abstractmethod
    def get_dfc(self, dfc_id: str) -> dict | None:
        pass

    @abstractmethod
    def get_dfc_attributes(self, class_type: str) -> list[str]:
        pass

    @abstractmethod
    def get_dfc_count(self, class_type: str) -> int:
        pass

    @abstractmethod
    def get_end_class_count(self, class_type: str) -> int:
        pass

    @abstractmethod
    def get_entity_sample(self, class_type: str, sample_size: int) -> list[str]:
        pass

    @abstractmethod
    def get_entity_trace(self, class_type: str, entity_element_id: str) -> dict | None:
        pass

    @abstractmethod
    def get_entity_types(self, class_type: str) -> list[str]:
        pass

    @abstractmethod
    def get_entities_for_dfc(self, dfc_id: str, limit: int, skip: int) -> list[NodeT]:
        pass

    @abstractmethod
    def get_entities_for_dfc_count(self, dfc_id: str) -> int:
        pass

    @abstractmethod
    def get_entities_for_event_class(
        self, class_id: str, limit: int, skip: int
    ) -> list[dict]:
        pass

    @abstractmethod
    def get_entities_for_event_class_count(self, class_id: str) -> int:
        pass

    @abstractmethod
    def get_event_class(self, event_class_id: str) -> NodeT | None:
        pass

    @abstractmethod
    def get_start_class_count(self, class_type: str) -> int:
        pass

    @abstractmethod
    def get_sync_edge_count(self, class_type: str) -> int:
        pass

    @abstractmethod
    def get_proclet(self, class_type: str) -> tuple[list[NodeT], list[EdgeT], list[EdgeT]]:
        pass

    @abstractmethod
    def get_proclet_types(self):
        pass




    @abstractmethod
    def get_process_executions(
        self, class_type: str, entity_ids: list[str]
    ) -> tuple[list[dict], datetime, datetime]:
        pass





