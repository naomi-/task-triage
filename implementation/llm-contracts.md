# LLM_CONTRACTS.md — Structured outputs + validation

## Claude output MUST be valid JSON and conform to schema
No free-form prose in the payload.

## Top-level triage response schema (MVP)
{
  "triage_session_id": "uuid",
  "items": [
    {
      "raw_text": "string",
      "action_title": "string",
      "description": "string",
      "status": "INBOX|NEXT|IN_PROGRESS|WAITING|SOMEDAY|DONE|ARCHIVED",
      "priority": 1-5,
      "urgency": 1-5,
      "effort": "XS|S|M|L|XL",
      "para_bucket": "PROJECT|AREA|RESOURCE|ARCHIVE",
      "project_suggestions": [{"name":"string","outcome":"string"}],
      "area_suggestions": [{"name":"string"}],
      "needs_clarification": boolean,
      "clarifying_questions": ["string", ...],
      "duplicate_candidates": [{"task_id":"uuid","reason":"string"}],
      "next_action": "string"
    }
  ]
}

## Validation rules
- Reject if JSON invalid
- Reject if enums invalid or missing required fields
- `status` must be one of: INBOX | NEXT | IN_PROGRESS | WAITING | SOMEDAY | DONE | ARCHIVED
- `effort` must be one of: XS | S | M | L | XL
- `para_bucket` must be one of: PROJECT | AREA | RESOURCE | ARCHIVE
- `project_suggestions` must be an array (empty array if none); max 10 items
- `area_suggestions` must be an array (empty array if none); max 10 items
- Clamp priority/urgency into 1..5
- Enforce max lengths: action_title ≤ 200 chars, description ≤ 2000 chars
- `next_action` max length: 500 chars
- These length limits prevent prompt-injection content from persisting in the graph
