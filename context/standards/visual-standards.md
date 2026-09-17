# Visual Design Standards

**Core Principle**: Design for clarity, accessibility, and user comprehension. Every visual element should serve a purpose.

---

## Design Principles

These principles guide all design decisions. When specific rules in this document don't cover a situation, fall back to these.

| # | Principle | Guidance |
|---|-----------|----------|
| 1 | **Don't make users think** | Navigation, actions, and labels must be self-explanatory. If a user has to guess what something does, redesign it. |
| 2 | **Don't squander patience** | Minimise barriers. Let users explore before requiring sign-up, input, or commitment. Progressive disclosure over upfront complexity. |
| 3 | **Guide attention deliberately** | Use visual hierarchy (see §Visual Hierarchy) to direct the eye. Every screen should have one clear focal point. |
| 4 | **Make features discoverable** | Available actions must be visible, not hidden in menus or behind hover states. If a feature exists, users should find it without a tutorial. |
| 5 | **Write concisely** | UI text must be scannable — short headings, clear labels, no marketing fluff. Front-load the important word in every label and heading. |
| 6 | **Choose simplicity** | When choosing between a simple and a clever solution, choose simple. Remove elements until something breaks, then add the last one back. |
| 7 | **Use white space generously** | Spacing reduces cognitive load and groups related content (see §Spacing Scale). When in doubt, add more space, not less. |
| 8 | **Be visually consistent** | Same patterns for same concepts. Consistent alignment, spacing, colour usage, and component treatment across all screens (see §Component Patterns). |
| 9 | **Follow conventions** | Use established UI patterns (see §Page Layout Patterns, §Component Patterns). Users bring expectations from other apps — leverage that familiarity, don't fight it. |
| 10 | **Test with real users** | Design assumptions must be validated. Test early with real tasks, not opinions. One user test is better than none. |

**Applying These Principles**:
- Before adding a UI element, ask: does this serve one of these principles or violate one?
- When two principles conflict (e.g. discoverability vs simplicity), favour the one that reduces user effort
- These principles apply to all agents: designers decide layout, coders preserve intent, testers verify compliance

---

## Visual Hierarchy

Every screen must have a clear information hierarchy so users can scan, understand, and act without effort. If a user cannot identify the most important element within 3 seconds, the hierarchy has failed.

### Three Levels of Information

All content and actions fall into three levels. Assign each element a level before designing.

| Level | Purpose | Visual Treatment |
|-------|---------|-----------------|
| **Primary** | The one thing users must see or do first | Largest, highest contrast, prominent position, strongest colour |
| **Secondary** | Supports or offers alternative to primary | Medium size, muted colour, adjacent to primary |
| **Tertiary** | Adds context but is not critical | Smallest, lowest visual weight, can be hidden behind disclosure |

**Rules**:
- Each screen should have exactly one primary focal point — if everything is emphasised, nothing is
- No more than 3 levels of visual contrast on a single screen
- Primary actions must be visually distinct from secondary (not just a different shade)

### Hierarchy Techniques

**Priority order** (strongest to weakest influence on the eye):

| Technique | How It Creates Hierarchy |
|-----------|-------------------------|
| **Size & scale** | Larger elements are seen first. Use for headings, primary actions, hero content. |
| **Colour & contrast** | High-contrast elements advance; low-contrast elements recede. Limit to 3 contrast levels — if everything is bold, nothing stands out. |
| **Position** | Top-left (in LTR layouts) is scanned first. Place primary content in the natural reading path (F-pattern for text-heavy, Z-pattern for sparse). |
| **Typography weight** | Bold, larger, or differently-styled text signals importance. Use distinct treatments for heading, subheading, and body. |
| **White space** | Elements with more surrounding space receive more attention (see §Spacing Scale). Isolate important elements with generous margins. |
| **Common region** | Elements sharing a background, border, or card are perceived as a group. Use containers to chunk related information. |
| **Alignment** | Aligned elements are understood as related. Break alignment deliberately to draw attention to an element. |
| **Motion** | A moving element carries greater visual weight than static ones. Use sparingly — only for drawing attention to updates or interactive affordances (see §Animation & Motion). |

