import abc
from abc import ABC
from typing import Literal, Mapping

from objektviz.backend.dot_elements.AbstractDotElement import (
    AbstractDotElement,
)

from objektviz.backend.utils import uuid_to_lbl


class AbstractDotEdge[EntityT: Mapping](AbstractDotElement[EntityT], ABC):
    """Takes care of producing dot descriptor code for edge (see parent class doc)"""

    sync_edge_color = "#c4c4c4"
    sync_edge_width  = 3

    style = "solid"
    arrow_size = 2
    force_labels = True

    @property
    def dot_descriptor(self):
        label_attr = "label"
        if self.config.dfc_preferences.use_x_labels:
            label_attr = "xlabel"

        return {
            "id": self.element_id,
            "tail_id": self.start_element_id,
            "head_id": self.end_element_id,
            "head_name": uuid_to_lbl(self.end_element_id),
            "tail_name": uuid_to_lbl(self.start_element_id),
            label_attr: self.descriptive_label,
            "forcelabels": str(self.force_labels),
            "fontname": self.fontname,
            "penwidth": str(self.penwidth),
            "arrowsize": f"{self.arrow_size}",
            "color": self.color,
            "style": self.style,
            "dir": self.dir,
            "weight": str(self.weight),
            "class": "sync-edge" if self.is_sync_edge else "dfc-edge",
            "headclip": str(not self.is_sync_edge),
        }

    @property
    def weight(self) -> int:
        if self.config.layout_preferences.weight_attribute is None:
            return 1

        return self.get(self.config.layout_preferences.weight_attribute, 0)

    @property
    @abc.abstractmethod
    def start_element_id(self):
        pass

    @property
    @abc.abstractmethod
    def end_element_id(self):
        pass

    @property
    def dot_element_type(self) -> Literal["edge"]:
        return "edge"

    @property
    def descriptive_label(self) -> str:
        if self.is_sync_edge:
            return ""

        value = self.get(self.config.dfc_preferences.caption, -1)
        if isinstance(value, float):
            return f"   {value:.2f}"

        if isinstance(value, int):
            return f"   {value:,}"

        return f"   {value}"

    @property
    def dir(self):
        if self.is_sync_edge:
            return "none"

        return "forward"

    @property
    def penwidth(self):
        if self.is_sync_edge:
            return self.sync_edge_color

        return self.shaders[self.shader_cluster].pen_width(self.entity)

    @property
    def color(self):
        if self.is_sync_edge:
            return self.sync_edge_color

        return self.shaders[self.shader_cluster].shading_color(self.entity)

    @property
    def is_visible(self):
        if self.config.root_element_filter and not self.config.root_element_filter.is_passing(self):
            return False

        if self.is_sync_edge:
            return True

        return self.config.dfc_root_filter.is_passing(self)

    @property
    @abc.abstractmethod
    def is_sync_edge(self):
        pass
