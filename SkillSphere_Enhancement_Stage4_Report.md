# SkillSphere Enhancement — Stage 4 Report: Support Ticket System, Ticket Lifecycle & Secure APIs

**Date:** November 23, 2026  
**Branch:** `feature/skillsphere-assistant-enhancements`  
**Base Commit:** `5abb1a6`  
**Status:** COMPLETED & VERIFIED — READY FOR REVIEW  

---

## 1. Executive Summary

In Stage 4, the **Support Ticket System, Ticket Lifecycle & Secure APIs** have been designed, implemented, and rigorously verified. This provides SkillSphere with a production-grade, secure customer support ticketing backbone that seamlessly connects user inquiries and troubleshooting escalations to backend support administrators.

All architectural and security constraints established in Stage 0 and reiterated in user directives were strictly adhered to:
1. **Concurrency-Safe Ticket Numbering:** Sequential format `TICK-YYYY-XXXX` generated via a dedicated database sequence table (`ticket_sequences`) with unique constraints, pessimistic row-locking (`FOR UPDATE`) on PostgreSQL, and thread locking for workers.
2. **Server-Derived Identity & Strict IDOR Defense:** `user_id` and `user_role` are derived exclusively from the verified JWT backend session. Request payload spoofing is completely ignored. Inaccessible cross-user tickets return `404 Not Found` to prevent ticket enumeration attacks.
3. **Internal Note & Audit Trail Privacy:** Internal administrator investigation notes (`is_internal=True`) and audit trails are completely isolated from candidates and recruiters at both query and serialization levels.
4. **Deterministic Lifecycle State Machine:** Status transitions (`OPEN` $\to$ `IN_PROGRESS` $\to$ `WAITING_USER` $\to$ `RESOLVED` $\to$ `CLOSED`) are validated server-side. User replies automatically transition `WAITING_USER` $\to$ `IN_PROGRESS`, and replies to `CLOSED` tickets are blocked.
5. **Zero Startup Migrations:** Migrations are never executed automatically on app startup. An explicit, reviewable migration script (`backend/app/db/migrate_support_tickets.py`) was created and verified against an isolated disposable database.
6. **100% Backward Compatibility:** All existing chatbot APIs and 30 foundational FAQs remain untouched and fully passing across all test suites (90/90 tests passing).

---

## 2. Database Models & Schema Design

Four new relational models were added to `backend/app/models/models.py` using SQLAlchemy:

### A. `TicketSequence`
- **Table:** `ticket_sequences`
- **Fields:**
  - `id`: Integer primary key
  - `year`: Integer (unique index)
  - `last_number`: Integer (atomic counter)
- **Purpose:** Database-backed sequence tracker guaranteeing sequential, collision-free numbers even across concurrent multi-worker environments.

### B. `SupportTicket`
- **Table:** `support_tickets`
- **Fields:**
  - `id`: Integer primary key
  - `ticket_number`: String (unique index, formatted as `TICK-YYYY-XXXX`)
  - `user_id`: Integer foreign key (`users.id`, indexed)
  - `user_role`: Enum (`RoleEnum`)
  - `subject`: String(255)
  - `description`: Text
  - `category`: Enum (`TicketCategoryEnum`: `RESUME_OCR`, `LIVEKIT_VIDEO`, `PROCTORING_MCQ`, `ACCOUNT_AUTH`, `GENERAL`)
  - `priority`: Enum (`TicketPriorityEnum`: `LOW`, `MEDIUM`, `HIGH`, `URGENT`, default `MEDIUM`)
  - `status`: Enum (`TicketStatusEnum`: `OPEN`, `IN_PROGRESS`, `WAITING_USER`, `RESOLVED`, `CLOSED`, default `OPEN`)
  - `assigned_admin_id`: Integer foreign key (`users.id`, nullable, indexed)
  - `created_at`: DateTime (UTC, indexed)
  - `updated_at`: DateTime (UTC)
- **Relationships:**
  - `user`: Many-to-One to `User`
  - `assigned_admin`: Many-to-One to `User`
  - `messages`: One-to-Many to `TicketMessage` (cascade="all, delete-orphan", order_by="asc(TicketMessage.created_at)")
  - `audit_logs`: One-to-Many to `TicketAuditLog` (cascade="all, delete-orphan", order_by="asc(TicketAuditLog.created_at)")