### Gestalt Principles

Apply these perceptual principles to group and separate information:

- **Proximity**: Related elements close together, unrelated elements spaced apart
- **Similarity**: Consistent visual cues (colour, shape, size) for items of the same type
- **Continuity**: Guide the eye along natural paths — aligned elements, consistent flow
- **Closure**: Use implied shapes and borders to reduce visual clutter
- **Common region**: Shared containers (cards, backgrounds) group related content

### Progressive Disclosure

Not all information needs to be visible at once. Reduce cognitive load by revealing information in stages.

- Show the minimum needed to understand and act — hide supporting detail behind expand/collapse, tabs, or drill-down
- Primary information always visible; secondary on hover or click; tertiary on dedicated detail view
- Never hide primary actions or critical status behind disclosure — only tertiary content

### Scanning Patterns

Design layouts to match how users actually scan screens:

| Pattern | When to Use | Layout Approach |
|---------|-------------|-----------------|
| **F-pattern** | Text-heavy pages (articles, docs, lists) | Important content in first two lines; front-load key words at line beginnings |
| **Z-pattern** | Sparse pages (landing, login, hero sections) | Key elements at top-left, top-right, centre, and bottom-right |
| **Gutenberg diagram** | Evenly distributed content | Primary info top-left (primary optical area), CTA bottom-right (terminal area) |

**Rules**:
- Place the most important element where the scanning pattern starts (top-left for LTR)
- Users scan headings and first words — front-load meaning in every label and heading
- Break the scanning pattern deliberately only when you need to draw attention to something critical

---

## Colour & Accessibility

**WCAG 2.1 AA Requirements** (Mandatory):

| Element | Minimum Contrast |
|---------|-----------------|
| Normal text (<18px) | 4.5:1 |
| Large text (≥18px or 14px bold) | 3:1 |
| UI components (borders, icons) | 3:1 |
| Focus indicators | 3:1 |

**WCAG AAA Target** (Recommended):

| Element | Target Contrast |
|---------|----------------|
| Normal text | 7:1 |
| Large text | 4.5:1 |

**Colour Token Naming** (Semantic):

```
✓ action-primary, danger-01, text-muted
✗ blue-500, red-400, gray-300
```

**Colour-Blind Safe**:
- Don't rely on colour alone to convey information
- Use shapes, patterns, or labels alongside colour
- Test with colour blindness simulators

---

## Data Visualisation

### Chart Types

**Line Charts**: Time-series data, trends over time
- Single-colour for one dataset, multi-colour for comparison
- Clear data points at appropriate density
- Smooth lines for continuous data, stepped for discrete

**Bar Charts**: Comparing quantities across categories
- Consistent bar width and spacing
- Baseline at zero (unless justified otherwise)
- Horizontal bars for long category labels

**Scatter Plots**: Correlation between two variables
- Size/colour for third dimension
- Trend line when showing correlation
- Clear axis labels with units

**Heatmaps**: Dense data showing intensity/frequency
- Sequential colour scale (light to dark)
- Diverging scale for positive/negative values
- Clear legend showing scale

### Chart Best Practices

| Do | Don't |
|----|-------|
| Start Y-axis at appropriate scale | Truncate axes deceptively |
| Use consistent scales across related charts | Mix scales without clear labels |
| Add clear axis labels with units | Assume users know the scale |
| Use annotations sparingly | Clutter with excessive labels |
| Show data density appropriate to timeframe | Compress/expand data misleadingly |
| Use colour purposefully | Rainbow gradients without meaning |

**Chart Clarity**:
- One key insight per visualisation
- Title describes the takeaway, not just the data
- Legend positioned to not obscure data
- Gridlines subtle (10-20% opacity)
- Markers/indicators at points of interest, not spanning entire chart

---

## Tooltips

**Content Rules**:
- Maximum ~20 characters per line
- Show only relevant information for context
- Different tooltip content for different element types
- No critical information hidden in tooltips only

**Positioning**:
- Adjacent to target element (above, below, or side)
- Never obscure the element being described
- Use arrow/pointer to connect tooltip to target
- Flip position if near viewport edge

