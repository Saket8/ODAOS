# Task 1.14: Premium Web Dashboard - MVP

## Vision
A **conversational AI-first dashboard** that anticipates user needs, delivers stunning visualizations, and delights with purposeful microinteractions. Non-technical users interact naturally - the interface feels intelligent, not intimidating.

**Estimated Time:** 60-70 hours (Week 1-3)

---

## 🎯 MVP Feature Matrix

### ✅ IN SCOPE (MVP)

| Category | Feature | Priority |
|----------|---------|----------|
| **Conversational AI** | Natural language chat interface | P0 |
| | Context-aware multi-turn conversations | P0 |
| | Typing indicators + streaming responses | P0 |
| | Quick-reply suggestion buttons | P0 |
| | AI-suggested follow-up questions | P1 |
| **Smart Visualizations** | Vector SVG charts (crisp at any zoom) | P0 |
| | Drill-down on click | P0 |
| | Hover tooltips with context | P0 |
| | Auto chart type selection by data | P0 |
| | Smart narratives (AI text summaries) | P1 |
| | Cross-filtering between charts | P1 |
| **Modern Design** | Glassmorphism + frosted glass | P0 |
| | Dark/Light mode with smooth transition | P0 |
| | Minimalist whitespace design | P0 |
| | Gradient overlays + layered depth | P0 |
| **Microinteractions** | Button ripple effects | P0 |
| | Skeleton loading screens | P0 |
| | Animated chart transitions | P0 |
| | Success celebrations (subtle) | P1 |
| | Scroll-triggered reveals | P1 |
| **Performance** | <2s page load | P0 |
| | <100ms interaction feedback | P0 |
| | Skeleton screens (no spinners) | P0 |
| | Progressive data loading | P0 |
| **Sessions** | Searchable chat history | P0 |
| | Resume previous conversations | P0 |
| | Export conversations | P1 |

### ❌ DEFERRED TO PRODUCTION (Task 2.7)

- Voice input, Real-time collaboration
- Predictive analytics, Anomaly detection overlays
- 3D visualizations, Sankey diagrams
- Gamification (badges, streaks)
- PWA/Mobile apps, Offline mode
- Team workspaces, @mentions
- Query scheduling, Slack/Teams integration
- Live co-editing, Version history

---

## 🏗️ Architecture

### Technology Stack

| Layer | Technology | Why |
|-------|------------|-----|
| **Frontend** | React 18 + Vite | Fast HMR, concurrent features |
| **styling** | Tailwind CSS + Framer Motion | Utility-first + production animations |
| **Charts** | Plotly.js + D3.js | Interactive + custom visualizations |
| **State** | Zustand + React Query | Simple state + async data caching |
| **Themes** | CSS Variables + next-themes | Smooth dark mode transitions |
| **Backend** | FastAPI (Python) | Reuse existing ODAOS core |
| **Streaming** | Server-Sent Events (SSE) | LLM response streaming |
| **Storage** | SQLite → PostgreSQL | Easy migration path |

