# Task 1.16: Prompt Library — Frontend

## Vision
A premium, browsable prompt library UI integrated into the existing ODAOS dashboard. Users log in through a simple auth gate, navigate to the library via the sidebar, browse/search/filter prompts by category, execute them with parameter modals, view streaming results, and track their favorites and history.

**Estimated Time:** 20.5 hours (Days 4–6)
**Dependencies:** Task 1.15 (Backend API) must be complete
**Risk Level:** Medium — adds `react-router-dom` and restructures `App.tsx`

---

## 🎯 Scope

### ✅ IN SCOPE
| Feature | Priority |
|---------|----------|
| `react-router-dom` integration + `/prompt-library` route | P0 |
| Login gate (hardcoded admin, localStorage session) | P0 |
| Sidebar navigation (Chat ↔ Prompt Library) | P0 |
| Zustand store for prompts state | P0 |
| Prompt library grid view with search + filters | P0 |
| Category sidebar with counts | P0 |
| Prompt cards with tags, difficulty, favorite toggle | P0 |
| Parameter input modal for parameterized prompts | P0 |
| Streaming execution results view | P0 |
| Execution history panel | P1 |

### ❌ OUT OF SCOPE
- Admin panel for CRUD (use Swagger/curl for now)
- Drag-and-drop prompt ordering
- Prompt sharing between users
- Mobile-specific responsive layouts

---

## 📁 Files Created / Modified

```
[NEW]    frontend/src/components/Auth/LoginGate.tsx
[NEW]    frontend/src/components/PromptLibrary/PromptLibraryView.tsx
[NEW]    frontend/src/components/PromptLibrary/CategorySidebar.tsx
[NEW]    frontend/src/components/PromptLibrary/PromptCard.tsx
[NEW]    frontend/src/components/PromptLibrary/ParameterModal.tsx
[NEW]    frontend/src/components/PromptLibrary/ExecutionResultView.tsx
[NEW]    frontend/src/components/PromptLibrary/PromptHistory.tsx
[NEW]    frontend/src/stores/promptStore.ts
[MODIFY] frontend/package.json               # add react-router-dom
[MODIFY] frontend/src/main.tsx                # wrap in BrowserRouter
[MODIFY] frontend/src/App.tsx                 # Routes + Layout wrapper
[MODIFY] frontend/src/components/Layout/Sidebar.tsx  # Add nav items
[MODIFY] frontend/src/index.css               # Prompt library styles
```

---

## 📋 Sub-Tasks Breakdown

### 1.16.1 Install react-router-dom + Restructure App.tsx (2h)

**Files:** `package.json`, `main.tsx`, `App.tsx`

- [ ] `npm install react-router-dom`
- [ ] Wrap `<App />` in `<BrowserRouter>` in `main.tsx`
- [ ] Restructure `App.tsx`:
  - Extract header + sidebar into a shared `<Layout>` wrapper
  - Add `<Routes>`:
    - `/` → `<ChatContainer />`
    - `/prompt-library` → `<PromptLibraryView />` (placeholder initially)
  - Preserve sidebar state, theme toggle, session management
- [ ] Verify: chat page at `/` still works identically

**Acceptance:**
- `http://localhost:5173/` renders chat (unchanged behavior)
- `http://localhost:5173/prompt-library` renders placeholder
- Sidebar, header, theme toggle all work on both routes
- Hot reload still functions

⚠️ **RISK:** Sidebar `onSessionSelect` state must survive route changes. May need to lift state to a store or context.

---

### 1.16.2 Login Gate Component (2h)

**File:** `frontend/src/components/Auth/LoginGate.tsx`, `App.tsx`

- [ ] Full-screen login form: username + password fields, "Sign in" button
- [ ] Calls `POST /api/auth/login` with Basic Auth header
- [ ] On success: store base64 credentials in `localStorage` key `odaos_auth`
- [ ] On fail: show error message ("Invalid credentials")
- [ ] Auto-check on mount: if `localStorage` has valid token, skip login
- [ ] Wrap entire `<App>` content inside `<LoginGate>`
- [ ] Style: centered card, matches existing dark theme, subtle animation
- [ ] Add logout button in Settings modal

