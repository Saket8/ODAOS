# Task 1.17: Prompt Library — Integration, Polish & Verification

## Vision
Wire everything together, polish the UI to premium standards, add cross-feature navigation, implement error handling, and run a full verification suite to ensure the Prompt Library works end-to-end without regressions.

**Estimated Time:** 13 hours (Days 7–8)
**Dependencies:** Task 1.15 (Backend) + Task 1.16 (Frontend) must be complete
**Risk Level:** Low — mostly glue code, styling, and testing

---

## 🎯 Scope

### ✅ IN SCOPE
| Feature | Priority |
|---------|----------|
| Pytest unit tests for PromptService | P0 |
| SSE execution pipeline validation | P0 |
| Premium styling & animations | P0 |
| Cross-feature navigation (chat ↔ prompt library) | P0 |
| Error handling & loading states | P0 |
| Backend API manual test suite | P0 |
| Frontend E2E walkthrough | P0 |
| Regression check on existing features | P0 |
| README update with prompt library docs | P1 |

---

## 📁 Files Created / Modified

```
[NEW]    tests/test_prompt_service.py            # Pytest unit tests
[MODIFY] src/api/routes/prompts.py               # SSE validation fixes
[MODIFY] src/api/services/prompt_service.py       # Edge case handling
[MODIFY] frontend/src/index.css                   # Prompt library styles
[MODIFY] frontend/src/components/PromptLibrary/*  # Polish all components
[MODIFY] frontend/src/components/Chat/ChatContainer.tsx  # Cross-nav link
[MODIFY] frontend/src/stores/promptStore.ts       # Error handling
[MODIFY] README.md                                # Prompt library setup docs
```

---

## 📋 Sub-Tasks Breakdown

### 1.17.0 Pytest Unit Tests for PromptService (2h)

**File:** `tests/test_prompt_service.py`

- [ ] Test `_init_db()` creates all 4 tables with correct columns
- [ ] Test `_seed_prompts()` inserts 35 prompts idempotently
- [ ] Test `_seed_categories()` inserts 9 categories idempotently
- [ ] Test `list_prompts()` returns all active prompts
- [ ] Test `list_prompts(category=...)` filters correctly
- [ ] Test `list_prompts(search=...)` matches title/description/tags
- [ ] Test `get_prompt(id)` returns full prompt details
- [ ] Test `toggle_favorite()` adds and removes
- [ ] Test `log_execution()` creates history record
- [ ] Test `list_history()` returns paginated results
- [ ] Use temporary SQLite DB (`tmp` dir) for isolation
- [ ] Target: 60%+ coverage of `prompt_service.py`

**Acceptance:**
- `pytest tests/test_prompt_service.py` passes all tests
- No test depends on external services (Oracle, LLM)

---

### 1.17.1 Wire Prompt Execution SSE Pipeline (2h)

**Files:** `prompts.py`, `prompt_service.py`

Validate and fix the end-to-end execution flow:
- [ ] Prompt template → parameter replacement → `ChatService.stream_response()`
- [ ] SSE events match existing chat stream format: `token`, `chart`, `suggestions`, `done`, `error`
- [ ] Frontend `promptStore.executePrompt()` handles all event types correctly
- [ ] Execution time tracked accurately (start→done)
- [ ] History logging captures result summary (first 500 chars of response)

**Acceptance:**
- Execute "Monthly Revenue Trend" → streams identical to typing same query in chat
- Execution history shows correct time + status
- Error in orchestrator → SSE sends `error` event → UI shows error state

---

### 1.17.2 Premium Styling & Animations (2h)

**Files:** `index.css`, all PromptLibrary components

- [ ] Card hover: subtle scale(1.01) + border glow (`var(--accent-primary)` at 20% opacity)
- [ ] Staggered card entry with `framer-motion` (50ms delay between cards)
- [ ] Modal: backdrop blur + slide-up entrance + fade-out exit
- [ ] Category sidebar: smooth active indicator transition
- [ ] Tags: subtle background with rounded pills, hover color shift
- [ ] Difficulty badges: green (beginner), amber (intermediate), red (advanced) with icon
- [ ] Search bar: focus ring animation
- [ ] Dark/light mode: all new components use CSS variables (no hardcoded colors)
- [ ] Skeleton loading: shimmer effect matching existing `skeleton-loading` class

**Acceptance:**
- UI feels premium and consistent with existing chat pages
- Dark mode → all components readable, no white flashes
- Light mode → all components readable, proper contrast
- No janky animations or layout shifts

---

### 1.17.3 Cross-Feature Navigation (1h)

**Files:** `ChatContainer.tsx`, `ExecutionResultView.tsx`

- [ ] Chat welcome screen: add "📚 Explore Prompt Library →" button below suggestion cards
- [ ] Clicking navigates to `/prompt-library`
- [ ] Execution result → "Chat about this" button → navigates to `/` and pre-fills the prompt query
- [ ] Quick replies in chat: add "Prompt Library" category option

**Acceptance:**
- Welcome screen shows library link
- Clicking library link navigates correctly
- "Chat about this" from execution results works

---

### 1.17.4 Error Handling & Loading States (1.5h)

**Files:** All PromptLibrary components, `promptStore.ts`

- [ ] API failure → toast/banner notification with error message + retry button
- [ ] Offline detection → "Unable to connect" banner
- [ ] Loading states:
  - Prompts loading → skeleton grid (4 cards)
  - Categories loading → skeleton sidebar
  - Execution loading → pulsing progress indicator
  - History loading → skeleton rows