**Behaviour**:
- Appear on hover (desktop) or tap (mobile)
- 100-200ms delay before showing (prevent flicker)
- Smooth fade animation (150-200ms)
- Easy to dismiss (move away, click elsewhere)

**Accessibility**:
- Keyboard accessible (focus triggers tooltip)
- Screen reader compatible (aria-describedby)
- Sufficient contrast for tooltip text

---

## Interactive States

**Required States for Interactive Elements**:

| State | Visual Treatment |
|-------|-----------------|
| Default | Base styling |
| Hover | Subtle highlight (background, border, or shadow) |
| Focus | Visible outline (2px, high contrast) |
| Active/Pressed | Slightly depressed or colour shift |
| Disabled | 50% opacity, cursor: not-allowed |
| Loading | Spinner or skeleton, preserve dimensions |
| Error | Red border/text, error icon, message |
| Success | Green indicator, confirmation message |

**Focus Indicators**:
- Never remove focus outlines without alternative
- Use `outline-offset` for better aesthetics
- Ensure 3:1 contrast against background

---

## Responsive Design

**Breakpoints** (Mobile-first):

| Name | Width | Target |
|------|-------|--------|
| sm | ≥640px | Large phones |
| md | ≥768px | Tablets |
| lg | ≥1024px | Laptops |
| xl | ≥1280px | Desktops |
| 2xl | ≥1536px | Large monitors |

**Touch Targets**:
- Minimum 44×44px for touch devices
- 8px minimum spacing between targets
- Larger targets for primary actions

---

## Layout System

**Container Constraints**:
- Content must never stretch to full viewport width on large screens
- Default page container: max-width ~1280px, centred horizontally
- Prose content: max-width 65ch for readability

**Grid System** (12-column):

| Context | Columns | Responsive Behaviour |
|---------|---------|---------------------|
| Page layout | 12 columns, 24px gap | Full grid at all sizes |
| Dashboard | 1 → 2 → 3 columns | Single column on mobile, expands with breakpoint |
| Sidebar + content | 3 + 9 columns | Sidebar collapses on mobile |
| Form layout | 1 → 2 columns | Stacks on mobile |

**Container Padding by Breakpoint**:

| Breakpoint | Horizontal Padding |
|------------|-------------------|
| Mobile (<640px) | 16px |
| Tablet (≥640px) | 24px |
| Desktop (≥1024px) | 32px |

**Rules**:
- Every page must have a max-width container — never allow content to span edge-to-edge
- Sidebar navigation should collapse to a hamburger menu below tablet breakpoint
- Content areas must have consistent padding at each breakpoint

---

## Spacing Scale

**Base Unit**: 4px. All spacing must use multiples of the base unit.

| Token | Size | Usage |
|-------|------|-------|
| space-1 | 4px | Tight: icon-to-label, inline elements |
| space-2 | 8px | Compact: within components, form field gaps |
| space-3 | 12px | Default: list items, small internal padding |
| space-4 | 16px | Standard: card padding, input padding |
| space-6 | 24px | Comfortable: between related sections |
| space-8 | 32px | Spacious: between distinct sections |
| space-12 | 48px | Loose: between major page regions |
| space-16 | 64px | Page-level: top/bottom page margins |
| space-24 | 96px | Hero/feature sections |

**Guidelines**:
- Within a component: use space-2 to space-4
- Between sibling components: use space-6 to space-8
- Between page sections: use space-12 to space-16
- Never use arbitrary values — always use the scale
- Vertical rhythm should feel consistent; if in doubt, use more space, not less

---

## Overflow Rules

**Mandatory**:
- No horizontal scrollbars at any breakpoint (exception: data tables with many columns)
- All content must fit within its container bounds
- Images and media must scale to fit their container (max-width: 100%, height: auto)
- Long URLs or strings must wrap or truncate — never overflow their container

**Text Truncation Strategy**:

| Context | Treatment |
|---------|-----------|
| Single-line labels | Ellipsis truncation |
| Multi-line descriptions | Line clamp (2-3 lines) |
| User-generated content | Word wrap |
| Code/URLs | Horizontal scroll within container, or break-all |

