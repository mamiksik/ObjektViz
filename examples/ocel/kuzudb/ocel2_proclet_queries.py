class OcelProcletQueryLibrary:
    @staticmethod
    def q_define_tables():
        return """
             CREATE NODE TABLE Class (
                id String,
                type String,
                EventType String,
                EntityType String,
                StartCount INT64 DEFAULT -1,
                EndCount INT64 DEFAULT -1,
                frequency INT64 DEFAULT -1,
                PRIMARY KEY(id)
            );
            
            CREATE REL TABLE DF (FROM Event TO Event, EntityType STRING, id STRING);
            CREATE REL TABLE DF_C (FROM Class TO Class, EntityType STRING, frequency Int64);
            CREATE REL TABLE OBSERVED (FROM Event to Class);
            CREATE REL TABLE SYNC (FROM Class to Class);
            CREATE REL TABLE P_START (FROM Event to Entity);
            CREATE REL TABLE P_END (FROM Event to Entity);
        """

    @staticmethod
    def q_infer_directly_follow():
        return """
            MATCH (n:Entity)
            MATCH (n)<-[:CORR]-(e)
            WITH n, e AS nodes ORDER BY e.time
            LIMIT 10000 // Kuzu requires limiting the size of order by (hack: limit to 10k max path length)
            
            WITH n, collect(nodes) AS event_node_list
            UNWIND range(1, size(event_node_list)-1) AS i
            WITH n, event_node_list[i] AS t1, event_node_list[i+1] AS t2
            
            MATCH (e1: Event {id: t1.id}), (e2: Event {id: t2.id})
            MERGE (e1)-[df:DF {EntityType:n.type, id:n.id}]->(e2)
        """

    @staticmethod
    def q_create_event_classes():
        return """
            MATCH (e:Event)-[:CORR]->(n:Entity) 
            WITH distinct e.type as EType, n.type as NType
            MERGE ( c : Class { id: EType+"_"+NType, EventType:EType, EntityType:NType, type:"EventType,EntityType"})
        """

    @staticmethod
    def q_link_events_to_classes():
        return """
            MATCH ( c :Class ) WHERE c.type = "EventType,EntityType"
            MATCH ( e :Event ) WHERE c.EventType = e.type
            CREATE (e) -[:OBSERVED]-> (c)
        """

    @staticmethod
    def q_lift_directly_follow():
        return """
            MATCH (c1:Class) <-[:OBSERVED]- (e1:Event) -[df:DF]-> (e2:Event) -[:OBSERVED]-> (c2:Class)
            MATCH (e1) -[:CORR] -> (n) <-[:CORR]- (e2)
            WHERE 
                c1.type = c2.type 
                AND c1.EntityType=n.type AND c2.EntityType=n.type
                AND n.type = df.EntityType
            WITH n.type as EType, c1, count(df) AS df_freq, c2
            
            MERGE (c1) -[rel2:DF_C {EntityType:EType}]-> (c2) 
                ON CREATE SET rel2.frequency=df_freq
        """

    @staticmethod
    def q_create_sync_relations():
        return """
            MATCH ( c1 : Class ), ( c2 : Class) 
            WHERE c1.EventType=c2.EventType AND c1.EntityType <> c2.EntityType
            MERGE (c1)-[:SYNC]->(c2)
        """

    @staticmethod
    def q_set_class_frequencies() -> str:
        return """
            MATCH (c:Class)<-[:OBSERVED]-(e:Event)
            WITH c, count(e) as cnt
            SET c.frequency = cnt
        """


    def q_mark_start_end_events(self) -> str:
        return """
            MATCH (n:Entity)<-[:CORR]-(e:Event)
            WITH n, e ORDER BY e.time ASC
            LIMIT 10000
            WITH n, collect(e) AS event_node_list
            WITH n, event_node_list[1] AS t_start_event, event_node_list[-1] AS t_end_event
            MATCH 
                (start_event:Event {id: t_start_event.id}), 
                (end_event:Event {id: t_end_event.id})
            MERGE (start_event)-[:P_START]->(n)
            MERGE (end_event)-[:P_END]->(n)
        """

    @staticmethod
    def q_set_start_count():
        return """
            MATCH (n:Entity)<-[:P_START]-(e:Event)-[:OBSERVED]->(c:Class)
            WITH c, count(e) as start_cnt
            SET c.StartCount = start_cnt
        """

    @staticmethod
    def q_set_end_count():
        return """
            MATCH (n:Entity)<-[:P_END]-(e:Event)-[:OBSERVED]->(c:Class)
            WITH c, count(e) as end_cnt
            SET c.EndCount = end_cnt
        """