- [ ] Empty states:
  - No search results → "No prompts match your search" + clear button
  - No favorites → "Star a prompt to add it to favorites"
  - No history → "Execute your first prompt to see history"
- [ ] Timeout handling: execution > 30s → show warning

**Acceptance:**
- Kill backend → UI shows error state, not blank page
- Search for gibberish → empty state with reset button
- All loading states display before data arrives

---

### 1.17.5 Backend API Manual Test Suite (1.5h)

Verify all endpoints via curl or Swagger UI at `http://localhost:8000/docs`:

- [ ] **Auth:**
  - `POST /api/auth/login` with valid creds → 200 `{authenticated: true}`
  - `POST /api/auth/login` with invalid creds → 401
  - Existing endpoints (`/api/chat`, `/api/sessions`) → still open (no auth)
- [ ] **Read:**
  - `GET /api/prompts` → 35 prompts
  - `GET /api/prompts?category=BRM_BUSINESS` → filtered subset
  - `GET /api/prompts?search=revenue` → matching results
  - `GET /api/prompts/categories` → 9 categories with counts
  - `GET /api/prompts/{id}` → single prompt details
- [ ] **Favorites:**
  - `POST /api/prompts/{id}/favorite` → toggle on
  - `GET /api/prompts/favorites` → includes toggled prompt
  - `POST /api/prompts/{id}/favorite` again → toggle off
- [ ] **Execution:**
  - `POST /api/prompts/{id}/execute` → SSE stream
  - `GET /api/prompts/history` → shows execution record
- [ ] **Admin:**
  - `POST /api/prompts/admin` → create new prompt
  - `PUT /api/prompts/admin/{id}` → update prompt
  - `DELETE /api/prompts/admin/{id}` → soft delete
  - All admin endpoints without auth → 401
- [ ] **Deprecation:**
  - `GET /api/chat/templates` → returns data from prompt_library
  - Response includes `Deprecation: true` header

**Acceptance:** All checks pass with expected status codes and data

---

### 1.17.6 Frontend E2E Walkthrough (1.5h)

Browser verification of the full user journey:

- [ ] 1. Open app → login form appears (fresh browser / incognito)
- [ ] 2. Enter `admin` / `odaos2024` → access granted
- [ ] 3. Chat page loads → sidebar shows "Chat" and "Prompt Library" nav items
- [ ] 4. Click "Prompt Library" → navigates to `/prompt-library`
- [ ] 5. Library shows 35 prompts in grid with categories on left
- [ ] 6. Click "Revenue" category → filters to revenue prompts only
- [ ] 7. Type "tablespace" in search → shows matching DBA prompts
- [ ] 8. Click ⭐ on a prompt → star fills → appears in "Favorites" category
- [ ] 9. Click a parameterized prompt → parameter modal opens
- [ ] 10. Fill parameters → click "Execute" → streaming results appear
- [ ] 11. Wait for completion → execution time shown → chart renders if applicable
- [ ] 12. Click "Back to Library" → returns to grid
- [ ] 13. Check "Recent" → shows execution in history
- [ ] 14. Click "Chat" in sidebar → chat page loads
- [ ] 15. Chat still works: send message → streaming response
- [ ] 16. Toggle dark/light mode → both pages render correctly
- [ ] 17. Settings modal still works
- [ ] 18. Refresh browser → still logged in, session preserved

**Acceptance:** All 18 steps pass without errors

---

### 1.17.7 Regression Check (1h)

Verify no existing functionality is broken:

- [ ] Chat streaming (`/api/chat/stream`) works end-to-end
- [ ] Session management: create, list, select, delete sessions
- [ ] Session search in sidebar works
- [ ] Session bookmarking works
- [ ] Charts render in chat messages (SmartChart)
- [ ] Quick replies work
- [ ] Suggestions appear after responses
- [ ] Settings modal opens and closes
- [ ] Dark/light mode toggle works globally
- [ ] `GET /api/health` returns OK

**Acceptance:** All existing features work identically to before Task 1.15+1.16

---

### 1.17.8 README Update (0.5h)

**File:** `README.md`

- [ ] Add "Prompt Library" section to README
- [ ] Document setup: env vars `ADMIN_USER`, `ADMIN_PASSWORD`
- [ ] Document endpoints: `GET /api/prompts`, `POST /api/prompts/{id}/execute`
- [ ] Document seed data: 35 built-in prompts
- [ ] Add screenshots of prompt library UI

**Acceptance:**
- README includes setup instructions for prompt library
- New developer can start the app and access prompt library using only README

---

## ✅ Phase 1.17 Success Criteria

| Metric | Target |
|--------|--------|
| All API endpoints return correct responses | 100% |
| Full E2E user journey completes | 18/18 steps pass |
| Existing chat features unbroken | 10/10 checks pass |
| Dark + light mode works on all new pages | ✅ |
| No console errors in browser | ✅ |
| Prompt execution streams correctly | ✅ |
| Walkthrough document created | ✅ |

---

## 📄 Deliverables

Upon completion of Task 1.17, the following should be committed:

1. **Backend:** 4 new files + 3 modified files
2. **Frontend:** 9 new files + 5 modified files  
3. **Database:** `data/prompts.db` auto-created on startup
4. **Docs:** Updated walkthrough with screenshots
5. **Git:** Single feature branch `feature/prompt-library` or incremental commits