**Responsive Media**:
- All images: max-width 100%, height auto
- Videos/embeds: use aspect-ratio containers (e.g. 16:9)
- Never set fixed pixel widths on media elements

**Anti-Patterns**:

| Don't | Why |
|-------|-----|
| Fixed pixel widths on containers | Causes overflow on smaller screens |
| `overflow: hidden` to hide layout bugs | Masks the problem, content is lost |
| Horizontal scroll on non-tabular content | Poor mobile experience |
| Unbounded text without max-width | Unreadable lines on wide screens |

---

## Page Layout Patterns

**Header / Content / Footer** (default for most pages):
- Full-height page with sticky header
- Content area centred with max-width container
- Footer pushed to bottom of viewport

**Sidebar + Content** (dashboards, settings):
- Fixed-width sidebar (approx 256px), hidden on mobile
- Content area fills remaining width with max-width container
- Sidebar collapses to hamburger menu on mobile

**Dashboard Grid** (cards, metrics):
- Responsive card grid: 1 column (mobile) → 2 columns (tablet) → 3 columns (desktop)
- Consistent gap between cards (24px)
- Cards have equal height within each row

**When to Use Which**:

| Layout | Use For |
|--------|---------|
| Header/Content/Footer | Marketing pages, simple apps, forms |
| Sidebar + Content | Admin panels, settings, documentation |
| Dashboard Grid | Metrics, overview pages, card-based content |
| Full-width (no sidebar) | Landing pages, authentication screens |

**Placement Rules**:
- Primary actions: top-right of content area or bottom of forms
- Navigation: left sidebar (desktop) or top bar (mobile)
- Status/alerts: top of content area, full width of container
- Floating actions (FAB): bottom-right, only one per page

---

## Z-index / Layering Strategy

**Named Scale** (must use these values, never arbitrary z-index):

| Layer | z-index | Usage |
|-------|---------|-------|
| base | 0 | Default page content |
| raised | 10 | Cards with elevation, raised elements |
| dropdown | 20 | Dropdown menus, popovers |
| sticky | 30 | Sticky headers, fixed sidebars |
| modal-backdrop | 40 | Modal overlay/backdrop |
| modal | 50 | Modal content |
| toast | 60 | Toast notifications |
| tooltip | 70 | Tooltips (must be above everything) |

**Rules**:
- Never use arbitrary z-index values outside this scale
- Modals must include a backdrop that prevents interaction with content below
- Tooltips must render above all other layers
- Sticky elements must not obscure modal or toast content
- When stacking within a layer, use increments of 1 (e.g. 31, 32)

---

## Empty, Loading & Error States

**Every data-driven view must handle all three states.** Never show a blank screen.

**Loading States**:

| Context | Treatment |
|---------|-----------|
| Full page | Skeleton screen preserving layout structure |
| Data table | Skeleton rows matching expected column widths |
| Card grid | Skeleton cards matching grid layout |
| Inline data | Spinner or shimmer within container, preserve dimensions |
| Button action | Spinner inside button, disable button, preserve button width |

**Empty States**:
- Centre vertically and horizontally in the content area
- Include: icon or illustration + descriptive message + primary action
- Message should explain what will appear and how to populate it
- Example: "No projects yet. Create your first project to get started." + [Create Project] button
- Never show an empty table with just headers

**Error States**:

| Context | Treatment |
|---------|-----------|
| Full page | Error message + retry action + link to home |
| Component | Inline error with retry, preserve surrounding layout |
| Form field | Red border + error message below field (see Component Patterns §Forms) |
| Network error | Toast notification with retry action |

**Rules**:
- Loading skeletons must match the layout they replace (same widths, heights, grid)
- Never show a spinner without context — always indicate what is loading
- Error messages must be actionable — include a retry button or next step
- Preserve page structure during loading — no layout shift when data arrives

---

## Dark Mode

**Strategy**: Use CSS custom properties and semantic colour tokens. Define surfaces, text, and borders as abstract tokens that resolve differently per theme.

**Colour Adjustments** (not simple inversion):

