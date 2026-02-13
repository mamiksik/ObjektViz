import itertools

from typing import Iterable
from collections import defaultdict

import graphviz

from objektviz.backend.BackendConfig import BackendConfig
from objektviz.backend.dot_elements import (
    AbstractDotElement,
    DotEdge,
    DotNode,
    CROSS_CLUSTER_SENTINEL,
)
from objektviz.backend.shaders import AbstractShader
from objektviz.backend.utils import to_lbl


def generate_dot_source(
    nodes: Iterable[DotNode],
    edges: Iterable[DotEdge],
    node_shaders: dict[str, AbstractShader],
    edge_shaders: dict[str, AbstractShader],
    config: BackendConfig,
):
    """Produces dot source code for given edges and nodes"""
    node_rank = {}

    # Sort graph elements for layout stability
    if config.layout_preferences.sort_event_classes_by_frequency:
        nodes = sorted(nodes, key=lambda n: n.frequency, reverse=True)
    else:
        nodes = sorted(nodes, key=lambda n: n.element_id)

    if config.layout_preferences.sort_connections_by_frequency:
        edges = sorted(edges, key=lambda n: n.frequency, reverse=True)
    else:
        edges = sorted(edges, key=lambda n: n.element_id)

    # 1st pass: Decide on node visibility and collect relevant ids and shader bounds for visible nodes and edges
    visible_node_ids = set()

    for node in nodes:
        if not node.is_visible:
            continue

        visible_node_ids.add(node.element_id)

    sync_edges_ids = set()
    connected_nodes_ids = set()
    visible_edges_ids = set()

    for edge in edges:
        if not edge.is_visible:
            continue

        if (edge.start_element_id not in visible_node_ids) or (
            edge.end_element_id not in visible_node_ids
        ):
            continue

        if (edge.start_element_id, edge.end_element_id) in sync_edges_ids or (
            edge.end_element_id,
            edge.start_element_id,
        ) in sync_edges_ids:
            continue

        if edge.is_sync_edge:
            sync_edges_ids.add((edge.end_element_id, edge.start_element_id))
        else:
            connected_nodes_ids.add(edge.start_element_id)
            connected_nodes_ids.add(edge.end_element_id)
            visible_edges_ids.add(edge.element_id)

    # Pass 2: Assign styled and visible nodes and edges into correct sub-graph
    elements_to_render = list()
    for node in nodes:
        if (
            node.element_id not in connected_nodes_ids
            or node.element_id not in visible_node_ids
        ):
            continue

        elements_to_render.append(node)
        node_shaders[node.shader_key].update_bounds(node.entity)
        # Store the raw element id for later mapping and synthetic-edge creation
        node_rank.setdefault(node.activity_name, []).append(node.element_id)

        if config.show_start_end_nodes and (node.process_start_count and node.process_start_count > 0):
            entity_stub = {
                config.dfc_preferences.shading_attr: node.process_start_count
            }
            edge_shaders[node.shader_key].update_bounds(entity_stub)

        if config.show_start_end_nodes and (node.process_end_count and node.process_end_count > 0):
            entity_stub = {
                config.dfc_preferences.shading_attr: node.process_end_count
            }
            edge_shaders[node.shader_key].update_bounds(entity_stub)

    edge_node_map = {}
    node_edge_map = {}
    node_node_map = {}
    for edge in edges:
        if (
            edge.is_sync_edge
            and (edge.end_element_id, edge.start_element_id) not in sync_edges_ids
        ):
            continue

        if edge.is_sync_edge and not (
            edge.start_element_id in connected_nodes_ids
            and edge.end_element_id in connected_nodes_ids
        ):
            continue

        if not edge.is_sync_edge and edge.element_id not in visible_edges_ids:
            continue

        edge_node_map.setdefault(edge.element_id, []).extend(
            [edge.start_element_id, edge.end_element_id]
        )
        node_edge_map.setdefault(edge.start_element_id, []).append(edge.element_id)
        node_edge_map.setdefault(edge.end_element_id, []).append(edge.element_id)
        node_node_map.setdefault(edge.start_element_id, []).append(edge.end_element_id)
        node_node_map.setdefault(edge.end_element_id, []).append(edge.start_element_id)

        if not edge.is_sync_edge:
            elements_to_render.append(edge)
            edge_shaders[edge.shader_key].update_bounds(edge.entity)

        if edge.is_sync_edge and not config.dfc_preferences.hide_sync_edges:
            elements_to_render.append(edge)

    # Pass 3: Built the graph
    builder = DotGraphDescriptorBuilder(
        config=config,
        edge_shaders=edge_shaders,
        visible_node_ids=visible_node_ids.union(connected_nodes_ids),
        edge2node=edge_node_map,
        node2edge=node_edge_map,
        node2node=node_node_map,
        node_rank=node_rank,
    )

    graph = builder.build_graph(elements_to_render)
    return graph.source, builder.edge2node, builder.node2edge, builder.node2node


