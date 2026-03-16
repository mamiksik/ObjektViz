# 📦 ObjektViz

<p align="center">
    <img src="assets/objektviz.png" alt="ObjektViz Screenshot" width="550px" align='center'/>
</p>

> ObjektViz is a visualizer for object-centric process models that enables users to explore and analyze even _very complex_ processes involving multiple interacting objects.

## Features
- 🔍 **Interactive Visualization**: Explore object-centric process models with intuitive visualizations.
- 🤝 **Multi-Object Support**: Analyze processes involving multiple interacting objects seamlessly.
- ⚙️ **Customizable**: Every dataset, every process is different. ObjektViz allows you to customize visualizations to fit your data.
- 🧩 **Manage Complexity**: Designed to handle very complex processes without overwhelming the user.
- ▶️ **Token Replay**: Replay the flow of tokens through the process to understand dynamics and interactions, even for **multi-object** scenarios.
- 🔄 **Morphing Visualizations**: Smoothly transition between different views and representations of the process model to understand various aspects of the data.

## Quick Start
ObjektViz has a lot of customization, and is built with the idea that you as a user will compose your own dashboard for the analysis you have at hand. However, to get you started quickly, we provide some example dashboards that you can run and explore.

In the examples we use KuzuDB, which works fine for small examples and the setup is easy. For real-world datasets, you might use Neo4J, but that requires more setup.
We have exported and processed some OCEL datasets into EKG and generated aggregated views (i.e. process models) for you to explore in the examples.

### Installation using pypi package
1. Create a new Python environment and install the `objektviz` package from PyPI:
   ```bash
   pip install objektviz[kuzu, neo4j]
   ```
2. Copy the example dashboard script (e.g. 'examples/generic_ocel_viewer.py') and dataset folder. 

3. Run the example dashboard:
    ```bash
   streamlit run generic_ocel_viewer.py
   ```

### Manual installation
1. Clone the repository:
   ```bash
   git clone git@github.com:mamiksik/ObjektViz.git
2. Navigate to the project directory:
   ```bash
   cd ObjektViz
3. Install the required dependencies (we use [uv](https://docs.astral.sh/uv/) to manage the Python environment and dependencies):
   ```bash
   uv sync --all-extras

4. Activate the virtual environment (bash shell):
   ```bash
   source .venv/bin/activate

5. Run the example dashboard:
    ```bash
   streamlit run examples/generic_ocel_viewer.py
   ```
> INFO: Using Chrome is strongly recommended. Mozilla Firefox and Safari should also work. (Although Safari does not support token replay.)

> INFO: Token Replay for now requires APOC library and is thus not available with KuzuDB

6. [OPTIONAL] If you are planning on editing the objektviz source code, you can install the objektviz package it in editable mode:
    ```bash
   uv add --editable --dev objektviz
   ```

<p align="center">
    <img src="assets/generic_ocel_visualizer.png" alt="Visualizer" width="750px" align='center'/>
</p>

## Feature spotlight 

**Morphing and Animation** - ObjektViz supports smooth morphing between different process model views. This allows users to transition seamlessly from one perspective to another, this helps to manage complexity and understand different aspects of the process.
<p align="center">
    <img src="assets/morphing.gif" alt="Morphing" width="550px" align='center'/>
</p>

**Shaders** - color lightness and thickness of edges play critical role in making a proces s model understandable. ObjektViz supports a variety of shaders that can be applied to nodes and edges to highlight different aspects of the process model or to deal with skewed distributions.
<p align="center">
    <img src="assets/shader-types.png" alt="Custom Shaders" width="300px" align='center'/>
</p>

**Token Replay** - understand the dynamics of your process by replaying tokens through the process model. This feature allows you to visualize how different objects interact over time within the process.
<p align="center">
    <img src="assets/token-replay.gif" alt="Custom Shaders" width="550px" align='center'/>
</p>

## Import your own OCEL dataset
To import your own OCEL dataset, you need to convert it into EKG format first and then generate aggregated views (i.e., process models) from it.
We provide scripts to help you with this process in the `examples` folder.

1. Convert OCEL to EKG and infer aggregated views:
   ```bash
   uv run python examples/ocel/kuzudb/process_ocel_to_kuzudb.py path/to/your/ocel.json path/to/save/ekg.kuzu
   ```
2. Copy one of the example dashboards (e.g. 'examples/generic_ocel_viewer.py') script and modify it to point to your newly created EKG database. The line to change is where the database is initialized:
    ```python
    db = kuzu.Database("path/to/save/ekg.kuzu")
    ```
3. Run your modified dashboard:
    ```bash
    uv run python -m streamlit run path/to/your/custom_dashboard.py
    ```

# ObjektViz Proclet Metamodel (Work In Progress - Subject to Change)
<p align="center">
    <img src="assets/metamodel-objektviz.png" alt="Proclet Metamodel" width="550px" align='center'/>
</p>

