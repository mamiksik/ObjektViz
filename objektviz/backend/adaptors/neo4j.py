import warnings
from datetime import datetime
from typing import Iterator

from neo4j import Driver
from neo4j.graph import Node, Relationship

from objektviz.backend.BackendConfig import BackendConfig
from objektviz.backend.adaptors.shared import AbstractEKGRepository
from objektviz.backend.dot_elements import AbstractDotNode, AbstractDotEdge, CROSS_CLUSTER_SENTINEL
from objektviz.backend.shaders import AbstractShader
from objektviz.backend.utils import shader_factory


def from_neo4j_to_dot_elements(
    nodes: list[Node],
    edges: list[Relationship],
    config: BackendConfig,
) -> tuple[
    Iterator[AbstractDotNode],
    Iterator[AbstractDotEdge],
    dict[str, AbstractShader],
    dict[str, AbstractShader],
    BackendConfig,
]:
    """Wrapper around to_dot that consumes Neo4J query output rather than instances of DotAbstractElement"""

    if len(nodes) == 0:
        warnings.warn("0 nodes were passed to neo4j_proclet_to_dot")

    if len(edges) == 0:
        warnings.warn("0 edges were passed to neo4j_proclet_to_dot")

    node_shaders, edge_shaders = shader_factory(config)
    _nodes = map(lambda node: Neo4JDotNode(node, node_shaders, config), nodes)
    _edges = map(lambda edge: Neo4JDotEdge(edge, edge_shaders, config), edges)

    return _nodes, _edges, node_shaders, edge_shaders, config

# IntelliJ has problems with inferring the type if neo4j.graph.Relationship is used
class Neo4JDotEdge(AbstractDotEdge[Relationship]):
    """Takes care of producing dot descriptor code for edge (see parent class doc)"""
    def get_nesting_attr(self, name, default=None):
        # This is the best way to handle this since, for kuzu we are now generating suboptimal solution
        start_attr = self.entity.start_node.get(name, default)
        end_attr = self.entity.end_node.get(name, default)
        if start_attr == end_attr:
            return start_attr
        else:
            return CROSS_CLUSTER_SENTINEL

    @property
    def element_id(self):
        return self.entity.element_id

    @property
    def start_element_id(self):
        return self.entity.start_node.element_id

    @property
    def end_element_id(self):
        return self.entity.end_node.element_id

    @property
    def is_sync_edge(self):
        return self.entity.type == "SYNC"



class Neo4JDotNode(AbstractDotNode[Node]):
    """Takes care of producing dot descriptor code for node (see parent class doc)"""

    @property
    def element_id(self):
        return self.entity.element_id