| Element | Light Mode | Dark Mode |
|---------|------------|-----------|
| Backgrounds | White/light grey | Dark grey (not pure black) |
| Text | Dark grey (#1a1a2e) | Light grey (#e0e0e0) |
| Borders | Light grey | Subtle dark grey |
| Shadows | Visible, subtle | Reduced or removed |
| Accent colours | Full saturation | Slightly desaturated |

**Rules**:
- Never use pure black (`#000`) backgrounds — use dark grey (`#1a1a2e` or similar)
- Maintain WCAG AA contrast ratios in both modes (see Colour & Accessibility)
- Shadows should be reduced or removed in dark mode (they are less visible and can look muddy)
- Test both modes at every breakpoint — dark mode bugs often hide in responsive views
- Use semantic colour tokens (e.g. `surface-primary`, `text-default`) rather than raw colour values
- All colour references should go through tokens — never hardcode hex values in components

**Anti-Patterns**:

| Don't | Why |
|-------|-----|
| Invert all colours | Creates jarring, unnatural appearance |
| Reduce contrast in dark mode | Accessibility failure |
| Forget to style shadows/borders | Looks broken in dark mode |
| Use transparent overlays without testing both modes | Overlay may be invisible in one mode |

---

## Typography

**Scale** (Consistent rhythm):
```
xs: 12px    sm: 14px    base: 16px
lg: 18px    xl: 20px    2xl: 24px
3xl: 30px   4xl: 36px
```

**Line Height**:
- Body text: 1.5 (150%)
- Headings: 1.2-1.3 (120-130%)
- UI labels: 1.25 (125%)

**Readability**:
- 45-75 characters per line optimal
- Left-align body text (avoid justified)
- Sufficient paragraph spacing (1em minimum)

---

## Animation & Motion

**Principles**:
- Purposeful: Guides attention or provides feedback
- Quick: 150-300ms for UI, 300-500ms for page transitions
- Eased: Use ease-out for entering, ease-in for exiting
- Reducible: Respect `prefers-reduced-motion`

**When to Animate**:
- State changes (hover, focus, toggle)
- Loading/progress indication
- Drawing attention to important updates
- Smooth transitions between views

**When NOT to Animate**:
- Critical error messages (show immediately)
- High-frequency updates (avoid visual noise)
- User-initiated navigation (keep fast)

---

## Component Patterns

**Cards**:
- Consistent padding (16-24px)
- Subtle shadow or border for separation
- Clear visual hierarchy within card
- Interactive cards: hover state, cursor pointer

**Forms**:
- Label above input (not placeholder as label)
- Error messages below field, not in tooltip
- Group related fields visually
- Clear required field indicators

**Tables**:
- Zebra striping OR borders (not both)
- Sticky headers for long lists
- Sortable columns: clear indicator of sort state
- Responsive: horizontal scroll or card layout on mobile

---

## Anti-Patterns (Forbidden)

| Don't | Why |
|-------|-----|
| Text over busy images without overlay | Poor contrast, unreadable |
| Pure black (#000) on pure white (#FFF) | Too harsh, causes eye strain |
| Relying on colour alone | Accessibility failure |
| Hiding critical info in tooltips | May not be discovered |
| Disabled buttons without explanation | User doesn't know why |
| Infinite scroll without position indicator | User loses context |
| Auto-playing animations/videos | Disruptive, accessibility issue |
| Small touch targets on mobile | Frustrating, unusable |

---

## Tools & Validation

**Contrast Checkers**:
- WebAIM Contrast Checker
- Figma A11y plugins
- Chrome DevTools colour picker

**Colour Blindness Testing**:
- Sim Daltonism (macOS)
- Colorblindly (Chrome extension)

**Design Token Management**:
- Tokens Studio (Figma)
- Style Dictionary (code export)

---

## Sources

- [Laws of UX](https://lawsofux.com/)
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [Nielsen Norman Group - Tooltip Guidelines](https://www.nngroup.com/articles/tooltip-guidelines/)
- [WebAIM - Contrast and Colour Accessibility](https://webaim.org/articles/contrast/)
- [Figma UI Design Principles](https://www.figma.com/resource-library/ui-design-principles/)