### System Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                    ODAOS Premium Dashboard                              │
├────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    React Frontend                                │   │
│  │                                                                  │   │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────┐  │   │
│  │  │ Conversational   │  │ Smart Viz Engine │  │ Proactive     │  │   │
│  │  │ Chat Interface   │  │                  │  │ Intelligence  │  │   │
│  │  │                  │  │ • Plotly Charts  │  │               │  │   │
│  │  │ • Multi-turn     │  │ • D3 Custom      │  │ • AI Insights │  │   │
│  │  │ • Quick Replies  │  │ • Cross-filter   │  │ • Suggestions │  │   │
│  │  │ • Streaming      │  │ • Drill-down     │  │ • Smart Narr. │  │   │
│  │  │ • Context Memory │  │ • Auto-select    │  │               │  │   │
│  │  └────────┬─────────┘  └────────┬─────────┘  └───────┬───────┘  │   │
│  │           │                     │                     │          │   │
│  │  ┌────────▼─────────────────────▼─────────────────────▼───────┐  │   │
│  │  │              Glassmorphism UI Layer                        │  │   │
│  │  │  Framer Motion Animations • Dark Mode • Microinteractions  │  │   │
│  │  └────────────────────────────┬───────────────────────────────┘  │   │
│  └───────────────────────────────┼──────────────────────────────────┘   │
│                                  │ SSE/HTTP                              │
│  ┌───────────────────────────────▼──────────────────────────────────┐   │
│  │                       FastAPI Backend                             │   │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────────┐  │   │
│  │  │ /api/chat/stream│  │ /api/viz/{type} │  │ /api/insights    │  │   │
│  │  │ SSE Streaming   │  │ Dynamic Charts  │  │ AI Suggestions   │  │   │
│  │  └────────┬────────┘  └────────┬────────┘  └─────────┬────────┘  │   │
│  │           │                    │                      │           │   │
│  │  ┌────────▼────────────────────▼──────────────────────▼────────┐  │   │
│  │  │                 ODAOS Core (Existing)                       │  │   │
│  │  │  ODAOSOrchestrator • AnalyticsAgent • PerformanceAgent     │  │   │
│  │  └─────────────────────────────────────────────────────────────┘  │   │
│  └───────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌──────────────┐  ┌────────────────┐  ┌─────────────────────────────┐  │
│  │ SQLite       │  │ Oracle DB      │  │ SSH Tunnel (BRM Data)       │  │
│  │ (Sessions)   │  │ PIN/PDC/ECE    │  │                             │  │
│  └──────────────┘  └────────────────┘  └─────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── Chat/
│   │   │   ├── ChatContainer.tsx       # Main conversational interface
│   │   │   ├── MessageBubble.tsx       # Glassmorphism message cards
│   │   │   ├── StreamingText.tsx       # Typewriter effect for AI
│   │   │   ├── QuickReplies.tsx        # Suggestion buttons
│   │   │   ├── TypingIndicator.tsx     # Animated dots
│   │   │   └── FollowUpSuggestions.tsx # AI-generated follow-ups
│   │   ├── Visualizations/
│   │   │   ├── ChartContainer.tsx      # Auto chart type selection
│   │   │   ├── InteractivePie.tsx      # Drill-down pie
│   │   │   ├── InteractiveBar.tsx      # Click-to-filter bars
│   │   │   ├── LineWithForecast.tsx    # Trend + prediction overlay
│   │   │   ├── HeatMap.tsx             # Plotly heatmap
│   │   │   ├── SmartNarrative.tsx      # AI text summary of chart
│   │   │   └── ChartExport.tsx         # PNG/SVG/PDF export
│   │   ├── Layout/
│   │   │   ├── GlassPanel.tsx          # Frosted glass container
│   │   │   ├── Sidebar.tsx             # Session history
│   │   │   ├── ThemeToggle.tsx         # Dark/light with transition
│   │   │   └── Header.tsx              # Minimal header
│   │   ├── Microinteractions/
│   │   │   ├── RippleButton.tsx        # Click ripple effect
│   │   │   ├── SkeletonLoader.tsx      # Shimmer loading
│   │   │   ├── SuccessCelebration.tsx  # Confetti/checkmark
│   │   │   └── ScrollReveal.tsx        # Fade in on scroll
│   │   └── Insights/
│   │       ├── ProactiveCard.tsx       # AI-surfaced insights
│   │       └── AnomalyBadge.tsx        # Highlight unusual data
│   ├── hooks/
│   │   ├── useChat.tsx                 # Chat state + streaming
│   │   ├── useChartData.tsx            # Reactive chart data
│   │   └── useTheme.tsx                # Theme management
│   ├── stores/
│   │   ├── chatStore.ts                # Zustand chat state
│   │   └── sessionStore.ts             # History state
│   ├── styles/
│   │   ├── globals.css                 # Base + glassmorphism
│   │   └── animations.css              # Keyframe animations
│   └── utils/
│       ├── chartAutoSelect.ts          # AI chart type selection
│       └── narrativeGenerator.ts       # Smart text summaries
```

---

## 🎨 Design System

### Glassmorphism Theme

```css
/* Glass card effect */
.glass-card {
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
}

/* Dark mode optimized */
.dark .glass-card {
  background: rgba(17, 24, 39, 0.7);
  border: 1px solid rgba(255, 255, 255, 0.05);
}
```

### Color Palette

| Purpose | Light Mode | Dark Mode |
|---------|------------|-----------|
| Background | `#F8FAFC` | `#0F172A` |
| Glass | `rgba(255,255,255,0.08)` | `rgba(17,24,39,0.7)` |
| Primary | `#3B82F6` | `#60A5FA` |
| Success | `#10B981` | `#34D399` |
| Warning | `#F59E0B` | `#FBBF24` |
| Error | `#EF4444` | `#F87171` |

### Animation Specs

| Animation | Duration | Easing |
|-----------|----------|--------|
| Theme switch | 300ms | ease-out |
| Chart transition | 500ms | spring(1, 80, 10) |
| Message appear | 200ms | ease-out |
| Skeleton shimmer | 1.5s | linear(loop) |
| Button ripple | 400ms | ease-out |

---

## 📡 API Design

### Streaming Chat Endpoint

```python
# Server-Sent Events for LLM streaming
@app.get("/api/chat/stream")
async def stream_chat(
    message: str,
    session_id: str,
    include_viz: bool = True
):
    async def event_generator():
        # Stream LLM response tokens
        async for token in orchestrator.stream(message):
            yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"
        
        # Send chart data if applicable
        if include_viz and needs_visualization(message):
            chart_data = await generate_chart(message)
            yield f"data: {json.dumps({'type': 'chart', 'data': chart_data})}\n\n"
        
        # Send follow-up suggestions
        suggestions = await generate_followups(message)
        yield f"data: {json.dumps({'type': 'suggestions', 'items': suggestions})}\n\n"
        
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
    
    return EventSourceResponse(event_generator())
```

### Smart Visualization Endpoint

```python
@app.post("/api/viz/smart")
async def smart_visualization(request: VizRequest):
    """Auto-selects best chart type based on data structure."""
    data = await fetch_data(request.query)
    
    chart_type = auto_select_chart_type(data)  # AI selection
    narrative = generate_smart_narrative(data)  # AI summary
    anomalies = detect_anomalies(data)          # Highlight unusual
    
    return {
        "chart_type": chart_type,
        "data": data,
        "narrative": narrative,
        "anomalies": anomalies,
        "drill_down_options": get_drill_options(data)
    }
```

---

## 📋 Sub-Tasks Breakdown

### 1.14.1 Backend API Foundation (10-12h)
- [ ] FastAPI app structure with SSE support
- [ ] `/api/chat/stream` with LLM streaming
- [ ] `/api/viz/smart` with auto chart selection
- [ ] `/api/insights` for proactive suggestions
- [ ] `/api/sessions` CRUD operations
- [ ] Session storage in SQLite

### 1.14.2 Conversational Chat Interface (12-15h)
- [ ] Chat container with glass panel styling
- [ ] Multi-turn context management
- [ ] Streaming text with typewriter effect
- [ ] Quick-reply suggestion buttons
- [ ] AI-generated follow-up questions
- [ ] Typing indicator animation
- [ ] Message persistence to sessions

### 1.14.3 Smart Visualizations (12-15h)
- [ ] Plotly integration with drill-down
- [ ] Auto chart type selection logic
- [ ] Cross-filtering between charts
- [ ] Smart narrative generation
- [ ] Hover tooltips with context
- [ ] Export to PNG/SVG/PDF
- [ ] Animated transitions

### 1.14.4 Glassmorphism UI + Microinteractions (10-12h)
- [ ] Glass card components
- [ ] Dark/light theme with smooth transition
- [ ] Skeleton loading screens
- [ ] Button ripple effects
- [ ] Scroll reveal animations
- [ ] Success celebration (subtle)
- [ ] Gradient overlays

### 1.14.5 Session & History Management (6-8h)
- [ ] Sidebar with session list
- [ ] Search within history
- [ ] Resume previous conversations
- [ ] Export conversation to PDF
- [ ] Bookmark important insights

### 1.14.6 Proactive Intelligence (6-8h)
- [ ] AI-suggested insights panel
- [ ] Context-aware recommendations
- [ ] "What's changed" summary
- [ ] Anomaly highlighting (visual badges)

### 1.14.7 Integration & Testing (6-8h)
- [ ] E2E tests for chat flow
- [ ] Chart rendering tests
- [ ] Dark mode visual tests
- [ ] Performance benchmarks
- [ ] Accessibility audit (WCAG 2.1 A)

---

## ✅ Success Criteria

| Metric | Target |
|--------|--------|
| Page load | <2s |
| Interaction feedback | <100ms |
| Chart render | <500ms |
| LLM first token | <1s |
| Test coverage | >70% |
| Lighthouse Performance | >90 |
| Lighthouse Accessibility | >85 |
| Theme switch | <300ms (no flicker) |

---

## 🎬 Inspiration References

- **Stripe** - Form microinteractions
- **Linear** - Minimal dark UI
- **Notion AI** - Context-aware suggestions
- **ChatGPT** - Streaming chat UX
- **Tableau** - Interactive viz drill-down
- **Vercel Dashboard** - Glassmorphism done right