class DotGraphDescriptorBuilder:
    def __init__(
        self,
        *,
        config: BackendConfig,
        edge_shaders: dict[str, AbstractShader],
        visible_node_ids: set[str],
        edge2node: dict[str, list[str]],
        node2edge: dict[str, list[str]],
        node2node: dict[str, list[str]],
        node_rank: dict[str, list[str]],
    ):
        self.config = config
        self.edge_shaders = edge_shaders
        self.visible_node_ids = visible_node_ids
        self.edge2node = edge2node
        self.node2edge = node2edge
        self.node2node = node2node
        self.counter = itertools.count(0, 1)
        self.node_rank = node_rank

        self.start_nodes_ids = []
        self.end_nodes_ids = []

    def build_graph(self, items: list[AbstractDotElement]):
        graph = graphviz.Digraph("dot-graph", comment="dot-graph")
        graph.body.append(f"""
            newrank=true;
            nodesep={self.config.layout_preferences.node_separation};
            ranksep={self.config.layout_preferences.rank_separation};
            rankdir={self.config.layout_preferences.rank_direction};
            edge[tailclip=false];
            graph [outputorder=edgesfirst; compound=true;];
        """)

        self.build_subgraph(graph, items, 0)
        self.enforce_same_rank(graph)
        return graph

    def build_subgraph(
        self,
        graph: graphviz.Digraph,
        items: list[AbstractDotElement],
        level,
    ):
        """
        Process current subgraph, either by adding nodes and edges or splitting
        the input into further sub-graphs and calling itself recursively
        """
        if not self.config.show_start_end_nodes_per_cluster and level == 0:
            self.inject_local_start_end_nodes(graph, items)

        # If we end of the nesting add the items to the graph
        if level >= len(self.config.layout_preferences.clustering_keys):
            if (
                self.config.show_start_end_nodes_per_cluster
                and self.config.show_start_end_nodes
            ):
                self.inject_local_start_end_nodes(graph, items)

            for item in items:
                self.add_elem_to_graph(graph, item)

            return

        # Build groping for the current level
        key = self.config.layout_preferences.clustering_keys[level]
        grouped = defaultdict(list)
        cross_graph = list()
        for dot_elem in items:
            attr_value = dot_elem.get_nesting_attr(key)
            if attr_value is CROSS_CLUSTER_SENTINEL:
                cross_graph.append(dot_elem)
            else:
                grouped[attr_value].append(dot_elem)

        # Build graphs for each attribute instance
        for group_key, group_items in grouped.items():
            cluster_name = f"cluster_{key}_{group_key}"
            subgraph = graphviz.Digraph(name=cluster_name)
            subgraph.body.append("""
                style=none;
                color=none;
            """)

            self.build_subgraph(subgraph, group_items, level + 1)
            graph.subgraph(subgraph)

        # Afterward attach all cross attribute level elements
        for item in cross_graph:
            self.add_elem_to_graph(graph, item)

    def inject_local_start_end_nodes(
        self, graph: graphviz.Digraph, items: list[AbstractDotElement]
    ):
        """
        Create start, end nodes and relevant edges for selected subgraph

        Note: I's important the node ids are unique but also stable for the same input *to_node* input,
              otherwise new layout will be produced on frontend
        """

        local_start_id = f"LocalStart_{next(self.counter)}"
        local_end_id = f"LocalEnd_{next(self.counter)}"

        local_start_nodes = [
            n
            for n in items
            if isinstance(n, DotNode)
            and n.process_start_count
            and n.process_start_count > 0
            and n.element_id in self.visible_node_ids
            # and n.element_id in self.connected_node_ids
        ]

        local_end_nodes = [
            n
            for n in items
            if isinstance(n, DotNode)
            and n.process_end_count
            and n.process_end_count > 0
            and n.element_id in self.visible_node_ids
            # and n.element_id in connected_node_ids
        ]

        if local_start_nodes:
            graph.node(
                id=local_start_id,
                name=local_start_id,
                label="▼",
                shape="circle",
                style="filled",
                color="#00800070",
                fontcolor="#008000",
                fillcolor="#90c08c",
            )
            self.start_nodes_ids.append(local_start_id)

            for node in local_start_nodes:
                edge_id = f"{local_start_id}-{to_lbl(node.element_id)}"

                self.edge2node.setdefault(edge_id, []).extend(
                    [local_start_id, node.element_id]
                )
                self.node2edge.setdefault(local_start_id, []).append(edge_id)
                self.node2edge.setdefault(node.element_id, []).append(edge_id)
                self.node2node.setdefault(local_start_id, []).append(node.element_id)
                self.node2node.setdefault(node.element_id, []).append(local_start_id)


                entity_stub = {
                    self.config.event_class_preferences.shading_attr: node.process_start_count
                }
                pen_width = self.edge_shaders[node.shader_key].pen_width(entity_stub)

                shading_color = "#00800050"
                if self.config.dfc_preferences.use_shading_color_on_start_end_edge:
                    shading_color = self.edge_shaders[node.shader_key].shading_color(entity_stub)

                if self.config.dfc_preferences.lower_start_end_edge_opacity:
                    shading_color = f"{shading_color}40"

                graph.edge(
                    local_start_id,
                    to_lbl(node.element_id),
                    id=edge_id,
                    label=f"{node.process_start_count:,}",
                    penwidth=str(pen_width),
                    fontname="Helvetica",
                    style="dashed",
                    # color="#00800050",
                    color=shading_color,
                    arrowsize="2",
                )

        if local_end_nodes:
            graph.node(
                id=local_end_id,
                name=local_end_id,
                label="✖",
                shape="circle",
                color="#B31B1B70",
                style="filled",
                fontcolor="#B31B1B",
                fillcolor="#e2968d",
            )
            self.end_nodes_ids.append(local_end_id)

            for node in local_end_nodes:
                edge_id = f"{to_lbl(node.element_id)}-{local_end_id}"

                self.edge2node.setdefault(edge_id, []).extend(
                    [edge_id, node.element_id]
                )
                self.node2edge.setdefault(local_end_id, []).append(edge_id)
                self.node2edge.setdefault(node.element_id, []).append(edge_id)

                self.node2node.setdefault(local_end_id, []).append(node.element_id)
                self.node2node.setdefault(node.element_id, []).append(local_end_id)


                entity_stub = {
                    self.config.event_class_preferences.shading_attr: node.process_end_count
                }
                pen_width = self.edge_shaders[node.shader_key].pen_width(entity_stub)

                shading_color = "#B31B1B"
                if self.config.dfc_preferences.use_shading_color_on_start_end_edge:
                    shading_color = self.edge_shaders[node.shader_key].shading_color(entity_stub)

                if self.config.dfc_preferences.lower_start_end_edge_opacity:
                    shading_color = f"{shading_color}40"

                graph.edge(
                    to_lbl(node.element_id),
                    local_end_id,
                    id=edge_id,
                    label=f"{node.process_end_count:,}",
                    penwidth=str(pen_width),
                    fontname="Helvetica",
                    style="dashed",
                    color=shading_color,
                    arrowsize="2",
                )

    def add_elem_to_graph(self, graph: graphviz.Digraph, item: AbstractDotElement):
        if item.dot_element_type == "node":
            graph.node(**item.dot_descriptor)
        elif item.dot_element_type == "edge":
            graph.edge(**item.dot_descriptor)

    def enforce_same_rank(self, graph):
        if (
            self.config.show_start_end_nodes
            and self.config.layout_preferences.force_process_start_end_same_rank
        ):
            elements = ";".join([f'"{e}"' for e in self.start_nodes_ids])
            graph.body.append(f"{{rank=same; {elements};}};")

            elements = ";".join([f'"{e}"' for e in self.end_nodes_ids])
            graph.body.append(f"{{rank=same; {elements};}};")

        if self.config.layout_preferences.force_same_rank_for_event_class:
            # Build a set of all node ids across all ranks
            all_nodes = set()
            for elems in self.node_rank.values():
                all_nodes.update(elems)

            # For each rank: emit a rank=same statement and create synthetic invisible
            # edges from one representative node (first element) to all nodes outside
            # that rank. These invisible edges help the layout algorithm to separate
            # ranks. We also update edge2node/node2edge/node2node maps so downstream
            # code can map synthetic edges back to original nodes.
            created_edges = set()
            for key, elements in self.node_rank.items():
                if not elements:
                    continue

                # Emit rank constraint using the node labels used in the graph
                quoted = ";".join([f'"{to_lbl(e)}"' for e in elements])
                graph.body.append(f"{{rank=same; {quoted};}};")

                # Representative node (use the first element of the rank)
                rep = elements[0]

                # Create invisible edges from rep to all nodes outside this rank
                outside = all_nodes - set(elements)
                for other in outside:
                    # Avoid self-loops and duplicate synthetic edges
                    if rep == other:
                        continue

                    # Create a stable edge id for the synthetic edge
                    edge_id = f"rank_invis_{to_lbl(rep)}_{to_lbl(other)}"
                    if edge_id in created_edges or edge_id in self.edge2node:
                        continue

                    # Add mapping entries using raw element ids
                    self.edge2node.setdefault(edge_id, []).extend([rep, other])
                    self.node2edge.setdefault(rep, []).append(edge_id)
                    self.node2edge.setdefault(other, []).append(edge_id)
                    self.node2node.setdefault(rep, []).append(other)
                    self.node2node.setdefault(other, []).append(rep)

                    # Add the invisible edge to the dot graph (use to_lbl for node ids)
                    graph.edge(
                        to_lbl(rep),
                        to_lbl(other),
                        id=edge_id,
                        style="invis",
                        color="transparent",
                        arrowhead="none",
                        constraint="true",
                    )

                    created_edges.add(edge_id)
