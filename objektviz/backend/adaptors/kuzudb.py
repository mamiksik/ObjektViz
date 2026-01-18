import warnings
from datetime import datetime
from typing import Iterator, Any

import kuzu

from objektviz.backend.BackendConfig import BackendConfig
from objektviz.backend.adaptors.shared import AbstractEKGRepository
from objektviz.backend.dot_elements import DotNode, DotEdge
from objektviz.backend.shaders import AbstractShader
from objektviz.backend.utils import shader_factory

type KuzuNode = Any # Placeholder for kuzu.graph.Node
type KuzuRelationship = Any # Placeholder for kuzu.graph.Relationship

def kuzu_internal_id_to_str(node: dict) -> str:
    # return f"[table={node['table']}][offset={node['offset']}]"
    return f"{node['table']}:{node['offset']}"

def kuzu_internal_id_to_element_id(id: str) -> str:
    return id.split(":")[1]

class KuzuDotNode(DotNode):
    @property
    def element_id(self):
        return kuzu_internal_id_to_str(self.entity['_id'])

class KuzuDotEdge(DotEdge):
    @property
    def element_id(self):
        return kuzu_internal_id_to_str(self.entity['_id'])

    @property
    def is_sync_edge(self):
        return self.entity['_label'] == "SYNC"

    @property
    def start_element_id(self):
        return kuzu_internal_id_to_str(self.entity['_src'])

    @property
    def end_element_id(self):
        return kuzu_internal_id_to_str(self.entity['_dst'])

def from_kuzu_to_dot_elements(
        nodes: list[KuzuNode],
        edges: list[KuzuRelationship],
        config: BackendConfig
) -> tuple[Iterator[KuzuDotNode], Iterator[KuzuDotEdge], dict[str, AbstractShader], dict[str, AbstractShader], BackendConfig]:
    """ Wrapper around to_dot that consumes Neo4J query output rather than instances of DotAbstractElement"""

    if len(nodes) == 0:
        warnings.warn("0 nodes were passed to neo4j_proclet_to_dot")

    if len(edges) == 0:
        warnings.warn("0 edges were passed to neo4j_proclet_to_dot")

    node_shaders, edge_shaders = shader_factory(config)
    _nodes = list(map(lambda node: KuzuDotNode(node, node_shaders, config), nodes))
    _edges = list(map(lambda edge: KuzuDotEdge(edge, edge_shaders, config), edges))

    return _nodes, _edges, node_shaders, edge_shaders, config


