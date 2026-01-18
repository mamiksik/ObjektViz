import pathlib

import kuzu

from ocel.ocel2_import import OcelImport
from ocel.ocel2_proclet_queries import OcelProcletQueryLibrary


def import_ocel_to_kuzu(ocel_json_path: pathlib.Path, database_path: pathlib.Path):
    # Delete existing database file if exists
    if pathlib.Path(database_path).exists():
        pathlib.Path(database_path).unlink()

    db = kuzu.Database(database_path)
    conn = kuzu.Connection(db)

    oi = OcelImport(conn)
    oi.readJsonOcel(ocel_json_path)
    oi.prepare_objects()
    oi.prepare_events()

    oi.import_objects()
    oi.import_events()
    oi.import_e2o_relation()


def discover_proclet_kuzu(database_path: pathlib.Path):
    db = kuzu.Database(database_path)
    conn = kuzu.Connection(db)

    queries = OcelProcletQueryLibrary()

    print("Defining EKG tables...")
    conn.execute(queries.q_define_tables())

    print("Inferring Directly Follow...")
    conn.execute(queries.q_infer_directly_follow())

    print("Creating event classes...")
    conn.execute(queries.q_create_event_classes())

    print("Linking events to classes...")
    conn.execute(queries.q_link_events_to_classes())

    print("Lifting Directly Follow to class level...")
    conn.execute(queries.q_lift_directly_follow())

    print("Creating sync relations...")
    conn.execute(queries.q_create_sync_relations())

    print("Setting class frequencies...")
    conn.execute(queries.q_set_class_frequencies())

    print("Marking start and end events...")
    conn.execute(queries.q_mark_start_end_events())
    conn.execute(queries.q_set_start_count())
    conn.execute(queries.q_set_end_count())


if __name__ == "__main__":
    # parse command line arguments
    import argparse

    parser = argparse.ArgumentParser(
        description="Import OCEL JSON file into Kuzu database and discover proclet model."
    )
    parser.add_argument(
        "ocel_json", type=pathlib.Path, help="Path to the OCEL JSON file."
    )
    parser.add_argument(
        "database", type=pathlib.Path, help="Path to the Kuzu database file."
    )
    args = parser.parse_args()

    # Ask for confirmation if database file exists
    if args.database.exists():
        response = input(
            f"Database file {args.database} already exists. Overwrite? (y/n): "
        )
        if response.lower() != "y":
            print("Aborting.")
            exit(0)

    import_ocel_to_kuzu(args.ocel_json, args.database)
    discover_proclet_kuzu(args.database)

    print("OCEL import and proclet discovery completed.")
    print(f"Kuzu database located at: {args.database}")
