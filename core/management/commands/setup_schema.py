"""
setup_schema.py — Django management command to deploy the Memgraph schema.

Safe to run multiple times (idempotent).  All statements use IF NOT EXISTS or
are wrapped in a try/except for duplicate-object errors from Memgraph.

Usage:
    python manage.py setup_schema
"""

from django.core.management.base import BaseCommand

from core.services import graphrag_service


# ---------------------------------------------------------------------------
# Uniqueness constraints — one per node type on `id`
# ---------------------------------------------------------------------------
CONSTRAINTS = [
    "CREATE CONSTRAINT ON (n:User)          ASSERT n.id IS UNIQUE;",
    "CREATE CONSTRAINT ON (n:Task)          ASSERT n.id IS UNIQUE;",
    "CREATE CONSTRAINT ON (n:Project)       ASSERT n.id IS UNIQUE;",
    "CREATE CONSTRAINT ON (n:Area)          ASSERT n.id IS UNIQUE;",
    "CREATE CONSTRAINT ON (n:Resource)      ASSERT n.id IS UNIQUE;",
    "CREATE CONSTRAINT ON (n:TriageSession) ASSERT n.id IS UNIQUE;",
    "CREATE CONSTRAINT ON (n:Suggestion)    ASSERT n.id IS UNIQUE;",
]

# ---------------------------------------------------------------------------
# Vector index — Task(embedding), 1024 dims, cosine similarity
# ---------------------------------------------------------------------------
VECTOR_INDEXES = [
    (
        "task_embedding_idx",
        """
        CREATE VECTOR INDEX task_embedding_idx
        ON :Task(embedding)
        WITH CONFIG {
          "dimension": 1024,
          "capacity": 10000,
          "metric": "cos"
        };
        """,
    ),
]


class Command(BaseCommand):
    help = (
        "Deploy Memgraph schema: uniqueness constraints on all node id fields "
        "and a cosine vector index on Task(embedding). Safe to run repeatedly."
    )

    def handle(self, *args, **options) -> None:
        driver = graphrag_service._get_driver()

        try:
            with driver.session() as session:
                # ── Constraints ─────────────────────────────────────────────
                self.stdout.write("Applying uniqueness constraints …")
                for cypher in CONSTRAINTS:
                    label = cypher.split("(n:")[1].split(")")[0].strip()
                    try:
                        session.run(cypher)
                        self.stdout.write(f"  ✓  {label}.id IS UNIQUE")
                    except Exception as exc:
                        # Memgraph raises if the constraint already exists
                        msg = str(exc).lower()
                        if "already exists" in msg or "already have" in msg:
                            self.stdout.write(
                                self.style.WARNING(f"  ↩  {label} constraint already exists, skipping")
                            )
                        else:
                            raise

                # ── Vector index ─────────────────────────────────────────────
                self.stdout.write("Applying vector indexes …")
                for index_name, cypher in VECTOR_INDEXES:
                    try:
                        session.run(cypher)
                        self.stdout.write(f"  ✓  {index_name} created")
                    except Exception as exc:
                        msg = str(exc).lower()
                        if "already exists" in msg or "already have" in msg:
                            self.stdout.write(
                                self.style.WARNING(f"  ↩  {index_name} already exists, skipping")
                            )
                        else:
                            raise

        finally:
            driver.close()

        self.stdout.write(self.style.SUCCESS("\nSchema setup complete."))

