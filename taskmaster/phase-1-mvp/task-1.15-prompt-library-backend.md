# Task 1.15: Prompt Library — Database, Auth & Backend API

## Vision
A curated prompt library backend that stores 35 pre-built BRM/DBA prompts in SQLite, provides a RESTful API for browsing/searching/executing/favoriting prompts, and gates access behind a hardcoded admin login.

**Estimated Time:** 17.5 hours (Days 1–3)
**Dependencies:** Task 1.14 (Web Dashboard MVP) must be complete
**Risk Level:** Medium — introduces auth middleware and a new API surface

---

## 🎯 Scope

### ✅ IN SCOPE
| Feature | Priority |
|---------|----------|
| SQLite storage for prompts, favorites, history | P0 |
| 35 seeded prompts (15 BRM + 20 DBA) | P0 |
| 9 prompt categories | P0 |
| Pydantic models for all prompt entities | P0 |
| Hardcoded admin auth middleware (Basic Auth) | P0 |
| CRUD read endpoints (`GET /api/prompts`) | P0 |
| Favorites toggle endpoint | P0 |
| Prompt execution via SSE (reuses ChatService) | P0 |
| Admin CRUD endpoints (create/update/soft-delete) | P1 |
| Deprecation of `/api/chat/templates` | P1 |

### ❌ OUT OF SCOPE
- OAuth / JWT / multi-user auth
- Role-based access control (RBAC)
- Prompt scheduling / recurring execution
- Redis caching layer

---

## 📁 Files Created / Modified

```
[NEW]    src/api/models/prompt.py           # Pydantic models
[NEW]    src/api/routes/prompts.py          # FastAPI router
[NEW]    src/api/services/prompt_service.py  # SQLite logic + seed
[NEW]    src/api/middleware/auth.py          # Basic auth dependency
[MODIFY] src/api/main.py                    # Register prompts router
[MODIFY] src/api/models/__init__.py         # Re-export new models
[MODIFY] src/api/routes/chat.py             # Deprecate /templates
[MODIFY] .env                               # ADMIN_USER, ADMIN_PASSWORD
```

---

## 📋 Sub-Tasks Breakdown

### 1.15.1 Pydantic Models (1.5h)

**File:** `src/api/models/prompt.py`

Create all Pydantic models:
- [ ] `Prompt` — full prompt representation
- [ ] `PromptSummary` — lightweight list item
- [ ] `PromptCategory` — category with count
- [ ] `PromptListResponse` — paginated list
- [ ] `PromptExecuteRequest` — `{parameters: {}}`
- [ ] `PromptFavorite` — favorite record
- [ ] `PromptHistoryEntry` — execution log
- [ ] `PromptCreate` / `PromptUpdate` — admin mutations
- [ ] Update `src/api/models/__init__.py` with re-exports

**Acceptance:**
- `from src.api.models.prompt import Prompt` imports without error
- All models validate with sample data

---

### 1.15.2 SQLite Schema + PromptService (2h)

**File:** `src/api/services/prompt_service.py`

Create `PromptService` class following the `SessionService` pattern:
- [ ] `__init__(self, db_path="data/prompts.db")` — creates DB file
- [ ] `_init_db()` — creates 4 tables:
  - `prompt_library` (id, category, title, description, prompt_template, parameters, default_values, expected_output, tags, difficulty_level, estimated_runtime, requires_approval, is_active, usage_count, average_runtime, created_at, updated_at)
  - `prompt_categories` (id, name, display_name, description, icon, sort_order, parent_category_id)
  - `user_prompt_favorites` (id, user_id, prompt_id, added_at, FK→prompt_library)
  - `prompt_execution_history` (id, user_id, prompt_id, parameters_used, executed_at, execution_time_ms, status, result_summary, FK→prompt_library)
- [ ] Indexes on `category`, `tags`, `user_id`, `executed_at`

**Acceptance:**
- `PromptService()` creates `data/prompts.db` with 4 tables
- Schema matches spec exactly
- Foreign keys enforce referential integrity

---

### 1.15.3 Seed 35 Prompts + 9 Categories (2h)

**File:** `src/api/services/prompt_service.py` (add `_seed_prompts()` + `_seed_categories()`)

- [ ] 15 BRM prompts (Revenue, Customer, Payment, Operations)
- [ ] 20 DBA prompts (Health, Performance, Capacity, Locks, Backup, Config)
- [ ] 9 categories with icons, display names, and sort order
- [ ] Use `INSERT OR IGNORE` for idempotent seeding
- [ ] Called automatically from `_init_db()`

**Acceptance:**
- `SELECT COUNT(*) FROM prompt_library` → 35
- `SELECT COUNT(*) FROM prompt_categories` → 9
- Re-running `_init_db()` does not duplicate rows

---

### 1.15.4 Auth Middleware (1.5h)

**File:** `src/api/middleware/auth.py`

