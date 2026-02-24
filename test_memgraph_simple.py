from neo4j import GraphDatabase
import os
import sys

# Minimal test
uri = "bolt+ssc://54.193.112.175:7687"
user = "naomi.l.touchet@gmail.com"
pw = "Catwalk-Refuge-Lent9-Love<3"

print(f"Connecting to {uri}...")
try:
    driver = GraphDatabase.driver(
        uri, 
        auth=(user, pw),
        connection_timeout=5.0,
        max_connection_lifetime=60.0
    )
    with driver.session() as session:
        print("Running query...")
        result = session.run("RETURN 1 AS n")
        val = result.single()["n"]
        print(f"Success! Result: {val}")
    driver.close()
except Exception as e:
    print(f"Failed: {e}")
