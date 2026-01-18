import warnings
from datetime import datetime
from typing import Iterator

import neo4j

from objektviz.backend.BackendConfig import BackendConfig
from objektviz.backend.adaptors.shared import AbstractEKGRepository
from objektviz.backend.dot_elements import DotNode, DotEdge
from objektviz.backend.shaders import AbstractShader
from objektviz.backend.utils import shader_factory


def from_neo4j_to_dot_elements(
        nodes: list[neo4j.graph.Node],
        edges: list[neo4j.graph.Relationship],
        config: BackendConfig
) -> tuple[Iterator[DotNode], Iterator[DotEdge], dict[str, AbstractShader], dict[str, AbstractShader], BackendConfig]:
    """ Wrapper around to_dot that consumes Neo4J query output rather than instances of DotAbstractElement"""

    if len(nodes) == 0:
        warnings.warn("0 nodes were passed to neo4j_proclet_to_dot")

    if len(edges) == 0:
        warnings.warn("0 edges were passed to neo4j_proclet_to_dot")

    node_shaders, edge_shaders = shader_factory(config)
    _nodes = map(lambda node: DotNode(node, node_shaders, config), nodes)
    _edges = map(lambda edge: DotEdge(edge, edge_shaders, config), edges)

    return _nodes, _edges, node_shaders, edge_shaders, config


class Neo4JEKGRepository(AbstractEKGRepository):
    def __init__(self, driver: neo4j.Driver):
        self.driver = driver

    def run_query(self, query, params, to_dict: bool = False):
        print('\n'+query + " " + str(params))
        with self.driver.session() as session:
            if to_dict:
                result = session.run(query, parameters=params).data()
            else:
                result = session.run(query, parameters=params).to_eager_result()
            return result

    def class_attributes(self, class_type: str) -> list[str]:
        return  self.run_query( """
            MATCH (c: Class {Type: $ClassType})
            UNWIND keys(c) as key
            RETURN collect(DISTINCT key)
        """, {
            "ClassType": class_type,
        }).records[0].value()

    def dfc_attributes(self, class_type: str) -> list[str]:
        return self.run_query( """
            MATCH (: Class {Type: $ClassType})-[r:DF_C]->(: Class {Type: $ClassType})
            UNWIND keys(r) as key
            RETURN collect(DISTINCT key)
        """, {
            "ClassType": class_type,
    }).records[0].value()

    def class_names(self, class_type) -> list[str]:
        return self.run_query("""
            MATCH (c: Class {Type: $ClassType})
            WITH DISTINCT c.Name as name
            RETURN name
        """, {
            "ClassType": class_type,
        }).records[0].value()

    def proclet(self, class_type: str) -> tuple[list[neo4j.graph.Node], list[neo4j.graph.Relationship]]:
        result = self.run_query("""
            MATCH (c1:Class)
                WHERE c1.Type = $ClassType
            OPTIONAL MATCH (c1)-[df:DF_C]->(c2)
            OPTIONAL MATCH (c1)-[sync:SYNC]->(c3)
            WITH
                apoc.coll.union(collect(c1), collect(c2)) as nodes,
                apoc.coll.union(collect(df), collect(sync)) as edges
            RETURN
                nodes,
                edges
        """, {
            "ClassType": class_type,
        })

        return result.records[0].get("nodes"), result.records[0].get("edges")

    # def get_process_executions(self, class_type, entity_ids: list[str], color_map: str | dict[str, str], animation_preferences: AnimationPreferences):
    def get_process_executions(self, class_type: str, entity_ids: list[str]) -> tuple[list[dict], datetime, datetime]:
        # start_date
        start_date = self.run_query("""
            CYPHER runtime=parallel
            MATCH (n: Entity)<-[:CORR]-(e1: Event)
            WHERE n.ID in $EntityIDs
            ORDER BY e1.timestamp ASC
            RETURN e1.timestamp as datetime
            LIMIT 1
        """, params={
            "EntityIDs": entity_ids,
        }).records[0].get('datetime')

        end_date = self.run_query( """
            CYPHER runtime=parallel
            MATCH (n: Entity)<-[:END]-(e1: Event)
            WHERE n.ID in $EntityIDs
            ORDER BY e1.timestamp DESC
            RETURN e1.timestamp as datetime
            LIMIT 1
        """, params={
            "EntityIDs": entity_ids,
        }).records[0].get('datetime')
        print("Start Data ", start_date)
        print("END Data ", end_date)

        return self.run_query("""
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
            RETURN n as Entity, ActiveElementIds, TraceSegments
        """,params={
            "ClassType": class_type,
            "EntityIDs": entity_ids,
            "StartDate": start_date,
            "EndDate": end_date
        }, to_dict=True), start_date, end_date

    def entity_sample(self, class_type: str, sample_size: int) -> list[str]:
        result = self.run_query("""
            CYPHER runtime=parallel
            MATCH (n:Entity)<-[corr:CORR]-(e:Event)-[obs:OBSERVED]->(:Class {Type: $ClassType})
            //WHERE n.ID = "O2" OR n.ID = "B"
            WITH DISTINCT n
            WITH n, rand() as r
            ORDER BY r
            RETURN DISTINCT n.ID as ID
            LIMIT $Limit
        """, {
            "ClassType": class_type,
            "Limit": sample_size,
        })

        return [
            n.get("ID") for n in result.records
        ]

    def count_classes(self, class_type: str) -> int:
        result = self.run_query("""
            MATCH (c: Class {Type: $ClassType})
            RETURN count(DISTINCT c) as Count
        """, {
            "ClassType": class_type,
        })

        return result.records[0].get("Count")

    def count_dfc(self, class_type: str) -> int:
        result = self.run_query("""
            MATCH (: Class {Type: $ClassType})-[r:DF_C]->(: Class {Type: $ClassType})
            RETURN count(DISTINCT r) as Count
        """, {
            "ClassType": class_type,
        })

        return result.records[0].get("Count")

    def count_sync(self, class_type: str) -> int:
        result = self.run_query("""
            MATCH (:Class {Type: $ClassType})-[r:SYNC]->(: Class {Type: $ClassType})
            RETURN count(DISTINCT r) as Count
        """, {
            "ClassType": class_type,
        })

        return int(result.records[0].get("Count") / 2) # Each SYNC relation is stored twice ()-[]->() and ()<-[]-()

    def proclet_types(self):
        result = self.run_query("""
            MATCH (c: Class)
            RETURN collect(DISTINCT c.Type) as Types
        """, {})

        return result.records[0].get("Types")

    def count_start_activities(self, class_type: str) -> int:
        result = self.run_query("""
            MATCH (c: Class {Type: $ClassType})
            WHERE c.StartCount IS NOT NULL AND c.StartCount > 0
            RETURN count(DISTINCT c) as Count
        """, {
            "ClassType": class_type,
        })

        return result.records[0].get("Count")

    def count_end_activities(self, class_type: str) -> int:
        result = self.run_query("""
            MATCH (c: Class {Type: $ClassType})
            WHERE c.EndCount IS NOT NULL AND c.EndCount > 0
            RETURN count(DISTINCT c) as Count
        """, {
            "ClassType": class_type,
        })

        return result.records[0].get("Count")