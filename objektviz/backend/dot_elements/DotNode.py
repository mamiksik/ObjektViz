from typing import Literal

import neo4j

from objektviz.backend.dot_elements.AbstractDotElement import AbstractDotElement
from objektviz.backend.utils import to_lbl


class DotNode(AbstractDotElement):
    """ Takes care of producing dot descriptor code for node (see parent class doc) """
    entity: neo4j.graph.Node
    shape = 'rect'
    style = 'rounded,filled'

    @property
    def dot_descriptor(self):
        return {
            'fontname': self.fontname,
            'id': self.element_id,
            'margin': '0.05',
            'name': to_lbl(self.element_id),
            'label': self.descriptive_label,
            'shape': self.shape,
            'style': self.style,
            'color': self.color,
            'fillcolor': self.fillcolor,
        }

    @property
    def dot_element_type(self) -> Literal["node"]:
        return "node"

    @property
    def descriptive_label(self) -> str:
        color = self.shaders[self.shader_key].shading_color(self.entity)
        full_color = color
        # full_color = self.shaders[self.entity_type].get_color(0.5)

        def get_caption(attr, alignment):
            caption = self.entity.get(attr, -1)
            icon = self.config.event_class_preferences.icon_map.get(attr, {}).get(caption, "")
            if isinstance(caption, int) or isinstance(caption, float):
                return f'<td align="{alignment}" ><font point-size="14" color="#31333f">{icon}{caption:,}</font></td>'
            else:
                return f'<td align="{alignment}" ><font point-size="14" color="#31333f">{icon}{caption}</font></td>'

        caption_left = get_caption(
            self.config.event_class_preferences.caption_left,
            "left"
        )
        caption_right = get_caption(
            self.config.event_class_preferences.caption_right,
            "right"
        )

        title = self.entity.get(self.config.event_class_preferences.title, '')
        icon = self.config.event_class_preferences.icon_map.get(self.config.event_class_preferences.title, {}).get(title, "")
        title = f"{icon}{title}"

        return f"""<
            <table border="0"  cellspacing="2" style='rounded'>
                <tr>
                    <td width="20" height="45" fixedsize="true" rowspan='3' bgcolor='{color}' style='rounded'><font point-size="1" color='{color}'>❖</font></td>
                </tr>
                <tr><td align="left" colspan='2'  valign='top' CELLPADDING='2'><font point-size="16" color='#31333f'>{title}</font></td></tr>
                <tr>{caption_left}{caption_right}</tr>
            </table>
        >"""


    @property
    def fillcolor(self):
        return '#f9fafb'

    @property
    def color(self):
        return '#d1d5db'

    @property
    def activity_name(self) -> str:
        # return self.entity.get('Name', '')
        return self.entity['EventType']

    @property
    def is_visible(self):
        return self.config.event_class_root_filter.is_passing(self.entity)

    @property
    def process_start_count(self) -> int | None:
        return self.entity.get('StartCount', None)

    @property
    def process_end_count(self) -> int | None:
        return self.entity.get('EndCount', None)

