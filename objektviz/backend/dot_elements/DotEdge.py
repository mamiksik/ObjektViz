from typing import Literal

import neo4j

from objektviz.backend.dot_elements.AbstractDotElement import (
    AbstractDotElement,
    CROSS_CLUSTER_SENTINEL,
)
from objektviz.backend.utils import to_lbl


class DotEdge(AbstractDotElement):
    """Takes care of producing dot descriptor code for edge (see parent class doc)"""

    entity: neo4j.graph.Relationship
    style = "solid"

    @property
    def dot_descriptor(self):
        label_attr = "label"
        if self.config.connection_preferences.use_x_labels:
            label_attr = "xlabel"

        return {
            "id": self.element_id,
            "tail_id": self.start_element_id,
            "head_id": self.end_element_id,
            "head_name": to_lbl(self.end_element_id),
            "tail_name": to_lbl(self.start_element_id),
            label_attr: self.descriptive_label,
            "forcelabels": str(True),
            "fontname": self.fontname,
            "penwidth": str(self.penwidth),
            "arrowsize": "2",
            "color": self.color,
            "style": self.style,
            "dir": self.dir,
            # 'constraint': str(not self.is_sync_edge),
            # 'fontsize':'18',
            # 'labeldistance':'4.5',
            # 'labelangle':'45',
            # 'headlabel':"True",
        }

    @property
    def dot_element_type(self) -> Literal["edge"]:
        return "edge"

    def get_nesting_attr(self, name, default=None):
        # start_attr = self.entity.start_node.get(name, default)
        # end_attr = self.entity.end_node.get(name, default)
        # if start_attr == end_attr:
        #     return start_attr
        # else:
        return CROSS_CLUSTER_SENTINEL

    @property
    def start_element_id(self):
        return self.entity.start_node.element_id

    @property
    def end_element_id(self):
        return self.entity.end_node.element_id

    @property
    def descriptive_label(self) -> str:
        if self.is_sync_edge:
            return ""

        value = self.entity.get(self.config.connection_preferences.caption, -1)
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
            return 5

        return self.shaders[self.shader_key].pen_width(self.entity)

    @property
    def color(self):
        if self.is_sync_edge:
            return "#4A4A4A50"

        return self.shaders[self.shader_key].shading_color(self.entity)

    @property
    def is_visible(self):
        if self.is_sync_edge:
            return True

        return self.config.connection_root_filter.is_passing(self.entity)

    @property
    def is_sync_edge(self):
        return self.entity.type == "SYNC"

    @property
    def shader_key(self):
        if self.is_sync_edge:
            return "CROSS_ENTITY"

        return super().shader_key

    @property
    def waiting_time(self):
        return self.entity.get("waitingTime", "0")
