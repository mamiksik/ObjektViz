from abc import ABCMeta, abstractmethod
from datetime import datetime
from typing import Any


class AbstractEKGRepository(metaclass=ABCMeta):
    @abstractmethod
    def class_attributes(self, class_type: str) -> list[str]:
        pass

    @abstractmethod
    def dfc_attributes(self, class_type: str) -> list[str]:
        pass

    @abstractmethod
    def class_names(self, class_type: str) -> list[str]:
        pass

    @abstractmethod
    def get_entity_types(self, class_type: str) -> list[str]:
        pass

    @abstractmethod
    def proclet(self, class_type: str) -> tuple[list[Any], list[Any], list[Any]]:
        pass

    @abstractmethod
    def get_process_executions(
        self, class_type: str, entity_ids: list[str]
    ) -> tuple[list[dict], datetime, datetime]:
        pass

    @abstractmethod
    def entity_sample(self, class_type: str, sample_size: int) -> list[str]:
        pass

    @abstractmethod
    def count_classes(self, class_type: str) -> int:
        pass

    @abstractmethod
    def count_dfc(self, class_type: str) -> int:
        pass

    @abstractmethod
    def count_sync(self, class_type: str) -> int:
        pass

    @abstractmethod
    def proclet_types(self):
        pass

    @abstractmethod
    def count_start_activities(self, class_type: str) -> int:
        pass

    @abstractmethod
    def count_end_activities(self, class_type: str) -> int:
        pass

    @abstractmethod
    def get_entities_for_dfc_count(self, dfc_id: str) -> int:
        pass

    @abstractmethod
    def get_entities_for_dfc(self, dfc_id: str, limit: int, skip: int) -> list[dict]:
        pass

    @abstractmethod
    def get_entities_for_event_class_count(self, class_id: str) -> int:
        pass

    @abstractmethod
    def get_entities_for_event_class(
        self, class_id: str, limit: int, skip: int
    ) -> list[dict]:
        pass

    @abstractmethod
    def get_dfc(self, dfc_id: str) -> dict | None:
        pass

    @abstractmethod
    def get_event_class(self, event_class_id: str) -> dict | None:
        pass
