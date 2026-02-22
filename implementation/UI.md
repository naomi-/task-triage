# UI.md — User Interface Specification (Cozy Triage)

## 1. Design goals

The UI should:
- Minimize cognitive load
- Support fast brain-dump capture
- Make triage review clear and safe (no accidental destructive actions)
- Emphasize “next actions” and clarity
- Feel calm, friendly, and non-judgmental

MVP aesthetic:
- Cozy / kawaii inspired
- Soft rounded cards
- Gentle color palette
- Clear typography
- Playful but minimal iconography

No heavy animations required for MVP.

---

## 2. Core screens (MVP)

### 2.1 Authentication
**Routes**
- `/login`
- `/signup`

**Fields**
- Email
- Password

**Behavior**
- Standard Django auth
- Redirect to Dashboard on success

---

### 2.2 Dashboard (Home)
**Route:** `/`

**Primary purpose**
Quick capture + view top priorities.

**Components**
- Quick add input (single-line)
- “Brain dump” button → opens multiline modal or navigates to Inbox
- “Triage Inbox” button (visible when INBOX has items)
- Top “Next Actions” list (priority + urgency sorted)
- Quick stats (optional):
  - Tasks in NEXT
  - Tasks WAITING
  - Active projects

**Interactions**
- Add task → immediately stored as `INBOX`
- Mark task complete inline

---

### 2.3 Inbox / Brain Dump
**Route:** `/inbox`

**Components**
- Multiline textarea for paste/typing
- “Add to Inbox” button
- Existing INBOX task list
- “Triage” button

**Behavior**
- Submitting multiline text creates:
  - one raw TriageSession
  - individual INBOX tasks (optional v1) OR kept as raw until triage (preferred)

**Recommendation**
Keep raw brain dump in TriageSession first, then create tasks only after triage approval.

---

### 2.4 Triage Review
**Route:** `/triage/<session_id>`

**Primary purpose**
Review AI suggestions before applying.

**Layout**
For each suggested item:
- Raw text (collapsed by default)
- Suggested action title
- Suggested next action
- Suggested status (NEXT / WAITING / SOMEDAY)
- Project suggestion (if any)
- Priority / urgency / effort
- Duplicate warning (if detected)

**Controls**
- Accept
- Edit → inline editable fields
- Reject

**Batch controls**
- Accept all
- Reject all

**Safety**
- No auto-apply in MVP
- Changes applied only after explicit user action

---

### 2.5 Task List
**Route:** `/tasks`

**Views (tabs or filters)**
- Next Actions
- Waiting
- Someday
- All active
- Completed

**Filters**
- By Area
- By Project
- By Effort (quick wins vs deep work)
- By KonMari signal (optional badge)

**Task card fields**
- Title
- Next action
- Project
- Priority badge
- Effort badge
- Status dropdown
- Complete checkbox

---

### 2.6 Projects
**Route:** `/projects`

**Components**
- Project list
- Project detail page:
  - Outcome
  - Tasks in project
  - Indicator if no NEXT action exists (GTD compliance)

---

## 3. Visual language (MVP theme)

### Colors
Soft neutral base + 1–2 accent colors.
Avoid high-saturation or harsh contrast.

### Shapes
- Rounded corners
- Card-based layout
- Generous spacing

### Icons
Simple line icons:
- Inbox
- Check
- Clock (waiting)
- Star (priority)
- Sparkle (joy signal)

---

## 4. Interaction patterns

### Low friction capture
- Quick add always visible on Dashboard
- Brain dump supports paste of large text blocks

### Progressive disclosure
- Advanced fields hidden by default
- Show details on expand

### Inline editing
- Tasks editable without leaving page

### Safe triage
- Suggestions are previewed, not auto-applied
- Duplicate detection shows warning, not merge

---

## 5. Accessibility (baseline)

- Keyboard navigable
- Sufficient color contrast for text
- Focus states visible
- Avoid color-only status indicators (use icons + labels)

---

## 6. Customization (Post-MVP design)

The UI will be **themeable** in the future.

### Planned theme system
User preference stored in:
`User.preferences_json.theme`

Themes will define:
- Color palette
- Font pairings
- Card radius / density
- Icon set (optional)
- Background texture (optional)

### Theme architecture recommendation
Use CSS variables:
