from abc import ABCMeta, abstractmethod
from datetime import datetime
from typing import Any


class AbstractEKGRepository(metaclass=ABCMeta):
    """ An abstract repository for accessing event knowledge graphs,
        defining the necessary methods for retrieving information about classes,
        dfcs, etc...
    """


    @abstractmethod
    def class_attributes(self, class_type: str) -> list[str]:
        """Returns the list of attributes for class of given class type (e.g. EventType, Frequency ...)"""
        pass

    @abstractmethod
    def dfc_attributes(self, class_type: str) -> list[str]:
        """Returns the list of attributes for dfc of given class type (e.g. EventType, Frequency ...)"""
        pass

    @abstractmethod
    def class_names(self, class_type: str) -> list[str]:
        pass

    @abstractmethod
    def get_entity_types(self, class_type: str) -> list[str]:
        """Returns the list of entity types related to given class type (e.g. Loan Application, Workflow, ...)"""
        pass

    @abstractmethod
    def proclet(self, class_type: str) -> tuple[list[Any], list[Any], list[Any]]:
        """ Returns the proclet for given class type,
            this means list of all classes, dfcs and syncs of the given class type
        """
        pass

    @abstractmethod
    def get_process_executions(
        self, class_type: str, entity_ids: list[str]
    ) -> tuple[list[dict], datetime, datetime]:
        pass

    @abstractmethod
    def entity_sample(self, class_type: str, sample_size: int) -> list[str]:
        """ Returns a sample of entity ids for given class type,
            this might be used to compute sample traces for token replay
        """
        pass

    @abstractmethod
    def count_classes(self, class_type: str) -> int:
        """ Returns the number of unique EventTypes for given class type """
        pass

    @abstractmethod
    def count_dfc(self, class_type: str) -> int:
        """ Returns the number of unique DFCs for given class type """
        pass

    @abstractmethod
    def count_sync(self, class_type: str) -> int:
        """ Returns the number of unique Syncs for given class type """
        pass

    @abstractmethod
    def proclet_types(self):
        """ Returns the list of all available proclet types i.e. all registered values for class_type"""
        pass

    @abstractmethod
    def count_start_activities(self, class_type: str) -> int:
        """ Returns the number of unique EventTypes that are starting activities for given class type """
        pass

    @abstractmethod
    def count_end_activities(self, class_type: str) -> int:
        """ Returns the number of unique EventTypes that are ending activities for given class type """
        pass

    @abstractmethod
    def get_entities_for_dfc_count(self, dfc_id: str) -> int:
        """ Returns the number of entities related to given dfc_id, this might be used for pagination purposes """
        pass

    @abstractmethod
    def get_entities_for_dfc(self, dfc_id: str, limit: int, skip: int) -> list[dict]:
        """ Returns the list of entities related to given dfc_id"""
        pass

    @abstractmethod
    def get_entities_for_event_class_count(self, class_id: str) -> int:
        """ Returns the number of entities related to given event class id, this might be used for pagination purposes """
        pass

    @abstractmethod
    def get_entities_for_event_class(
        self, class_id: str, limit: int, skip: int
    ) -> list[dict]:
        """ Returns the list of entities related to given event class id"""
        pass

    @abstractmethod
    def get_dfc(self, dfc_id: str) -> dict | None:
        """ Returns the dfc with given id, or None if not found """
        pass

    @abstractmethod
    def get_event_class(self, event_class_id: str) -> dict | None:
        """ Returns the event class with given id, or None if not found """
        pass
