import warnings
from datetime import datetime
from typing import Iterator, Mapping

import kuzu

from objektviz.backend.BackendConfig import BackendConfig
from objektviz.backend.adaptors.shared import AbstractEKGRepository, CypherQueries
from objektviz.backend.dot_elements import AbstractDotNode, CROSS_CLUSTER_SENTINEL, AbstractDotEdge
from objektviz.backend.shaders import AbstractShader
from objektviz.backend.utils import shader_factory

type KuzuNode = Mapping  # Placeholder for kuzu Node
type KuzuRelationship = Mapping  # Placeholder for kuzu Relationship


def kuzu_internal_id_to_str(node: dict) -> str:
    # return f"[table={node['table']}][offset={node['offset']}]"
    return f"{node['table']}:{node['offset']}"


def kuzu_internal_id_to_element_id(id: str) -> str:
    return id.split(":")[1]


class KuzuDotNode(AbstractDotNode):
    @property
    def element_id(self):
        return kuzu_internal_id_to_str(self.entity["_id"])


class KuzuDotEdge(AbstractDotEdge[KuzuRelationship]):
    @property
    def element_id(self):
        return kuzu_internal_id_to_str(self.entity["_id"])

    @property
    def is_sync_edge(self):
        return self.entity["_label"] == "SYNC"

    @property
    def start_element_id(self):
        return kuzu_internal_id_to_str(self.entity["_src"])

    @property
    def end_element_id(self):
        return kuzu_internal_id_to_str(self.entity["_dst"])

    def get_nesting_attr(self, name, default=None):
        # TODO: Fix this for KUZUDB, now all edges are considered cross cluster,
        # since kuzudb does not return the start and end as part of the same record

        # This is suboptimal since we might not cluster on EntityType, thus
        # sync edges could be in the same cluster
        if self.is_sync_edge and name == 'EntityType':
            return CROSS_CLUSTER_SENTINEL

        return self.entity.get(name, default)


def from_kuzu_to_dot_elements(
    nodes: list[KuzuNode], edges: list[KuzuRelationship], config: BackendConfig
) -> tuple[
    Iterator[KuzuDotNode],
    Iterator[KuzuDotEdge],
    dict[str, AbstractShader],
    dict[str, AbstractShader],
    BackendConfig,
]:
    """Wrapper around to_dot that consumes Neo4J query output rather than instances of DotAbstractElement"""

    if len(nodes) == 0:
        warnings.warn("0 nodes were passed to from_kuzu_to_dot_elements")

    if len(edges) == 0:
        warnings.warn("0 edges were passed to from_kuzu_to_dot_elements")

    node_shaders, edge_shaders = shader_factory(config)
    _nodes = list(map(lambda node: KuzuDotNode(node, node_shaders, config), nodes))
    _edges = list(map(lambda edge: KuzuDotEdge(edge, edge_shaders, config), edges))

    return _nodes, _edges, node_shaders, edge_shaders, config