**Acceptance:**
- Fresh browser → login form appears
- Correct credentials (`admin` / `odaos2024`) → grants access
- Wrong credentials → error message, form stays
- Refresh → still logged in (localStorage)
- Logout → returns to login form

---

### 1.16.3 Sidebar Navigation (1h)

**File:** `frontend/src/components/Layout/Sidebar.tsx`

- [ ] Add navigation section at top of sidebar:
  - `💬 Chat` → navigates to `/`
  - `📚 Prompt Library` → navigates to `/prompt-library`
- [ ] Active state highlight based on `useLocation()` from react-router
- [ ] Use `useNavigate()` for programmatic navigation
- [ ] Separator line between nav items and session list
- [ ] Session list only visible when on Chat page

**Acceptance:**
- Clicking "Prompt Library" navigates to `/prompt-library`
- Active item is visually highlighted
- Session list hides when on Prompt Library page

---

### 1.16.4 Prompt Library Zustand Store (2h)

**File:** `frontend/src/stores/promptStore.ts`

- [ ] State: `prompts[]`, `categories[]`, `favorites[]`, `history[]`, `selectedCategory`, `searchQuery`, `selectedPrompt`, `isExecuting`, `executionResult`, `loading`, `error`
- [ ] Actions:
  - `fetchPrompts(category?, search?, tag?)` — `GET /api/prompts`
  - `fetchCategories()` — `GET /api/prompts/categories`
  - `fetchFavorites()` — `GET /api/prompts/favorites`
  - `toggleFavorite(promptId)` — `POST /api/prompts/{id}/favorite`
  - `executePrompt(promptId, params)` — `POST /api/prompts/{id}/execute` (SSE)
  - `fetchHistory(limit, offset)` — `GET /api/prompts/history`
  - `setSelectedCategory(category)` — filter + refetch
  - `setSearchQuery(query)` — debounced search
- [ ] All API calls include auth header from `localStorage`

**Acceptance:**
- `usePromptStore.getState().fetchPrompts()` populates `prompts` with 35 items
- `fetchCategories()` returns 9 categories
- `toggleFavorite()` updates `favorites` array reactively

---

### 1.16.5 PromptLibraryView — Main Layout (3h)

**File:** `frontend/src/components/PromptLibrary/PromptLibraryView.tsx`

- [ ] Two-column layout: left `<CategorySidebar>` (240px) + right content area
- [ ] Header bar: title "Prompt Library", search input, view toggle (grid/list)
- [ ] Grid of `<PromptCard>` components (3–4 columns responsive)
- [ ] Fetches prompts + categories on mount via store
- [ ] Search input with debounce (300ms)
- [ ] Empty state: "No prompts found" with reset filter button
- [ ] Loading state: skeleton cards while fetching

**Acceptance:**
- Page shows all 35 prompts in grid
- Clicking category in sidebar filters prompts
- Typing in search narrows results in real-time
- Loading shows skeleton, then cards fade in

---

### 1.16.6 CategorySidebar Component (1.5h)

**File:** `frontend/src/components/PromptLibrary/CategorySidebar.tsx`

- [ ] Sections:
  - **Quick Access:** ⭐ Favorites (count), 🕐 Recent (count), 📁 All Prompts (count)
  - **BRM Business:** Revenue, Customer, Payment, Operations
  - **DBA Operational:** Health, Performance, Capacity, Locks, Backup, Config
- [ ] Each item shows: icon + label + count badge
- [ ] Click selects category → store updates → grid filters
- [ ] Active category highlighted with accent color

**Acceptance:**
- Counts match actual prompt distribution
- Clicking "Revenue" shows only revenue prompts
- "All Prompts" clears filter

---

### 1.16.7 PromptCard Component (2h)

**File:** `frontend/src/components/PromptLibrary/PromptCard.tsx`

- [ ] Card shows: category icon, title, description (2 lines truncated), tag badges, difficulty badge (color-coded: green/yellow/red), estimated runtime text
- [ ] Actions: ⭐ favorite toggle button, ▶️ "Run" button
- [ ] Hover: subtle elevation + border glow
- [ ] Click card → opens `ParameterModal` (or executes directly if no params)
- [ ] Favorite state reactive from store

**Acceptance:**
- Card renders all fields correctly
- Favorite toggle persists via API
- Difficulty "beginner" → green, "intermediate" → yellow, "advanced" → red
- Hover animation is smooth

---

### 1.16.8 ParameterModal Component (2.5h)

**File:** `frontend/src/components/PromptLibrary/ParameterModal.tsx`

- [ ] Modal overlay with prompt title and description
- [ ] Dynamic form fields generated from prompt's `parameters` schema:
  - Text input for strings
  - Number input for integers
  - Dropdown for enum values (e.g., quarter: Q1/Q2/Q3/Q4)
  - Date picker for date parameters
- [ ] Pre-fills with `default_values` from prompt
- [ ] Preview section: shows prompt template with params filled in (live update)
- [ ] Shows estimated runtime badge
- [ ] Shows `requires_approval` warning badge if true
- [ ] Cancel and "Execute Prompt" buttons
- [ ] Validation: required params must be filled

**Acceptance:**
- Opening modal for "Revenue by Product" shows Quarter + Year fields
- Changing a param updates the preview in real-time
- Empty required field → validation error
- Execute button triggers streaming

---

### 1.16.9 ExecutionResultView Component (3h)

**File:** `frontend/src/components/PromptLibrary/ExecutionResultView.tsx`

- [ ] Replaces the grid when a prompt is being executed
- [ ] Shows: prompt title, "Executing..." status with timer
- [ ] Streaming text area (reuse markdown rendering from `MessageList`)
- [ ] Chart rendering if SSE sends `chart` event (reuse `SmartChart`)
- [ ] Completion: show execution time, status badge (success/error)
- [ ] Action buttons: "Run Again", "Modify Parameters", "Back to Library"
- [ ] Handles SSE events: `token`, `chart`, `suggestions`, `done`, `error`

**Acceptance:**
- Executing prompt shows streaming text
- Chart appears below text when data arrives
- Error shows error message with retry button
- "Back to Library" returns to grid view

---

### 1.16.10 PromptHistory Component (1.5h)

**File:** `frontend/src/components/PromptLibrary/PromptHistory.tsx`

- [ ] Accessed via "🕐 Recent" in CategorySidebar
- [ ] Table/list view: prompt title, timestamp, parameters used, status badge, execution time
- [ ] Click row → "Re-run" with same parameters
- [ ] Paginated (20 per page)
- [ ] Empty state: "No execution history yet"

**Acceptance:**
- After 3 executions, history shows all 3
- Timestamps formatted nicely (e.g., "2 hours ago")
- Re-run opens ParameterModal with previous params pre-filled

---

## 🎨 Design Guidelines

All components must use the existing design system:

| Element | Style |
|---------|-------|
| Card background | `var(--bg-secondary)` |
| Card border | `var(--border-subtle)` |
| Hover | `var(--bg-hover)` + 1px border glow |
| Tags | Small pills, `var(--accent-primary)` bg with opacity |
| Difficulty badges | Success/warning/error accent colors |
| Animations | `framer-motion` — staggered card entry, modal slide-up |
| Typography | Same as chat (Inter/system font) |

---

## ✅ Phase 1.16 Success Criteria

| Metric | Target |
|--------|--------|
| Login gate blocks unauthenticated users | ✅ |
| Prompt library route accessible | ✅ |
| All 35 prompts visible and searchable | ✅ |
| Category filtering works | ✅ |
| Favorites persist across sessions | ✅ |
| Prompt execution streams results | ✅ |
| No regression in chat functionality | ✅ |
| Dark/light mode works on all new pages | ✅ |
