
# ObjektViz — Overview

A compact explanation of the project purpose, architecture and how to get started.

## What is ObjektViz

ObjektViz is a small framework for building interactive Event Knowledge Graph dashboards. It provides:
1. A Streamlit-based UI layer for dashboard components.
2. A backend that builds DOT graph source from database results.
3. A front-end visualizer (D3.js) that renders DOT graphs.


## High-level architecture

UI \--> Backend \--> Dot Source \--> Frontend

- UI: Streamlit components that produce user preferences and interact with the repository layer.
- Backend: Builds DOT nodes/edges using configuration, shaders and filters.
- Dot Source: DOT representation that describes the graph to render.
- Frontend: D3.js renderer that consumes DOT source and provides interaction.

## Key concepts

1. `AbstractEKGRepository`
    - Interface used by UI (streamlit) components to query databases. Adaptors implement this interface so components can remain database-agnostic.

2. Control components
    - Streamlit controls that output preference dataclasses. Pass these to the backend to influence graph generation.

3. Visualization components
    - Components to render the DOT graph and auxiliary views (histograms, detail panes).

4. `BackendConfig`
    - Central configuration for backend behavior: shaders, filters, layout, etc.

5. DOT elements (`DotNode`, `DotEdge`)
    - Each instance wraps a query result row and knows how to render itself as DOT. Elements that fail filters are omitted.

6. `generate_dot_source`
    - Main orchestration function. Takes `DotNode`/`DotEdge` instances and `BackendConfig`, returns the DOT source (and additional metadata).

## Project layout (relevant folders)

1. `backend` — core graph building, config and utilities
2. `backend/adaptors` — database adaptors (examples: Neo4j, KuzuDB)
3. `backend/filters` — filter primitives (And, Or, Range, Match, Not)
4. `backend/shaders` — value-to-color/size scalers (Normalized, Percentile, RobustScaler)
5. `backend/dot_elements` — DOT node/edge classes and helpers

Adaptors provide factory methods to convert query results into `DotNode` / `DotEdge` instances and implement `AbstractEKGRepository`.

## Design notes

1. Filters are composable. Combine `And`, `Or`, `Not` and atomic filters (`Range`, `Match`) to create expressive rules.
2. Shaders map attribute values to visual properties and help handle skewed distributions or outliers.
3. The system is database-agnostic: add an adaptor for a new DB and implement the required factory methods and repository interface.

## When to read which files

1. Start with `backend/BackendConfig.py` to understand configurable options.
2. Inspect `backend/dot_elements/DotNode.py` and `backend/dot_elements/DotEdge.py` to see how DOT output is produced.
3. Look into `backend/adaptors` for examples on converting query results into DOT elements.
4. Read `backend/filters` and `backend/shaders` to customize visualization logic.

## Notes

1. ObjektViz is optimized for Streamlit dashboards but can be reused outside Streamlit with manual UI wiring.
2. The focus is on building reusable components rather than a single monolithic app.