class KuzuEKGRepository(AbstractEKGRepository):
    def __init__(self, connection: kuzu.Connection):
        self.connection = connection

    def run_query(self, query, params) -> kuzu.QueryResult:
        return self.connection.execute(query, params)

    def get_entity_type_frequency(self, class_type: str, entity_type: str) -> int:
        result = self.run_query(f"""
            MATCH (n:Entity {{Type: "{entity_type}"}})<-[:CORR]-(:Event)-[:OBSERVED]->(:Class {{Type: "{class_type}"}})
            RETURN count(DISTINCT n) as frequency
        """, {})

        return result.get_all()[0][0]

    def get_avg_class_order(self, class_type: str, entity_type: str) -> list[str]:
        warnings.warn("class type is not used in get_avg_class_order for KuzuDB yet")
        res = self.run_query(f"""
            MATCH 
                (startEvent:Event)-[:P_START]->(entity:Entity {{Type: "{entity_type}"}})<-[:P_END]-(endEvent:Event)
            MATCH path = (startEvent)-[:DF* SHORTEST (r, n | WHERE r.EntityType = "{entity_type}" AND LABEL(n) = "Event" AND (n)-[:CORR]->(entity))]->(endEvent)
            WITH nodes(path) AS pathNodes
            UNWIND range(1, size(pathNodes)) AS position
            WITH pathNodes[position] AS pathNode, position
            WITH pathNode.Type AS activity, position
    
            WITH activity,
                 avg(position) AS avgPosition,
                 count(*) AS frequency
    
            ORDER BY avgPosition ASC, frequency DESC
            SKIP 0
            RETURN collect(activity) AS sorted
        """, {})
        return res.get_all()[0][0]

    def get_all_activity_names(self, class_type: str, entity_type: str) -> list[str]:
        warnings.warn("class type is not used in get_all_activity_names for KuzuDB yet")
        res = self.run_query(f"""
            MATCH (e:Event)-[:CORR]->(n:Entity {{Type: "{entity_type}"}})
            RETURN DISTINCT e.Type AS activity
        """, {})
        return [x[0] for x in res.get_all()]

    def get_class_attributes(self, class_type: str) -> list[str]:
        qparams = { "ClassType": class_type }
        return (
            self.run_query(CypherQueries.get_class_attributes(), qparams)
            .get_all()[0][0]
        )

    def get_classes_count(self, class_type: str) -> int:
        qparams = { "ClassType": class_type }
        return (
            self.run_query(CypherQueries.get_classes_count(), qparams)
            .get_all()[0][0]
        )

    def get_dfc(self, dfc_id: str) -> dict | None:
        result = self.run_query(
            """
            MATCH (c1: Class)-[df_c:DF_C]->(c2: Class)
            WHERE OFFSET(ID(df_c)) = $DFCId
            RETURN c1, df_c, c2
        """,
            {
                "DFCId": kuzu_internal_id_to_element_id(dfc_id),
            },
        )

        records = result.get_all()
        if len(records) == 0:
            return None

        record = records[0]
        return {
            "source_class": record[0],
            "target_class": record[2],
            "dfc_relation": record[1],
        }


    def get_dfc_attributes(self, class_type: str) -> list[str]:
        qparams = { "ClassType": class_type }
        return (
            self.run_query(CypherQueries.get_dfc_attributes(), qparams)
            .get_all()[0][0]
        )

    def get_dfc_count(self, class_type: str) -> int:
        qparams = { "ClassType": class_type }
        return (
            self.run_query(CypherQueries.get_dfc_count(), qparams)
            .get_all()[0][0]
        )

    def get_end_class_count(self, class_type: str) -> int:
        qparams = { "ClassType": class_type }
        result = self.run_query(CypherQueries.get_end_class_count(), qparams)
        return result.get_all()[0][0]

    def get_entity_sample(self, class_type: str, sample_size: int) -> list[str]:
        raise RuntimeError("We do not support TokenReplay in KuzuDB")

    def get_entity_trace(self, class_type: str, entity_element_id: str) -> dict | None:
        raise RuntimeError("We do not support TokenReplay in KuzuDB")

    def get_entity_types(self, class_type: str = None) -> list[str]:
        qparams = { "ClassType": class_type }
        if class_type is None:
            result = self.run_query(CypherQueries.get_entity_types(),{})
        else:
            result = self.run_query(CypherQueries.get_entity_types_for_class(), qparams)

        return [x[0] for x in result.get_all()]

    def get_entities_for_dfc(self, dfc_id: str, limit: int, skip: int) -> list[dict]:
        result = self.run_query(
            """
            MATCH (c1: Class)-[df_c:DF_C]->(c2: Class)
            WHERE OFFSET(ID(df_c)) = $DFCId
            WITH c1, c2
            
            MATCH (e1: Event)-[:CORR]->(n: Entity)<-[:CORR]-(e2: Event)
            WHERE
                (e1)-[:DF]->(e2)
                AND (e1)-[:OBSERVED]->(c1)
                AND (e2)-[:OBSERVED]->(c2)
            RETURN DISTINCT n
            ORDER BY n.ID
            SKIP $Skip
            LIMIT $Limit
        """,
            {
                "DFCId": kuzu_internal_id_to_element_id(dfc_id),
                "Limit": limit,
                "Skip": skip,
            },
        )

        return [n[0] for n in result.get_all()]

    def get_entities_for_dfc_count(self, dfc_id: str) -> int:
        result = self.run_query(
            """
            MATCH (c1: Class)-[df_c:DF_C]->(c2: Class)
            WHERE OFFSET(ID(df_c)) = $DFCId
            WITH c1, c2
            MATCH (e1: Event)-[:CORR]->(n: Entity)<-[:CORR]-(e2: Event)
            WHERE
                (e1)-[:DF]->(e2)
                AND (e1)-[:OBSERVED]->(c1)
                AND (e2)-[:OBSERVED]->(c2)
            RETURN count(DISTINCT n) as Count
        """,
            {
                "DFCId": kuzu_internal_id_to_element_id(dfc_id),
            },
        )

        return result.get_all()[0][0]

    def get_entities_for_event_class(
            self, class_id: str, limit: int, skip: int
    ) -> list[dict]:
        result = self.run_query(
            """
            MATCH (c: Class)
            WHERE OFFSET(ID(c)) = $ClassId
            WITH c
            MATCH (e: Event)-[:CORR]->(n: Entity)
            WHERE (e)-[:OBSERVED]->(c)
            RETURN DISTINCT n
            ORDER BY n.ID
            SKIP $Skip
            LIMIT $Limit
        """,
            {
                "ClassId": kuzu_internal_id_to_element_id(class_id),
                "Limit": limit,
                "Skip": skip,
            },
        )

        return [n[0] for n in result.get_all()]

    def get_entities_for_event_class_count(self, class_id: str) -> int:
        result = self.run_query(
            """
            MATCH (c: Class)
            WHERE OFFSET(ID(c)) = $ClassId
            WITH c
            MATCH (e: Event)-[:CORR]->(n: Entity)
            WHERE (e)-[:OBSERVED]->(c)
            RETURN count(DISTINCT n) as Count
        """,
            {
                "ClassId": kuzu_internal_id_to_element_id(class_id),
            },
        )

        return result.get_all()[0][0]

    def get_start_class_count(self, class_type: str) -> int:
        qparams = {"ClassType": class_type}
        result = self.run_query(CypherQueries.get_start_class_count(), qparams)
        return result.get_all()[0][0]


    def get_event_class(self, event_class_id: str) -> dict | None:
        result = self.run_query(
            """
            MATCH (c: Class)
            WHERE OFFSET(ID(c)) = $ClassId
            RETURN c
        """,
            {
                "ClassId": kuzu_internal_id_to_element_id(event_class_id),
            },
        )

        records = result.get_all()
        if len(records) == 0:
            return None

        return records[0][0]

    def get_sync_edge_count(self, class_type: str) -> int:
        qparam = {"ClassType": class_type}
        result = self.run_query(CypherQueries.get_sync_edge_count(), qparam)
        return int(
            result.get_all()[0][0] // 2
        )  # Each SYNC relation is stored twice ()-[]->() and ()<-[]-()

    def get_proclet(
        self, class_type: str
    ) -> tuple[list[KuzuNode], list[KuzuRelationship], list[KuzuRelationship]]:
        result = self.run_query(
            """
            MATCH (c1:Class)
                WHERE c1.Type = $ClassType
            OPTIONAL MATCH (c1)-[df:DF_C]->(c2) WHERE c1.Type = c2.Type
            OPTIONAL MATCH (c1)-[sync:SYNC]->(c3) WHERE c1.Type = c3.Type
            return collect(DISTINCT c1), collect(DISTINCT c2), collect(DISTINCT c3), collect(DISTINCT df), collect(DISTINCT sync)
        """,
            {
                "ClassType": class_type,
            },
        )

        ids = set()
        x = result.get_all()[0]
        nodes = list(x[0])

        # collect existing ids and append unique nodes from additional lists
        ids.update(n["id"] for n in nodes)

        def _append_unique(source):
            for n in source:
                nid = n.get("id")
                if nid not in ids:
                    nodes.append(n)
                    ids.add(nid)

        _append_unique(x[1])
        _append_unique(x[2])

        # Nodes, DFC Edges, SYNC Edges
        return nodes, x[3], x[4]

    def get_proclet_types(self):
        result = self.run_query(CypherQueries.get_proclet_types(), {})
        return result.get_all()[0][0]

    # def get_process_executions(self, class_type, entity_ids: list[str], color_map: str | dict[str, str], animation_preferences: AnimationPreferences):
    def get_process_executions(
        self, class_type: str, entity_ids: list[str]
    ) -> tuple[list[dict], datetime, datetime]:
        raise NotImplementedError("TokenReplay is not implemented for KuzuDB")