### C. `TicketMessage`
- **Table:** `ticket_messages`
- **Fields:**
  - `id`: Integer primary key
  - `ticket_id`: Integer foreign key (`support_tickets.id`, indexed)
  - `sender_id`: Integer foreign key (`users.id`, indexed)
  - `sender_role`: Enum (`RoleEnum`)
  - `message`: Text
  - `is_internal`: Boolean (default `False`, indexed)
  - `created_at`: DateTime (UTC, indexed)
- **Purpose:** Threaded ticket communication. `is_internal=True` marks administrative internal investigation notes hidden from regular users.

### D. `TicketAuditLog`
- **Table:** `ticket_audit_logs`
- **Fields:**
  - `id`: Integer primary key
  - `ticket_id`: Integer foreign key (`support_tickets.id`, indexed)
  - `actor_id`: Integer foreign key (`users.id`, indexed)
  - `action`: String(64) (`CREATED`, `STATUS_CHANGED`, `ASSIGNED`, `MESSAGE_ADDED`, `INTERNAL_NOTE_ADDED`)
  - `old_status`: Enum (`TicketStatusEnum`, nullable)
  - `new_status`: Enum (`TicketStatusEnum`, nullable)
  - `details`: JSON (structured contextual metadata)
  - `created_at`: DateTime (UTC, indexed)
- **Purpose:** Complete tamper-evident audit history of ticket lifecycle changes and administrative actions.

---

## 3. Ticket Lifecycle State Machine

Status transitions are strictly validated by `ticket_service.py` via `VALID_STATUS_TRANSITIONS`:

| Current Status | Allowed Target Statuses | Notes |
| :--- | :--- | :--- |
| `OPEN` | `IN_PROGRESS`, `WAITING_USER`, `RESOLVED`, `CLOSED` | Initial state upon creation. |
| `IN_PROGRESS` | `WAITING_USER`, `RESOLVED`, `CLOSED` | Admin actively triaging or working. |
| `WAITING_USER` | `IN_PROGRESS`, `RESOLVED`, `CLOSED` | Admin awaiting candidate/recruiter input. |
| `RESOLVED` | `OPEN`, `IN_PROGRESS`, `CLOSED` | Issue addressed; can be reopened or finalized. |
| `CLOSED` | `OPEN` | Final terminal state. Reopening transitions to `OPEN`. |

### Automated State Dynamics
1. **User Reply Auto-Transition:** When a ticket is in `WAITING_USER` and the candidate/recruiter replies with additional details, the service layer automatically transitions the ticket status to `IN_PROGRESS` and records a status audit log.
2. **Closed Ticket Guard:** Any attempt by a user to reply to a ticket in `CLOSED` status is rejected with `400 Bad Request` ("Cannot post messages to a closed ticket. Please reopen the ticket or create a new one.").
3. **Admin Assignment Tracking:** Assigning an admin updates `assigned_admin_id` and appends an `ASSIGNED` audit log entry with actor ID and assigned target ID.

---

## 4. Security & Role Isolation

### A. IDOR Defense (Insecure Direct Object Reference)
- In `ticket_service.get_ticket_for_user`:
  ```python
  ticket = db.query(SupportTicket).filter(
      SupportTicket.id == ticket_id,
      SupportTicket.user_id == current_user.id
  ).first()
  if not ticket:
      raise HTTPException(
          status_code=status.HTTP_404_NOT_FOUND,
          detail="Support ticket not found"
      )
  ```
- Returning `404 Not Found` (rather than `403 Forbidden`) ensures an attacker cannot probe ticket IDs to deduce whether tickets exist for other users.
- `GET /api/v1/tickets` strictly filters by `SupportTicket.user_id == current_user.id`.

### B. Internal Note Privacy
- Messages with `is_internal=True` are visible **only** to users with `RoleEnum.ADMIN`.
- In `ticket_service.serialize_ticket_detail`:
  ```python
  if msg.is_internal and not is_admin:
      continue
  ```
- Non-admin responses completely exclude `audit_logs` and internal messages from response payloads.

### C. Role Authorization & Route Separation
- Regular users (`JOB_SEEKER`, `RECRUITER`) access `/api/v1/tickets`.
- Administrators access `/api/v1/admin/tickets` with dependency `current_user: User = Depends(require_role(RoleEnum.ADMIN))`.

---

## 5. API Endpoints Specification

### User Endpoints (`/api/v1/tickets`)
- `POST /api/v1/tickets`: Create a new ticket (validates subject, description, category, priority).
- `GET /api/v1/tickets`: List current user's tickets (paginated, sorted by `created_at` descending).
- `GET /api/v1/tickets/{ticket_id}`: Retrieve detailed ticket view including user-visible message thread.
- `POST /api/v1/tickets/{ticket_id}/messages`: Post a user reply to an existing open ticket.

