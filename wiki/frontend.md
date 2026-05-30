# Frontend — React + TypeScript + Vite

**Directory:** `frontend/`

## Design Reference

Visual design matches `docs/demo.html`. Three-column layout, obsidian background `#080A0F`, amber `#F5A623` accents, Syne + IBM Plex Mono fonts.

## Component Tree

```
App.tsx
├── TopBar.tsx              — Logo, subtitle, elapsed timer, cost pill
├── [Progress strip]        — 3px amber gradient, width = progress%
└── [Three-column grid]
    ├── AgentPanel.tsx      — Agent pipeline list, metrics
    ├── ChatArea.tsx        — Message stream, task bar, input/interrupt
    └── DetailsPanel.tsx    — Browser/Models/Verify tabs
```

## Key Files

| File | Purpose |
|------|---------|
| `src/types.ts` | All TypeScript types: WSMessage union, AgentState, WorkflowUIState |
| `src/styles.css` | CSS variables (design tokens) + animations |
| `src/hooks/useWorkflow.ts` | WebSocket connection, state machine, all message dispatch |
| `src/components/TopBar.tsx` | Header with logo, cost, elapsed time |
| `src/components/AgentPanel.tsx` | Left sidebar: agent pipeline + metrics |
| `src/components/ChatArea.tsx` | Center: streaming messages + input bar |
| `src/components/DetailsPanel.tsx` | Right: browser/models/verify tabs |

## CSS Variables (Design Tokens)

```css
--bg: #080A0F          /* main background */
--surface: #0F1118     /* panel backgrounds */
--elevated: #171B25    /* elevated elements */
--border: #232735      /* default border */
--border-hi: #2E3447   /* highlighted border */
--amber: #F5A623       /* primary accent */
--amber-dim: #C47D0E
--amber-glow: #F5A62322
--teal: #00C9A7        /* success/done */
--teal-dim: #00876F
--red: #FF5C5C
--green: #3DDB85
--purple: #9B7FFF      /* reviewer accent */
--text: #C8CEDF
--text-dim: #5E6680
--text-hi: #EEF1FA
--mono: 'IBM Plex Mono', monospace
--sans: 'IBM Plex Sans', sans-serif
--display: 'Syne', sans-serif
```

## State Management (useWorkflow.ts)

`WorkflowUIState` holds all UI state. `applyMessage()` is a pure function that maps each incoming `WSMessage` to a state update. No Redux, no Zustand — plain React `useState`.

## Agent Color Scheme

| Agent | Background | Border | Text |
|-------|-----------|--------|------|
| evaluator/router | amber-glow | amber-dim | amber |
| researcher | teal/11 | teal/44 | teal |
| architect/coder | blue/11 | blue/44 | #60A5FA |
| reviewer | purple/11 | purple/44 | purple |
| verifier | green/11 | green/44 | green |
| user | violet/22 | violet/44 | #A78BFA |

## Grid Layout

```css
/* App.tsx main grid */
display: grid;
grid-template-columns: 240px 1fr 320px;
```
