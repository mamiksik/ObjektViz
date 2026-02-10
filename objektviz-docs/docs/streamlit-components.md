# Streamlit Components

ObjektViz provides interactive control components that let you customize your process model visualizations through an intuitive dashboard interface.

## Overview

Control components follow a simple data flow pattern:

**Default Values** → **UI Controls** → **Preferences** → **Backend Config** → **Visualization**

1. **Default Values**: Set initial states for your dashboard controls
2. **UI Controls**: Interactive Streamlit components (sliders, dropdowns, toggles)
3. **Preferences**: Structured data classes containing user selections
4. **Backend Config**: Configuration object that drives graph generation
5. **Visualization**: The final rendered process model

!!! tip "Quick Start"
    Most users will start by modifying default values in the example dashboards. For advanced customization, you can create custom control components.

---

## General Preferences

Configure high-level visualization settings that affect the entire process model.

### Component Function
```python
general_preferences(proclet_types: list[str]) -> tuple[str, bool, bool, bool, Callable]
```

### Controls

| Control | Type | Description |
|---------|------|-------------|
| **Proclet Class Type** | `selectbox` | Choose which process model type to visualize |
| **Show Start/End Nodes** | `checkbox` | Include process start and end nodes in visualization |
| **Start/End Per Cluster** | `checkbox` | Create separate start/end nodes for each cluster vs. shared nodes |
| **Enable Path Effects** | `checkbox` | Highlight paths when hovering over nodes and edges |
| **Shader Type** | `selectbox` | Algorithm for mapping attribute values to visual properties |

### Shader Types

Shaders control how attribute values are mapped to colors and edge thickness:

- **Normalize**: Uses min/max values as bounds (good for normal distributions)
- **Percentile**: Uses specified percentile range as bounds (handles outliers well)  
- **RobustScaler**: Uses robust statistical measures (best for skewed data)

!!! example "When to Use Each Shader"
    - Use **Normalize** for clean, normally distributed data
    - Use **Percentile** when you have outliers that skew the visualization
    - Use **RobustScaler** for highly skewed distributions or when you want consistent scaling

---

## Layout Preferences

Control the spatial arrangement and structure of your process model.

### Component Function
```python
layout_preferences_input(
    defaults: DefaultLayoutPreferences,
    dfc_attributes: list[str]
) -> LayoutPreferences
```

### Controls

#### Ranking & Positioning
| Control | Type | Default | Description |
|---------|------|---------|-------------|
| **Force Same Rank per Activity** | `checkbox` | `False` | Align nodes with the same activity on the same level |
| **Force Start/End Same Rank** | `checkbox` | `False` | Align all start nodes (and separately, all end nodes) |
| **Sort Classes by Frequency** | `checkbox` | `False` | Order node declarations by frequency (affects layout) |
| **Sort Connections by Frequency** | `checkbox` | `False` | Order edge declarations by frequency (affects layout) |

#### Spacing & Direction
| Control | Type | Default | Description |
|---------|------|---------|-------------|
| **Node Separation** | `slider` | `1.0` | Horizontal spacing between nodes on same level |
| **Rank Separation** | `slider` | `1.0` | Vertical spacing between levels |
| **Rank Direction** | `selectbox` | `"TB"` | Layout direction: TB, BT, LR, RL |

#### Advanced Options
| Control | Type | Default | Description |
|---------|------|---------|-------------|
| **Weight Attribute** | `selectbox` | `None` | Use attribute values as edge weights (higher = shorter/straighter) |
| **Clustering Keys** | `multiselect` | `[]` | Attributes for creating nested clusters |

!!! tip "Clustering Example"
    Setting clustering keys to `['EntityType', 'Location']` creates clusters by entity type, with nested sub-clusters by location.

---

## DFC (Connection) Preferences

Customize how edges between event classes are displayed.

### Component Function
```python
dfc_appearance_input(
    edge_attributes: list[str],
    defaults: DefaultConnectionPreferences  
) -> DFCPreferences
```

### Controls

| Control | Type | Default | Description |
|---------|------|---------|-------------|
| **DFC Width Range** | `range_slider` | `(2, 10)` | Min/max edge thickness based on shading attribute |
| **DFC Label** | `selectbox` | `"frequency"` | Attribute to display on edge labels |
| **DFC Shading Attribute** | `selectbox` | `"frequency"` | Numeric attribute for edge thickness/color |
| **Use XLabels** | `toggle` | `False` | Place labels outside layout calculation for cleaner routing |

