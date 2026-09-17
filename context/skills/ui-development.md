---
name: ui-development
description: Procedural guidance for authoring UI components and layouts.
globs: ["**/*.tsx", "**/*.jsx"]
---

# UI Development Skill

---

## Overview
Procedural guidance for UI styling, component creation, and layout authoring.

---

## 1. Styling Priority

When styling components, follow this strict priority order:
1. **DaisyUI semantic classes**: e.g., `btn`, `card`, `modal`, `alert`.
2. **Tailwind utility classes**: e.g., `flex`, `p-4`, `text-lg`.
3. **Custom CSS**: ONLY when neither DaisyUI nor Tailwind provides what's needed.

---

## 2. Component Patterns

Use semantic classes instead of custom styles:

| Action | Correct | Wrong |
|--------|---------|-------|
| Button | `className="btn btn-primary"` | `style={{...}}` or custom `.my-button` |
| Card | `className="card"` | custom `.custom-card` with `.css` file |
| Layout | Tailwind `flex`, `grid`, `gap-4` | Custom CSS grid/flexbox |
| Theming | DaisyUI theme + CSS custom properties | Hardcoded hex values |

---

## 3. Rationale
Custom CSS creates inconsistency, breaks theme switching, and duplicates what the design system already provides. DaisyUI + Tailwind cover 95%+ of UI needs.

---

## 4. Visual Fidelity & Design Handoff

Before writing UI code, always reference:
1. `{project-root}/artefacts/design/design-system.md` (foundations, components, wireframes)
2. `context/standards/visual-standards.md` for hierarchy, spacing, responsive rules

**Creative Latitude:**
Wireframes are a starting point, not a pixel-perfect spec. Agents may improve on wireframes — better layouts, clearer hierarchy, improved interactions are encouraged. But the design intent must be preserved. Document any deviations in the handoff with a rationale.

**Implementation Requirements:**
- Implement all states: empty, loading, error, populated.
- Test at breakpoints from `visual-standards.md`.

---

## 5. Required Rule Invariants (Enforced via Pre-Commit)
When executing this skill, ensure output satisfies the deterministic rules:
- UI Development constraints: `context/rules/ui-dev.md`
