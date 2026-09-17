# Interstitials

Reference directory for interstitial types used during multi-part book assembly.

These files serve as specifications and templates for interstitial dividers. Interstitials are generated inline by `typst/scripts/build.py` (`_generate_book_typ()`) using template functions exposed by the active brand pack (`typst/brands/*.typ`).

---

## Available Interstitial Styles

| Style | Template Function | Description |
|-------|-------------------|-------------|
| `part-divider` (default) | `brand-part-divider` | Branded separator page displaying Part number, title, and optional embedded mini-TOC. |
| `contents` | `brand-contents` | Styled table of contents page. |

---

## Usage in `build.yaml`

When defining a book compilation in `build.yaml`, inject interstitials between document parts:

```yaml
books:
  rhythm-of-delivery-book:
    title: "The Rhythm of Delivery"
    subtitle: "The Four Types of Work"
    date: "September 2026"
    output: build/pdf/rhythm-of-delivery.pdf
    parts:
      - type: interstitial
        params:
          style: contents
          depth: 2

      - type: interstitial
        params:
          style: part-divider
          label: "Part 1"
          title: "The Four Types of Work"
          contents: true
          depth: 2

      - type: document
        doc: four-types-overview

      - type: interstitial
        params:
          style: part-divider
          label: "Part 2"
          title: "Systems Thinking and Flow"
          contents: true
          depth: 2
```

---

## Brand Integration

Each brand theme (`neutral.typ`, `mindrocket.typ`, `plandek.typ`) implements its own visual styling for dividers (background tone, typography, and accent rules), ensuring consistent appearance across all compiled outputs.
