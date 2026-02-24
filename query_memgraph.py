import os
import sys

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()

from neo4j import GraphDatabase
from decouple import config
from core.dtos import TriageSessionNode, UserNode

driver = GraphDatabase.driver(
    config('MEMGRAPH_URI', 'bolt://localhost:7687'),
    auth=(config('MEMGRAPH_USERNAME', ''), config('MEMGRAPH_PASSWORD', ''))
)

with driver.session() as session:
    result = session.run("MATCH (ts:TriageSession) RETURN ts ORDER BY ts.created_at DESC LIMIT 5")
    sessions = list(result)
    
    print(f"Found {len(sessions)} recent TriageSession nodes.")
    for record in sessions:
        ts = record['ts']
        print(f"--- Session ID: {ts.get('id')} ---")
        print(f"Input: {ts.get('input_text')}")
        print(f"Model: {ts.get('model')}")
        print(f"Created At: {ts.get('created_at')}")
        print()
driver.close()