- [ ] `verify_admin` FastAPI dependency — checks `Authorization: Basic <base64>` header
- [ ] Loads credentials from env: `ADMIN_USER` (default: `admin`), `ADMIN_PASSWORD` (default: `odaos2024`)
- [ ] Returns `HTTPException(401)` if missing/wrong
- [ ] `POST /api/auth/login` endpoint — validates credentials, returns `{authenticated: true, token: <base64>}`
- [ ] Add `ADMIN_USER` and `ADMIN_PASSWORD` to `.env` and `.env.example`

**Acceptance:**
- `GET /api/prompts` without header → 401
- `GET /api/prompts` with correct Basic header → 200
- `POST /api/auth/login` with wrong password → 401
- Existing `/api/chat`, `/api/sessions`, `/api/viz` remain open (no auth required)

⚠️ **RISK:** Must NOT break existing open endpoints. Auth only applies to `/api/prompts` and `/api/auth/login`.

---

### 1.15.5 Read API Endpoints (2h)

**Files:** `src/api/routes/prompts.py`, `src/api/services/prompt_service.py`, `src/api/main.py`

- [ ] `GET /api/prompts` — list all active prompts (optional `?category=`, `?search=`, `?tag=`, `?difficulty=`)
- [ ] `GET /api/prompts/categories` — list categories with prompt counts
- [ ] `GET /api/prompts/{prompt_id}` — single prompt with full details
- [ ] `GET /api/prompts/favorites` — user's favorites
- [ ] `GET /api/prompts/history` — execution history (paginated, `?limit=`, `?offset=`)
- [ ] Register router in `main.py`: `app.include_router(prompts.router, prefix="/api/prompts", tags=["Prompts"])`
- [ ] Implement corresponding service methods

**Acceptance:**
- `GET /api/prompts` → 35 prompts
- `GET /api/prompts?category=BRM_BUSINESS` → filtered subset
- `GET /api/prompts?search=revenue` → matching prompts
- `GET /api/prompts/categories` → 9 categories with counts
- Swagger docs show all endpoints

---

### 1.15.6 Favorites Toggle (1h)

**Files:** `src/api/routes/prompts.py`, `src/api/services/prompt_service.py`

- [ ] `POST /api/prompts/{prompt_id}/favorite` — toggle for hardcoded user `"admin"`
- [ ] Service: insert if not exists, delete if exists
- [ ] Return `{favorited: true/false}`

**Acceptance:**
- First POST → `{favorited: true}`; `GET /favorites` includes it
- Second POST → `{favorited: false}`; `GET /favorites` excludes it

---

### 1.15.7 Prompt Execution Endpoint (3h)

**Files:** `src/api/routes/prompts.py`, `src/api/services/prompt_service.py`

- [ ] `POST /api/prompts/{prompt_id}/execute` — body: `{parameters: {...}}`
- [ ] Fetch prompt template from DB
- [ ] Validate parameters against schema (type checking, required fields)
- [ ] Merge with defaults, replace `{placeholders}` in template
- [ ] Stream final query through `ChatService.stream_response()` via SSE
- [ ] Log to `prompt_execution_history` (user_id, prompt_id, params, time, status)
- [ ] Increment `usage_count` on `prompt_library`

**Acceptance:**
- Executing `brm-revenue-001` streams response via SSE
- `prompt_execution_history` has new row with correct data
- `usage_count` incremented by 1
- Invalid parameters return 422

⚠️ **RISK:** Integration point with existing orchestrator. Must reuse `ChatService`, not duplicate.

---

### 1.15.8 Deprecate `/api/chat/templates` (0.5h)

**File:** `src/api/routes/chat.py`

- [ ] Replace hardcoded `get_query_templates()` body with proxy to `PromptService.list_prompts(limit=12)`
- [ ] Add `Deprecation: true` and `Link: </api/prompts>` response headers

**Acceptance:**
- `GET /api/chat/templates` still returns data (from prompt_library table now)
- Response includes deprecation headers
- No frontend breakage

---

### 1.15.9 Admin CRUD Endpoints (2h)

**Files:** `src/api/routes/prompts.py`, `src/api/services/prompt_service.py`

- [ ] `POST /api/prompts/admin` — create prompt (protected by `verify_admin`)
- [ ] `PUT /api/prompts/admin/{prompt_id}` — update prompt
- [ ] `DELETE /api/prompts/admin/{prompt_id}` — soft delete (`is_active = false`)
- [ ] Validate prompt_template placeholders match parameter names

**Acceptance:**
- Full CRUD cycle: create → read → update → delete
- Deleted prompt no longer appears in `GET /api/prompts`
- Unauthenticated requests → 401

---

## ✅ Phase 1.15 Success Criteria

| Metric | Target |
|--------|--------|
| All endpoints return correct status codes | 100% |
| Swagger docs generated for all new endpoints | ✅ |
| 35 prompts seeded on first run | ✅ |
| Auth gate blocks unauthenticated users | ✅ |
| Existing endpoints unaffected | ✅ |
| `data/prompts.db` created automatically | ✅ |
