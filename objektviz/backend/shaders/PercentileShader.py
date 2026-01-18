import dataclasses

import neo4j.graph
import numpy as np
from objektviz.backend.shaders.NormalizedShader import NormalizedShader


@dataclasses.dataclass
class PercentileShader(NormalizedShader):
    percentile_range: tuple[int, int]

    def update_bounds(self, entity: neo4j.graph.Entity):
        # In case the attribute is not present, default to self.lower_bound to make the element visible
        value = entity.get(self.leading_attribute, self.lower_bound)

        if not (isinstance(value, float) or isinstance(value, int)):
            raise ValueError(
                f"Attribute {self.leading_attribute} must be float or int, not {type(value)}"
            )

        self.values.append(value)
        self.lower_bound = np.percentile(self.values, self.percentile_range[0])
        self.upper_bound = np.percentile(self.values, self.percentile_range[1])
