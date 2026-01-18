# 📦 ObjektViz

<p align="center">
    <img src="assets/objektviz.png" alt="ObjektViz Screenshot" width="550px" align='center'/>
</p>

> ObjektViz is visualizer for object-centric process models that enables users to explore and analyze even _very complex_ processes involving multiple interacting objects.

## Features
- 🔍 **Interactive Visualization**: Explore object-centric process models with intuitive visualizations.
- 🤝 **Multi-Object Support**: Analyze processes involving multiple interacting objects seamlessly.
- ⚙️ **Customizable**: Every dataset, every process is different. ObjektViz allows you to customize visualizations to fit your data.
- 🧩 **Manage Complexity**: Designed to handle very complex processes without overwhelming the user.
- ▶️ **Token Replay**: Replay the flow of tokens through the process to understand dynamics and interactions, even for **multi-object** scenarios.
- 🔄 **Morphing Visualizations**: Smoothly transition between different views and representations of the process model to understand various aspects of the data.

## Quick Start
ObjektViz has a lot of customization, and is build with the idea that you as a user will compose your own dashboard for the analysis you have on hand. However, to get you started quickly, we provide some example dashboards that you can run and explore.

In the examples we use KuzuDB, which works fine for small examples and the setup is easy. For real world datasets, you might use Neo4J, but that requires more setup.
We have exported processed some OCEL dataset into EKG and generated aggregated views (i.e. process models) for you to explore in the examples.

1. Clone the repository:
   ```bash
   git clone git@github.com:mamiksik/ObjektViz.git
2. Navigate to the project directory:
   ```bash
   cd ObjektViz
3. Install the required dependencies:
   ```bash
   uv sync

5. Run the example dashboard:
    ```bash
   uv run python -m streamlit run examples/generic_ocel_viewer.py
   ```
> IMPORTANT: Do **not** use streamlit run from the command line directly, as this will lead to issues with imports.

<p align="center">
    <img src="assets/generic_ocel_visualizer.png" alt="OCEL" width="750px" align='center'/>
</p>