class Neo4JEKGRepository(AbstractEKGRepository):
    def get_entity_types(self, class_type: str = None) -> list[str]:
        if class_type is None:
            result = self.run_query(
                """
                MATCH (c: Class)
                WITH DISTINCT c.EntityType as entityType
                RETURN entityType
            """,
                {},
            )
        else:
            result = self.run_query(
                """
                MATCH (c: Class {Type: $ClassType})
                WITH DISTINCT c.EntityType as entityType
                RETURN entityType
            """,
                {
                    "ClassType": class_type,
                },
            )

        return [r.get("entityType") for r in result.records]

    def get_entities_for_dfc_count(self, dfc_id: str) -> int:
        result = self.run_query(
            """
            MATCH (n: Entity)<-[:CORR]-(e1: Event)-[df:DF]->(e2: Event)-[:CORR]->(n),
                  (c1: Class)-[df_c:DF_C]->(c2: Class)
            WHERE elementId(df_c) = $DFCId
              AND (e1)-[:OBSERVED]->(c1)
              AND (e2)-[:OBSERVED]->(c2)
            RETURN count(DISTINCT n) as Count
        """,
            {"DFCId": dfc_id},
        )

        return result.records[0].get("Count")

    def get_entities_for_dfc(self, dfc_id: str, limit: int, skip: int) -> list[dict]:
        result = self.run_query(
            """
            MATCH (n: Entity)<-[:CORR]-(e1: Event)-[df:DF]->(e2: Event)-[:CORR]->(n),
                  (c1: Class)-[df_c:DF_C]->(c2: Class)
            WHERE elementId(df_c) = $DFCId 
              AND n.EntityType = c1.EntityType
              AND n.EntityType = c2.EntityType
              AND (e1)-[:OBSERVED]->(c1)
              AND (e2)-[:OBSERVED]->(c2)
            RETURN DISTINCT n
            SKIP $Skip
            LIMIT $Limit
        """,
            {
                "DFCId": dfc_id,
                "Limit": limit,
                "Skip": skip,
            },
            to_dict=True,
        )

        return result

    def get_entities_for_event_class_count(self, class_id: str) -> int:
        result = self.run_query(
            """
            MATCH (n: Entity)<-[:CORR]-(e:Event)-[:OBSERVED]->(c: Class)
            WHERE elementId(c) = $ClassId AND n.EntityType = c.EntityType
            RETURN count(DISTINCT n) as Count
        """,
            {"ClassId": class_id},
        )

        return result.records[0].get("Count")

    def get_entities_for_event_class(
        self, class_id: str, limit: int, skip: int
    ) -> list[dict]:
        result = self.run_query(
            """
            MATCH (n: Entity)<-[:CORR]-(e: Event)-[:OBSERVED]->(c: Class)
            WHERE 
                elementId(c) = $ClassId
                AND n.EntityType = c.EntityType
            RETURN DISTINCT n
            SKIP $Skip
            LIMIT $Limit
        """,
            {
                "ClassId": class_id,
                "Limit": limit,
                "Skip": skip,
            },
            to_dict=True,
        )

        return result

    def get_dfc(self, dfc_id: str) -> dict | None:
        result = self.run_query(
            """
            MATCH (c1: Class)-[df_c:DF_C]->(c2: Class)
            WHERE elementId(df_c) = $DFCId
            RETURN c1, df_c, c2
        """,
            {"DFCId": dfc_id},
            to_dict=True,
        )

        if len(result) == 0:
            return None

        return {
            "source_class": result[0]["c1"],
            "dfc_relation": result[0]["df_c"][0],
            "target_class": result[0]["c2"],
        }

    def get_event_class(self, event_class_id: str) -> dict | None:
        result = self.run_query(
            """
            MATCH (c: Class)
            WHERE elementId(c) = $ClassId
            RETURN c
        """,
            {"ClassId": event_class_id},
            to_dict=True,
        )

        if len(result) == 0:
            return None
        print(result)
        return result[0]["c"]

    def __init__(self, driver: Driver):
        self.driver = driver

    def run_query(self, query, params, to_dict: bool = False):
        # print("\n" + query + " " + str(params))
        with self.driver.session() as session:
            if to_dict:
                result = session.run(query, parameters=params).data()
            else:
                result = session.run(query, parameters=params).to_eager_result()
            return result

    def class_attributes(self, class_type: str) -> list[str]:
        return (
            self.run_query(
                """
            MATCH (c: Class {Type: $ClassType})
            UNWIND keys(c) as key
            RETURN collect(DISTINCT key)
        """,
                {
                    "ClassType": class_type,
                },
            )
            .records[0]
            .value()
        )

    def dfc_attributes(self, class_type: str) -> list[str]:
        return (
            self.run_query(
                """
            MATCH (: Class {Type: $ClassType})-[r:DF_C]->(: Class {Type: $ClassType})
            UNWIND keys(r) as key
            RETURN collect(DISTINCT key)
        """,
                {
                    "ClassType": class_type,
                },
            )
            .records[0]
            .value()
        )

    def class_names(self, class_type) -> list[str]:
        return (
            self.run_query(
                """
            MATCH (c: Class {Type: $ClassType})
            WITH DISTINCT c.Name as name
            RETURN name
        """,
                {
                    "ClassType": class_type,
                },
            )
            .records[0]
            .value()
        )

    def proclet(
        self, class_type: str
    ) -> tuple[
        list[Node],
        list[Relationship],
        list[Relationship],
    ]:
        result = self.run_query(
            """
            MATCH (c1:Class)
                WHERE c1.Type = $ClassType
            OPTIONAL MATCH (c1)-[df_c:DF_C]->(c2)
            OPTIONAL MATCH (c1)-[sync:SYNC]->(c3)
            WITH
                apoc.coll.union(collect(c1), collect(c2)) as nodes,
                collect(df_c) as edges,
                collect(sync) as sync
            RETURN
                nodes,
                edges,
                sync
        """,
            {
                "ClassType": class_type,
            },
        )

        return (
            result.records[0].get("nodes"),
            result.records[0].get("edges"),
            result.records[0].get("sync"),
        )

    # def get_process_executions(self, class_type, entity_ids: list[str], color_map: str | dict[str, str], animation_preferences: AnimationPreferences):
    def get_process_executions(
        self, class_type: str, entity_ids: list[str]
    ) -> tuple[list[dict], datetime, datetime]:
        # start_date
        start_date = (
            self.run_query(
                """
            CYPHER runtime=parallel
            MATCH (n: Entity)<-[:CORR]-(e1: Event)
            WHERE n.ID in $EntityIDs
            ORDER BY e1.timestamp ASC
            RETURN e1.timestamp as datetime
            LIMIT 1
        """,
                params={
                    "EntityIDs": entity_ids,
                },
            )
            .records[0]
            .get("datetime")
        )

        end_date = (
            self.run_query(
                """
            CYPHER runtime=parallel
            MATCH (n: Entity)<-[:END]-(e1: Event)
            WHERE n.ID in $EntityIDs
            ORDER BY e1.timestamp DESC
            RETURN e1.timestamp as datetime
            LIMIT 1
        """,
                params={
                    "EntityIDs": entity_ids,
                },
            )
            .records[0]
            .get("datetime")
        )
        print("Start Data ", start_date)
        print("END Data ", end_date)

        return (
            self.run_query(
                """
            CYPHER runtime=parallel
            MATCH (n: Entity)
            WHERE n.ID in $EntityIDs
            CALL(n) {
                MATCH
                    (n)<-[:CORR]-(e1: Event)-[df:DF]->(e2: Event)-[:CORR]->(n),
                    (c1: Class {Type: $ClassType})-[df_c:DF_C]->(c2: Class),
                    (e1)-[:OBSERVED]->(c1),
                    (e2)-[:OBSERVED]->(c2)
                WHERE
                    c1.Type = c2.Type
                    AND n.EntityType  = df.EntityType
                    AND c1.EntityType = n.EntityType
                    AND c2.EntityType = n.EntityType
                ORDER BY e1.timestamp
                WITH
                    n,
                    apoc.coll.union(
                        collect(elementId(c1)),
                        apoc.coll.union(
                            collect(elementId(c2)),
                            collect(elementId(df_c))
                        )
                    ) as ActiveElementIds,
                    collect({
                        DFCElementId: elementId(df_c),
                        DurationSec: duration.inSeconds(e1.timestamp, e2.timestamp).seconds,
                        StartOffsetSec: duration.inSeconds($StartDate, e1.timestamp).seconds
                    }) as TraceSegments
    
                RETURN ActiveElementIds, TraceSegments
            }
            RETURN n as Entity, elementId(n) as EntityElementId, ActiveElementIds, TraceSegments
        """,
                params={
                    "ClassType": class_type,
                    "EntityIDs": entity_ids,
                    "StartDate": start_date,
                    "EndDate": end_date,
                },
                to_dict=True,
            ),
            start_date,
            end_date,
        )

    def get_entity_trace(
        self,
        class_type: str,
        entity_element_id: str,
    ) -> dict | None:
        result = self.run_query(
            """
            CYPHER runtime=parallel
            MATCH (n: Entity)
            WHERE elementId(n) = $EntityElementId
            MATCH (e1: Event)-[:CORR]->(n)
            ORDER BY e1.timestamp ASC
            WITH n, e1
            RETURN n as Entity, collect(e1) as Events
        """,
            params={
                "ClassType": class_type,
                "EntityElementId": entity_element_id,
            },
            to_dict=True,
        )

        if len(result) == 0:
            return None

        return result[0]

    def entity_sample(self, class_type: str, sample_size: int) -> list[str]:
        result = self.run_query(
            """
            CYPHER runtime=parallel
            MATCH (n:Entity)<-[corr:CORR]-(e:Event)-[obs:OBSERVED]->(:Class {Type: $ClassType})
            //WHERE n.ID = "O2" OR n.ID = "B"
            WITH DISTINCT n
            WITH n, rand() as r
            ORDER BY r
            RETURN DISTINCT n.ID as ID
            LIMIT $Limit
        """,
            {
                "ClassType": class_type,
                "Limit": sample_size,
            },
        )

        return [n.get("ID") for n in result.records]

    def count_classes(self, class_type: str) -> int:
        result = self.run_query(
            """
            MATCH (c: Class {Type: $ClassType})
            RETURN count(DISTINCT c) as Count
        """,
            {
                "ClassType": class_type,
            },
        )

        return result.records[0].get("Count")

    def count_dfc(self, class_type: str) -> int:
        result = self.run_query(
            """
            MATCH (: Class {Type: $ClassType})-[r:DF_C]->(: Class {Type: $ClassType})
            RETURN count(DISTINCT r) as Count
        """,
            {
                "ClassType": class_type,
            },
        )

        return result.records[0].get("Count")

    def count_sync(self, class_type: str) -> int:
        result = self.run_query(
            """
            MATCH (:Class {Type: $ClassType})-[r:SYNC]->(: Class {Type: $ClassType})
            RETURN count(DISTINCT r) as Count
        """,
            {
                "ClassType": class_type,
            },
        )

        return int(
            result.records[0].get("Count") / 2
        )  # Each SYNC relation is stored twice ()-[]->() and ()<-[]-()

    def proclet_types(self):
        result = self.run_query(
            """
            MATCH (c: Class)
            RETURN collect(DISTINCT c.Type) as Types
        """,
            {},
        )

        return result.records[0].get("Types")

    def count_start_activities(self, class_type: str) -> int:
        result = self.run_query(
            """
            MATCH (c: Class {Type: $ClassType})
            WHERE c.StartCount IS NOT NULL AND c.StartCount > 0
            RETURN count(DISTINCT c) as Count
        """,
            {
                "ClassType": class_type,
            },
        )

        return result.records[0].get("Count")

    def count_end_activities(self, class_type: str) -> int:
        result = self.run_query(
            """
            MATCH (c: Class {Type: $ClassType})
            WHERE c.EndCount IS NOT NULL AND c.EndCount > 0
            RETURN count(DISTINCT c) as Count
        """,
            {
                "ClassType": class_type,
            },
        )

        return result.records[0].get("Count")