### Admin Endpoints (`/api/v1/admin/tickets`)
- `GET /api/v1/admin/tickets`: List all platform tickets with filtering by status, category, priority, and user ID.
- `GET /api/v1/admin/tickets/{ticket_id}`: Retrieve full ticket details including all internal notes and audit logs.
- `PUT /api/v1/admin/tickets/{ticket_id}/status`: Transition ticket status across validated state machine.
- `PUT /api/v1/admin/tickets/{ticket_id}/assign`: Assign ticket to an active administrator.
- `POST /api/v1/admin/tickets/{ticket_id}/messages`: Post a response to the ticket (public reply or internal note with `is_internal=True`).

Both routers are registered in `backend/app/main.py`.

---

## 6. Migration Procedure & Verification

An explicit migration script was implemented at `backend/app/db/migrate_support_tickets.py`:
- Contains table definitions and execution routine `run_migration(database_url)`.
- Does **not** run on application startup (respecting the architectural constraint).
- Tested and verified in `test_explicit_migration_script` against a disposable test database (`sqlite:///{tmp_path}/disposable_test.db`).

---

## 7. Verification & Test Results

A comprehensive test suite was implemented in `backend/tests/test_support_ticket_system.py` covering 12 target test cases:

1. `test_ticket_creation_and_attributes`: Ticket creation, sequence numbering, initial message, and CREATED audit log.
2. `test_concurrency_safe_ticket_number_sequence`: Sequential format `TICK-2026-0001`, `0002`, `0003`.
3. `test_multithreaded_concurrent_ticket_numbers`: 10 simultaneous worker threads verifying thread safety and unique ticket generation.
4. `test_user_ticket_listing_isolation`: Candidate A cannot view Candidate B's tickets in ticket listings.
5. `test_cross_user_idor_blocked_with_404`: Candidate A cannot view or reply to Candidate B's ticket (returns 404).
6. `test_recruiter_can_create_and_manage_tickets`: Recruiters have full user-level ticket capabilities.
7. `test_internal_notes_never_leaked_to_user`: `is_internal=True` notes are completely stripped from user responses.
8. `test_valid_status_transitions`: Full lifecycle traversal (`OPEN` $\to$ `IN_PROGRESS` $\to$ `WAITING_USER` $\to$ `IN_PROGRESS` via user reply $\to$ `RESOLVED` $\to$ `CLOSED`).
9. `test_invalid_status_transition_rejected_with_400`: Forbidden transitions (e.g. `CLOSED` $\to$ `RESOLVED`) are rejected with 400.
10. `test_cannot_reply_to_closed_ticket`: Replies to `CLOSED` tickets are rejected with 400.
11. `test_admin_ticket_assignment`: Assigning an admin updates the ticket and records an `ASSIGNED` audit log.
12. `test_explicit_migration_script`: Clean table creation via explicit migration runner.

### Full Test Suite Execution
```bash
$env:PYTHONPATH='backend'; python -m pytest backend/tests/test_multilingual_engine.py backend/tests/test_chatbot_isolated_suite.py backend/tests/test_chatbot_foundation.py backend/tests/test_intent_and_kb_expansion.py backend/tests/test_smart_troubleshooting_and_llm.py backend/tests/test_support_ticket_system.py -v
```

**Results:**
- `test_multilingual_engine.py`: 20/20 PASSED
- `test_chatbot_isolated_suite.py`: 13/13 PASSED
- `test_chatbot_foundation.py`: 12/12 PASSED
- `test_intent_and_kb_expansion.py`: 21/21 PASSED
- `test_smart_troubleshooting_and_llm.py`: 12/12 PASSED
- `test_support_ticket_system.py`: 12/12 PASSED
- **Total: 90 passed, 0 failed (100% pass rate in 8.61s)**

---

## 8. Git Working Tree & Safety Verification

- Branch: `feature/skillsphere-assistant-enhancements`
- Commits made to `main`: **0**
- Commits made to `feature/skillsphere-assistant`: **0**
- Production database modified: **NO**
- Render deployed: **NO**

---

## 9. Conclusion & Stage 5 Readiness

Stage 4 is fully completed, verified, and adheres to all architectural, functional, and security requirements. 

We are ready to proceed to **Stage 5: Admin Support Dashboard & Analytics**, which will build upon these secure APIs to provide the frontend administrative dashboard for ticket triage, status updates, team assignments, and support SLA analytics.

*Awaiting your review and approval before proceeding.*