class KuzuEKGRepository(AbstractEKGRepository):
    def __init__(self, connection: kuzu.Connection):
        self.connection = connection

    def run_query(self, query, params) -> kuzu.QueryResult:
        # print('\n'+query + " " + str(params))
        return self.connection.execute(query, params)

    def class_attributes(self, class_type: str) -> list[str]:
        return  self.run_query( """
            MATCH (c: Class {type: $ClassType})
            UNWIND keys(c) as key
            RETURN collect(DISTINCT key)
        """, {
            "ClassType": class_type,
        }).get_all()[0][0]

    def dfc_attributes(self, class_type: str) -> list[str]:
        return self.run_query( """
            MATCH (: Class {type: $ClassType})-[r:DF_C]->(: Class {type: $ClassType})
            UNWIND keys(r) as key
            RETURN collect(DISTINCT key)
        """, {
            "ClassType": class_type,
    }).get_all()[0][0]

    def class_names(self, class_type) -> list[str]:
        return self.run_query("""
            MATCH (c: Class {type: $ClassType})
            WITH DISTINCT c.EventType as name
            RETURN name
        """, {
            "ClassType": class_type,
        }).get_all()[0][0]

    def get_entity_types(self, class_type: str = None) -> list[str]:
        if class_type is None:
            return [x[0] for x in self.run_query("""
                MATCH (c: Class)
                WITH DISTINCT c.EntityType as entityType
                RETURN entityType
            """, {}).get_all()]

        raise NotImplementedError("KuzuEKGRepository.get_entity_types with class_type is not implemented yet")
        # return self.run_query("""
        #     MATCH (c: Class {type: $ClassType})
        #     WITH DISTINCT c.EntityType as entityType
        #     RETURN entityType
        # """, {
        #     "ClassType": class_type,
        # }).get_all()[0]

    def proclet(self, class_type: str) -> tuple[list[KuzuNode], list[KuzuRelationship]]:
        result = self.run_query("""
            MATCH (c1:Class)
                WHERE c1.Type = $ClassType
            OPTIONAL MATCH (c1)-[df:DF_C]->(c2) WHERE c1.Type = c2.Type
            OPTIONAL MATCH (c1)-[sync:SYNC]->(c3) WHERE c1.Type = c3.Type
            return collect(DISTINCT c1), collect(DISTINCT c2), collect(DISTINCT c3), collect(DISTINCT df), collect(DISTINCT sync)
        """, {
            "ClassType": class_type,
        })

        ids = set()
        x = result.get_all()[0]
        nodes = list(x[0])

        # collect existing ids and append unique nodes from additional lists
        ids.update(n['id'] for n in nodes)

        def _append_unique(source):
            for n in source:
                nid = n.get('id')
                if nid not in ids:
                    nodes.append(n)
                    ids.add(nid)

        _append_unique(x[1])
        _append_unique(x[2])

        edges = x[3]
        edges.extend(x[4])

        return nodes, edges

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

        return result.get_all()[0][0]

    def count_dfc(self, class_type: str) -> int:
        result = self.run_query("""
            MATCH (: Class {Type: $ClassType})-[r:DF_C]->(: Class {Type: $ClassType})
            RETURN count(DISTINCT r) as Count
        """, {
            "ClassType": class_type,
        })

        return result.get_all()[0][0]

    def count_sync(self, class_type: str) -> int:
        result = self.run_query("""
            MATCH (:Class {type: $ClassType})-[r:SYNC]->(: Class {type: $ClassType})
            RETURN count(DISTINCT r) as Count
        """, {
            "ClassType": class_type,
        })

        return int(result.get_all()[0][0] / 2) # Each SYNC relation is stored twice ()-[]->() and ()<-[]-()

    def proclet_types(self):
        result = self.run_query("""
            MATCH (c: Class)
            RETURN collect(DISTINCT c.Type) as Types
        """, {})

        return result.get_all()[0][0]

    def count_start_activities(self, class_type: str) -> int:
        try:
            result = self.run_query("""
                MATCH (c: Class {Type: $ClassType})
                WHERE c.StartCount IS NOT NULL AND c.StartCount > 0
                RETURN count(DISTINCT c) as Count
            """, {
                "ClassType": class_type,
            })

            return result.get_all()[0][0]
        except RuntimeError:
            return None

    def count_end_activities(self, class_type: str) -> int:
        try:
            result = self.run_query("""
                MATCH (c: Class {Type: $ClassType})
                WHERE c.EndCount IS NOT NULL AND c.EndCount > 0
                RETURN count(DISTINCT c) as Count
            """, {
                "ClassType": class_type,
            })

            return result.get_all()[0][0]
        except RuntimeError:
            return None


    def get_entities_for_dfc_count(self, dfc_id: str) -> int:
        result = self.run_query("""
            MATCH (c1: Class)-[df_c:DF_C]->(c2: Class)
            WHERE OFFSET(ID(df_c)) = $DFCId
            WITH c1, c2
            MATCH (e1: Event)-[:CORR]->(n: Entity)<-[:CORR]-(e2: Event)
            WHERE
                (e1)-[:DF]->(e2)
                AND (e1)-[:OBSERVED]->(c1)
                AND (e2)-[:OBSERVED]->(c2)
            RETURN count(DISTINCT n) as Count
        """, {
            "DFCId": kuzu_internal_id_to_element_id(dfc_id),
        })

        return result.get_all()[0][0]

    def get_entities_for_dfc(self, dfc_id: str, limit: int, skip: int) -> list[dict]:
        result = self.run_query("""
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
        """, {
            "DFCId": kuzu_internal_id_to_element_id(dfc_id),
            "Limit": limit,
            "Skip": skip,
        })

        return [n[0] for n in result.get_all()]


    def get_entities_for_event_class_count(self, class_id: str) -> int:
        result = self.run_query("""
            MATCH (c: Class)
            WHERE OFFSET(ID(c)) = $ClassId
            WITH c
            MATCH (e: Event)-[:CORR]->(n: Entity)
            WHERE (e)-[:OBSERVED]->(c)
            RETURN count(DISTINCT n) as Count
        """, {
            "ClassId": kuzu_internal_id_to_element_id(class_id),
        })

        return result.get_all()[0][0]


    def get_entities_for_event_class(self, class_id: str, limit: int, skip: int) -> list[dict]:
        result = self.run_query("""
            MATCH (c: Class)
            WHERE OFFSET(ID(c)) = $ClassId
            WITH c
            MATCH (e: Event)-[:CORR]->(n: Entity)
            WHERE (e)-[:OBSERVED]->(c)
            RETURN DISTINCT n
            ORDER BY n.ID
            SKIP $Skip
            LIMIT $Limit
        """, {
            "ClassId": kuzu_internal_id_to_element_id(class_id),
            "Limit": limit,
            "Skip": skip,
        })

        return [n[0] for n in result.get_all()]