# ClearWayAI Technical Documentation Portal (`docs-site`)

Standalone technical documentation website built with React, Vite, and TypeScript. Automatically deployed to GitHub Pages via GitHub Actions.

---

## 1. Directory Structure

```
docs-site/
├── public/
│   └── 404.html            # SPA fallback script for GitHub Pages deep linking
├── src/
│   ├── components/
│   │   ├── Header.tsx      # Top bar with search trigger and theme switcher
│   │   ├── Sidebar.tsx     # Categorized navigation with task status tags
│   │   ├── SearchModal.tsx # Full-text keyword search dialog (Ctrl+K)
│   │   ├── DocViewer.tsx   # Markdown renderer, code copy, and callouts
│   │   └── MermaidChart.tsx# SVG flowcharts and sequence diagrams
│   ├── data/
│   │   └── docsContent.ts  # Knowledge base covering 24 comprehensive chapters
│   ├── App.tsx             # Theme management and hash router
│   ├── index.css           # Dark and light theme variables
│   └── main.tsx            # Entrypoint
├── package.json
├── tsconfig.json
├── vite.config.ts          # Base path configured for /ClearWayAI/
└── README.md
```

---

## 2. Features

- **24 Technical Chapters:** Covers all aspects from initial mathematical formulation to 3D coordinate mapping and physical hardware prototypes.
- **Instant Search:** Full-text keyword search across titles, categories, and content snippets.
- **Theme Support:** Dark and Light themes with persistent state in `localStorage`.
- **Code Copy:** Single-click copy button for code blocks.
- **Status Indicators:** Clearly marks each topic as `VERIFIED` or `PLAN` to match the source of truth in `docs/PROJECT_STATUS.md`.

---

## 3. Running Locally

```bash
# Start docs development server (port 3001)
pnpm --filter clearway-docs-site dev

# Build production bundle
pnpm --filter clearway-docs-site build
```

---

## 4. Deployment

Automated by `.github/workflows/docs-deploy.yml` upon push to `main`. Published to:  
`https://nguyentribaothang.github.io/ClearWayAI/`

