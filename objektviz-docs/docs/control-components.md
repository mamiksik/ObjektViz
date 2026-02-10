# Control Components
ObjektViz provides a lot of control components that allow you to modify the appearance of your process models from the dashboard UI.

In general, the composition of control components is as follows:
[1. DefaultPreferences] --> [2. Control Component] --> [3. Preference Dataclass] --> [4A. BackendConfig] --> [4B. Graph Generation]

1. DefaultPreferences are used to populate the control components with default values. You can modify these default values to change the initial state of the dashboard when you load it.
2. You pass these to appropriate control components, which render the controls in the UI.
3. The control components output preference dataclasses.
4.The preference dataclasses are then used to build the `BackendConfig`, which is passed to the graph generation function and influences how the graph is generated (e.g., which filters and shaders are applied, which layout algorithm is used, etc.)

## General Preferences
Component: `general_preferences`
Input: Available process models (class types)
Output: Varied (see below)

- `Proclet class type`
   select which process model to visualize (class type)
- `is_process_start_end_visualized`
  whether to include start and end nodes in the visualization, this can be useful when the start and end events are not relevant for the analysis or when they create too much clutter in the graph.

- `start_end_nodes_per_cluster`
    whether to create separate start and end nodes for each cluster of event classes (defined by the `clustering_keys` in layout preferences) or to use a single shared start and end node. This can help to reduce clutter and improve readability when there are many event classes.

- `enable_path_effects_on_hover`
    whether to enable path effects (e.g., highlighting) when hovering over nodes and edges.


- `shader`
  * Shards are used to map values of specified attributes to node/edge color and edge thickness. You speficy the attirbue for :Class and :DF_C individual in their respectively controls panels
    * Normalize shader simply take the minimum and maximum value for the specified attribute as it's bounds
    * Percentile shader takes the specify percentile range as it's bounds (usefully when dealing with outliers in the data)
    * RobustScaler - is just robust:) 

## Preferences Group
Is just a high level wrapper around Layout, DFC, Event Class and Animation preferences panels. See the individual sections below for details.

## Layout Preferences
Component: `layout_preferences_input`
Input: `DefaultLayoutPreferences` and `list of :DFC attributes`
Output: `LayoutPreferences`

The preferences are passed to DOT engine and influence the layout of the graph. The settings include:
- `force_same_rank_for_event_class` (bool)  
  Put all classes with the same activity string on the same rank/level.

- `force_process_start_end_same_rank` (bool)  
  Force process start and end nodes to share the same rank (applies separately for start and end).

- `sort_event_classes_by_frequency` (bool)  
  Sort event class declarations by frequency. Affects declaration order in the DOT source and can change layout heuristics.

- `sort_connections_by_frequency` (bool)  
  Sort edge declarations by frequency. Affects declaration order in the DOT source and can change layout heuristics.

- `weight_attribute` (str \| None)  
  If set to an attribute name, its values are used as edge weights during layout. Higher weight causes edges to be treated as "shorter" and "straighter".

- `clustering_keys` (list)  
  Keys used to create subgraph clusters (order matters).  
  Example: `['EntityType', 'Location']` creates clusters per entity type with nested clusters per location.

- `node_separation` (float)  
  Minimal horizontal spacing between nodes on the same rank/level.

- `rank_separation` (float)  
  Minimal vertical spacing between ranks/levels.

- `rank_direction` (str)  
  Graph layout direction: `TB` = top-to-bottom, `BT` = bottom-to-top, `LR` = left-to-right, `RL` = right-to-left.

## DFC Preferences
Component: `dfc_preferences_input`
Input: `DefaultConnectionPreferences` and `list of :DFC attributes`
Output: `DFCPreferences`

DFC preferences influence how :DF_C edges are rendered. The settings include:
- `pen_width_range` (tuple of two floats)
   Defines the minimal and maximal line thickness used during rendering based on the `shading_attr`.

- `caption` (str)
   Attribute used to display a value on top of the edge.

- `shading_attr` (str)
  Numeric attribute used for edge shading (e.g., frequency or average transition duration).

- `use_x_labels` (bool)
  If true, xlabels are used for captions and are not taken into account for layout. This can produce more compact and less convoluted edge routes, but labels might not be visible.

## Event Class Preferences
Component: `event_class_appearance_input`
Input: `DefaultEventClassPreferences` and `list of :Class attributes`
Output: `EventClassPreferences`

Event class preferences influence how :Class nodes are rendered. The settings include:
- `shading_attr` (str)  
  Numeric attribute used to compute the shading range for node color/opacity.

- `title` (str)  
  Attribute displayed as the node title.

- `caption_left` (str)  
  Attribute shown on the left side of the node (small caption).

- `caption_right` (str)  
  Attribute shown on the right side of the node (small caption).

- `icon_map` (dict[str, dict[str, str]])  
  Mapping used to prefix node titles/captions with icons when an attribute value matches.  
  Example: `{"EntityType": {"Package": "📦", "Contract": "📝"}}` — when `EntityType` equals `Package`, the `📦` icon is prefixed.


## Animation Preferences
Component: `animation_preferences_input`
Input: N/A
Output: `TokenReplayPreferences`

Animation preferences influence token replay and animation of active elements. The settings include:

- `animate_active_elements_flag` (bool)
  If true, `:DF_C` edges that participate in any token flows will be highlighted.

- `animate_tokens_flag` (bool)
  If true, token replay is enabled and tokens will be animated on the graph.

- `token_animation_speed` (float)
  Controls the speed of token movement during replay (larger values = faster).

- `token_animation_alignment` (`"At-once"` \| `"Real-time"`)
  - `At-once`: all tokens start simultaneously.
  - `Real-time`: tokens are added with time offsets proportional to their event timing relative to the sample.

- `fixed_animation_duration` (bool)
  If true, all replays take the same amount of time regardless of case duration; if false, replay duration is scaled to the case execution length.
  Only applicable when `token_animation_alignment` is set to `At-once`.