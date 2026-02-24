import os
import sys

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()

from neo4j import GraphDatabase
from decouple import config

driver = GraphDatabase.driver(
    config('MEMGRAPH_URI', 'bolt://localhost:7687'),
    auth=(config('MEMGRAPH_USERNAME', ''), config('MEMGRAPH_PASSWORD', ''))
)

with driver.session() as session:
    # Let's get the latest session
    result = session.run("MATCH (ts:TriageSession) RETURN ts.id AS id ORDER BY ts.created_at DESC LIMIT 1")
    latest_session = result.single()
    if not latest_session:
        print("No sessions found.")
        sys.exit(0)
        
    s_id = latest_session["id"]
    print(f"Checking session {s_id}")
    
    # Check what suggestions are attached
    result = session.run(
        """
        MATCH (ts:TriageSession {id: $s_id})
        OPTIONAL MATCH (ts)-[:PRODUCED]->(s:Suggestion)
        RETURN s
        """, s_id=s_id
    )
    
    suggestions = list(result)
    print(f"Found {len(suggestions)} suggestions relations.")
    for rec in suggestions:
        s = rec["s"]
        if s:
            print(f"- Suggestion: {s.get('id')}, accepted_bool: {s.get('accepted_bool')}")
        else:
            print("- No suggestion attached.")
            
    # Check if there are any suggestions globally
    result = session.run("MATCH (s:Suggestion) RETURN count(s) as c")
    print(f"Total suggestions in DB: {result.single()['c']}")
    
driver.close()
