import re
import os

filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "core", "services", "graphrag_service.py")

with open(filepath, "r") as f:
    content = f.read()

# Replace _get_driver definition
old_driver_def = """def _get_driver() -> Driver:
    \"\"\"Return a connected Neo4j/Bolt driver for Memgraph.\"\"\"
    return GraphDatabase.driver(
        settings.MEMGRAPH_URI,
        auth=(settings.MEMGRAPH_USERNAME, settings.MEMGRAPH_PASSWORD),
    )"""

new_driver_def = """_driver_instance = None

def _get_driver() -> Driver:
    \"\"\"Return a connected Neo4j/Bolt driver for Memgraph.\"\"\"
    global _driver_instance
    if _driver_instance is None:
        _driver_instance = GraphDatabase.driver(
            settings.MEMGRAPH_URI,
            auth=(settings.MEMGRAPH_USERNAME, settings.MEMGRAPH_PASSWORD),
            max_connection_lifetime=300, # 5 min
            max_connection_pool_size=50,
            connection_acquisition_timeout=30.0
        )
    return _driver_instance"""

content = content.replace(old_driver_def, new_driver_def)

# Remove all `driver.close()` lines, taking care of indentation
content = re.sub(r"^[ \t]*driver\.close\(\)\n?", "", content, flags=re.MULTILINE)

with open(filepath, "w") as f:
    f.write(content)

print(f"Successfully refactored {filepath}")
