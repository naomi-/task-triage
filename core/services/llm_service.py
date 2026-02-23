"""
llm_service.py — Anthropic Claude utilities.

Responsible for:
- Sending brain-dump text to Claude with a structured prompt
- Parsing and validating the JSON response against the LLM contract schema
- Returning a validated TriageSuggestion dict (never raw LLM output)
"""

from __future__ import annotations

import json
import logging
from typing import Any

from anthropic import Anthropic
from decouple import config

logger = logging.getLogger(__name__)

# Initialize Anthropic client
_client = Anthropic(api_key=config("ANTHROPIC_API_KEY"))


# ─────────────────────────────────────────────────────────────────────────────
# Validation schema and helpers
# ─────────────────────────────────────────────────────────────────────────────

VALID_STATUSES = {"INBOX", "NEXT", "IN_PROGRESS", "WAITING", "SOMEDAY", "DONE", "ARCHIVED"}
VALID_EFFORTS = {"XS", "S", "M", "L", "XL"}
VALID_PARA_BUCKETS = {"PROJECT", "AREA", "RESOURCE", "ARCHIVE"}


def _validate_triage_response(data: dict) -> dict:
    """
    Validate triage response against LLM contract schema.
    Raises ValueError if validation fails.
    Returns cleaned/clamped data.
    """
    if not isinstance(data, dict):
        raise ValueError("Response must be a dict")

    if "items" not in data or not isinstance(data["items"], list):
        raise ValueError("Response must have 'items' array")

    cleaned_items = []
    for i, item in enumerate(data["items"]):
        if not isinstance(item, dict):
            raise ValueError(f"Item {i} must be a dict")

        # Required fields
        required = ["action_title", "description", "status", "priority", "urgency", "effort"]
        for field in required:
            if field not in item:
                raise ValueError(f"Item {i} missing required field: {field}")

        # Validate enums
        if item["status"] not in VALID_STATUSES:
            raise ValueError(f"Item {i}: invalid status '{item['status']}'")
        if item["effort"] not in VALID_EFFORTS:
            raise ValueError(f"Item {i}: invalid effort '{item['effort']}'")

        # Clamp priority/urgency to 1-5
        priority = int(item.get("priority", 3))
        urgency = int(item.get("urgency", 3))
        priority = max(1, min(5, priority))
        urgency = max(1, min(5, urgency))

        # Enforce max lengths
        action_title = str(item.get("action_title", ""))[:200]
        description = str(item.get("description", ""))[:2000]
        next_action = str(item.get("next_action", ""))[:500]

        cleaned_item = {
            "raw_text": item.get("raw_text", ""),
            "action_title": action_title,
            "description": description,
            "status": item["status"],
            "priority": priority,
            "urgency": urgency,
            "effort": item["effort"],
            "para_bucket": item.get("para_bucket", "ARCHIVE"),
            "project_suggestions": item.get("project_suggestions", [])[:10],
            "area_suggestions": item.get("area_suggestions", [])[:10],
            "needs_clarification": bool(item.get("needs_clarification", False)),
            "clarifying_questions": item.get("clarifying_questions", []),
            "duplicate_candidates": item.get("duplicate_candidates", []),
            "next_action": next_action,
        }
        cleaned_items.append(cleaned_item)

    return {"items": cleaned_items}


def triage_brain_dump(text: str, context: dict | None = None) -> dict:
    """
    Send brain dump to Claude for triage.
    Returns validated triage response with items array.

    Args:
        text: Brain dump text from user
        context: Optional dict with user context (projects, areas, recent decisions)

    Returns:
        {"items": [...]} with validated triage suggestions

    Raises:
        ValueError: If response validation fails
        Exception: If Claude call fails
    """
    if not text or not text.strip():
        raise ValueError("Brain dump text cannot be empty")

    context_str = ""
    if context:
        context_str = f"""
## User Context
- Recent projects: {context.get('recent_projects', [])}
- Active areas: {context.get('active_areas', [])}
- Recent decisions: {context.get('recent_decisions', [])}
"""

    system_prompt = """You are a task triage assistant for Cozy Triage, a personal task management system inspired by GTD, PARA, and Second Brain methodologies.

Your job is to parse a brain dump (unstructured thoughts, tasks, ideas) and convert it into structured, actionable items.

For each item in the brain dump:
1. Extract the core action/task
2. Suggest a status (INBOX for new items, NEXT for immediate actions)
3. Estimate priority (1-5) and urgency (1-5)
4. Estimate effort (XS/S/M/L/XL)
5. Suggest which project or area it belongs to
6. Flag if clarification is needed
7. Suggest related projects/areas to create if needed

Return ONLY valid JSON matching the schema. No prose, no markdown, no explanations."""

    user_prompt = f"""Please triage this brain dump:

{text}
{context_str}

Return a JSON object with this structure:
{{
  "items": [
    {{
      "raw_text": "original text snippet",
      "action_title": "concise title (≤200 chars)",
      "description": "fuller context (≤2000 chars)",
      "status": "INBOX|NEXT|IN_PROGRESS|WAITING|SOMEDAY|DONE|ARCHIVED",
      "priority": 1-5,
      "urgency": 1-5,
      "effort": "XS|S|M|L|XL",
      "para_bucket": "PROJECT|AREA|RESOURCE|ARCHIVE",
      "project_suggestions": [{{"name":"string","outcome":"string"}}],
      "area_suggestions": [{{"name":"string"}}],
      "needs_clarification": boolean,
      "clarifying_questions": ["string"],
      "duplicate_candidates": [{{"task_id":"uuid","reason":"string"}}],
      "next_action": "specific next step (≤500 chars)"
    }}
  ]
}}"""

    # Try up to 2 times (initial + 1 retry)
    for attempt in range(2):
        try:
            response = _client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=4096,
                messages=[
                    {"role": "user", "content": user_prompt}
                ],
                system=system_prompt,
            )

            # Extract JSON from response
            response_text = response.content[0].text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            elif response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            data = json.loads(response_text)

            # Validate and clean
            validated = _validate_triage_response(data)
            logger.info(f"Triage succeeded: {len(validated['items'])} items")
            return validated

        except json.JSONDecodeError as e:
            if attempt == 0:
                logger.warning(f"Attempt {attempt + 1}: JSON decode error, retrying: {e}")
                continue
            else:
                raise ValueError(f"Claude returned invalid JSON after 2 attempts: {e}")
        except ValueError as e:
            if attempt == 0:
                logger.warning(f"Attempt {attempt + 1}: Validation error, retrying: {e}")
                continue
            else:
                raise ValueError(f"Triage response validation failed after 2 attempts: {e}")
        except Exception as e:
            logger.exception(f"Attempt {attempt + 1}: Unexpected error in triage")
            raise