!!! info "XLabels vs Regular Labels"
    - **Regular labels** are considered during layout calculation, ensuring visibility but potentially creating complex edge routes
    - **XLabels** are ignored during layout, creating cleaner paths but labels might overlap or be hidden

### Example Configuration
```python
# Thick edges for high-frequency transitions
DFCPreferences(
    pen_width_range=(1, 15),
    caption="average_duration", 
    shading_attr="frequency",
    use_x_labels=True
)
```

---

## Event Class (Node) Preferences  

Control the appearance and content of individual nodes in your process model.

### Component Function
```python
event_class_appearance_input(
    node_attributes: list[str],
    defaults: DefaultEventClassPreferences
) -> EventClassPreferences
```

### Controls

#### Content
| Control | Type | Default | Description |
|---------|------|---------|-------------|
| **Node Title** | `selectbox` | `"EventType"` | Main text displayed in node |
| **Left Caption** | `selectbox` | `"EntityType"` | Small text on left side |
| **Right Caption** | `selectbox` | `"frequency"` | Small text on right side |

#### Styling  
| Control | Type | Default | Description |
|---------|------|---------|-------------|
| **Shading Attribute** | `selectbox` | `"frequency"` | Numeric attribute for node color/opacity |
| **Icon Mapping** | `dict` | `{}` | Map attribute values to emoji/icon prefixes |

### Icon Mapping

Add visual context to your nodes with custom icons:

```python
icon_map = {
    "EntityType": {
        "Package": "📦",
        "Contract": "📝", 
        "Customer": "👤"
    },
    "Priority": {
        "High": "🔴",
        "Medium": "🟡",
        "Low": "🟢"
    }
}
```

!!! example "Node Appearance Result"
    With the above icon mapping, a package-related node with high priority might display as:
    ```
    📦🔴 Package Processing
    Customer    │    1,234
    ```

---

## Animation Preferences

Configure token replay and animation effects for process visualization.

### Component Function
```python
animation_preferences_input() -> TokenReplayPreferences
```

### Controls

#### Animation Toggles
| Control | Type | Default | Description |
|---------|------|---------|-------------|
| **Animate Process Flow** | `toggle` | `False` | Show dashed animation on active paths |
| **Animate Tokens** | `toggle` | `True` | Enable token movement along paths |

#### Timing Controls
| Control | Type | Default | Description |
|---------|------|---------|-------------|
| **Token Replay Speed** | `slider` | `5.0` | Animation speed (higher = faster) |
| **Animation Alignment** | `segmented_control` | `"At-once"` | Token start timing |
| **Fixed Duration** | `checkbox` | `False` | Same duration for all replays vs. scaled |

### Animation Alignment Options

- **At-once**: All tokens start moving simultaneously
- **Real-time**: Tokens start with delays proportional to their actual event timing

!!! tip "Performance Considerations"
    Animation can be resource-intensive for large process models. Consider disabling animations or reducing speed for better performance.

---

## Preference Groups

For convenience, ObjektViz provides a high-level wrapper that combines multiple preference panels:

### Component Function
```python
preferences_group(
    queries: AbstractEKGRepository,
    class_type: str,
    default_layout_preferences_input: DefaultLayoutPreferences,
    default_connection_visuals: DefaultConnectionPreferences,
    default_event_class_visuals: DefaultEventClassPreferences
) -> tuple[LayoutPreferences, DFCPreferences, EventClassPreferences, bool, TokenReplayPreferences]
```

This component renders all preference panels in a single function call and returns their combined outputs.

### Example Usage

```python
# Set up defaults
DEFAULT_LAYOUT = DefaultLayoutPreferences()
DEFAULT_CONNECTIONS = DefaultConnectionPreferences(shading="duration")
DEFAULT_NODES = DefaultEventClassPreferences(title="ActivityName")

# Get all preferences at once
layout_prefs, dfc_prefs, node_prefs, show_sample_only, animation_prefs = (
    ov_components.preferences_group(
        queries=queries,
        class_type=selected_class_type,
        default_layout_preferences_input=DEFAULT_LAYOUT,
        default_connection_visuals=DEFAULT_CONNECTIONS,
        default_event_class_visuals=DEFAULT_NODES
    )
)
```