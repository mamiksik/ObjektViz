class OcelImportQueryLibrary:
    @staticmethod
    # create index on nodes with label 'node_label', for a specific attribute 'id'
    def q_create_index(nodel_label, id):
        index_query = (
            f"CREATE INDEX {nodel_label}_{id} FOR (n:{nodel_label}) ON (n.{id})"
        )
        print(index_query)
        return index_query

    @staticmethod
    def q_define_table(node_label, csv_header):
        col_types = {
            "timestamp": "TIMESTAMP",
            "start": "TIMESTAMP",
            "end": "TIMESTAMP",
            # 'id': 'INT32'
        }

        event_ddl = (
            ", ".join(f"{col} {col_types.get(col, 'STRING')}" for col in csv_header)
            + ", PRIMARY KEY(id)"
        )

        query_str = f"CREATE NODE TABLE {node_label} ({event_ddl})"
        return query_str

    @staticmethod
    # Use Neo4j's bulk import from CSV to create on :event node per record in CSV file
    # - 'fileName' is the system file path to the CSV file from which Neo4j will load
    # - 'logHeader' the list of attribute names of the CSV file
    # - an optional `LogID` to distinguish events coming from different event logs
    def q_load_csv_as_nodes(file_name, csv_header, node_label):
        return f"COPY {node_label} FROM '{file_name}' (header=true, quote='\"');"

    @staticmethod
    def q_link_node_to_node(
        sourceNode, sourceAttribute, relationship, targetNode, targetAttribute
    ):
        query_str = f"""
            MATCH (t:{targetNode}) WITH t
            MATCH (s:{sourceNode} {{ {sourceAttribute}: t.{targetAttribute} }}) WITH s,t
            MERGE (s)-[:{relationship}]->(t)"""
        return query_str

    @staticmethod
    def q_define_rel(rel_label, from_node, to_node, attributes):
        attrs = ""
        if attributes and len(attributes) > 0:
            attrs = ", " + ", ".join(map(lambda a: f"{a} STRING", attributes))

        query_str = (
            f"CREATE REL TABLE {rel_label} (FROM {from_node} TO {to_node} {attrs})"
        )
        return query_str

    @staticmethod
    def q_load_csv_as_relation(
        fileName,
        csvFrom,
        sourceNode,
        sourceAttr,
        csvType,
        relationship,
        csvTo,
        targetNode,
        targetAttribute,
    ) -> str:
        query = f"""
            LOAD FROM $dataframe
            MATCH (s:{sourceNode} {{ {sourceAttr}:{csvFrom} }} )
            MATCH (n:{targetNode} {{ {targetAttribute}:{csvTo} }} )
            MERGE (s) -[r:{relationship}]-> (n) ON CREATE SET r.type={csvType}
        """

        return query

    @staticmethod
    def q_load_csv_as_e2o_relation(fileName):
        return OcelImportQueryLibrary.q_load_csv_as_relation(
            fileName,
            "eventId",
            "Event",
            "id",
            "qualifier",
            "CORR",
            "objectId",
            "Entity",
            "id",
        )

    @staticmethod
    def q_ocel2_materialize_last_object_state():
        query_str = """
            MATCH (n:Entity) -[:HAS_ATTRIBUTE]-> (a) WITH DISTINCT n,a.name AS aName 
            MATCH (n) -[:HAS_ATTRIBUTE]-> (a {name:aName}) WITH n, a ORDER BY a.time DESC
            WITH n, a.name AS aName, collect(a.value)[0] AS aValue
            call apoc.create.setProperty(n, aName, aValue)
            YIELD node
            RETURN COUNT(*)
            """
        print(query_str)

        return query_str
