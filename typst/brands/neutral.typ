// ─────────────────────────────────────────────────────────────────────────────
// Neutral brand pack (default PDF theme)
//
// Same public API as `plandek.typ` (`plandek-doc`, `plandek-endpiece`, …) so the
// build driver can swap `#import` paths.  No customer logos, CETZ panel, or QR.
// ─────────────────────────────────────────────────────────────────────────────

// ── Palette (variable names match Plandek pack for shared body rules) ─────────
#let plandek-orange = rgb("#2563EB")
#let plandek-black  = rgb("#0f172a")
#let plandek-white  = rgb("#FFFFFF")
#let plandek-gray   = rgb("#64748b")
#let plandek-dark   = rgb("#1e293b")
#let plandek-light  = rgb("#f1f5f9")

// ── Right-hand column on cover / dividers (flat panel, no CETZ) ──────────────
#let _network-panel = block(width: 100%, height: 100%, inset: 0pt)[
  #rect(width: 100%, height: 100%, fill: rgb("#e2e8f0"), stroke: none)
]

// ── Shared cover layout ───────────────────────────────────────────────────────
#let _cover-page(title, subtitle, date) = {
  let title-parts = title.split("\n")
  page(
    paper: "a4",
    margin: 0pt,
    background: rect(width: 100%, height: 100%, fill: plandek-black),
  )[
    #grid(
      columns: (55%, 45%),
      rows: (100%),
      block(width: 100%, height: 100%, inset: (x: 2.4cm, y: 2.2cm))[
        #set text(fill: plandek-white, font: "Outfit")
        #text(size: 10pt, weight: "semibold")[Neutral PDF theme]
        #v(1fr)
        #text(size: 26pt, weight: "bold", hyphenate: false)[
          #title-parts.join[\
          ]
        ]
        #if subtitle != "" [
          #v(0.9em)
          #text(size: 14pt, fill: plandek-orange)[#subtitle]
        ]
        #v(1fr)
        #if date != "" [
          #text(size: 10pt)[#date]
        ]
      ],
      block(width: 100%, height: 100%, clip: true)[
        #_network-panel
      ],
    )
  ]
}

// ── Footer ────────────────────────────────────────────────────────────────────
#let _footer(page-num) = {
  grid(
    columns: (auto, 1fr, auto),
    align: (left + horizon, center + horizon, right + horizon),
    gutter: 0pt,
    box(width: 0.6cm),
    text(size: 7pt, fill: plandek-gray)[Draft PDF · generic typesetting],
    text(size: 7pt, fill: plandek-gray)[#page-num],
  )
}

// ── Body style rules (shared by doc template and book assembly) ───────────────
#let apply-body-styles(body) = {
  set text(font: "Outfit", size: 10.5pt, fill: plandek-dark, lang: "en")
  set par(justify: true, leading: 0.65em, spacing: 1.1em)
  set page(
    paper: "a4",
    margin: (top: 2cm, bottom: 2cm, left: 2.2cm, right: 2.2cm),
    footer: context _footer(str(counter(page).get().first())),
  )
  set heading(numbering: none)

  show heading.where(level: 1): it => {
    pagebreak(weak: true)
    v(0.5em)
    text(size: 20pt, weight: "bold", fill: plandek-dark)[#it.body]
    v(0.3em)
    line(length: 100%, stroke: 2pt + plandek-orange)
    v(0.8em)
  }
  show heading.where(level: 2): it => {
    pagebreak(weak: true)
    block(breakable: false)[
      #v(0.8em)
      #text(size: 15pt, weight: "bold", fill: plandek-dark)[#it.body]
      #v(0.4em)
    ]
  }
  show heading.where(level: 3): it => {
    block(breakable: false, sticky: true)[
      #v(0.5em)
      #text(size: 12.5pt, weight: "bold", fill: plandek-dark)[#it.body]
      #v(0.2em)
    ]
  }
  show heading.where(level: 4): it => {
    block(breakable: false, sticky: true)[
      #v(0.4em)
      #text(size: 11.5pt, weight: "bold", fill: plandek-dark)[#it.body]
      #v(0.15em)
    ]
  }
  show heading.where(level: 5): it => {
    block(breakable: false, sticky: true)[
      #v(0.3em)
      #text(size: 11pt, weight: "bold", fill: plandek-dark)[#it.body]
      #v(0.1em)
    ]
  }

  set list(marker: text(fill: plandek-orange)[▸], indent: 1em)
  set enum(numbering: n => text(fill: plandek-orange)[#n.], indent: 1em)
  show link: it => text(fill: plandek-orange, it)

  show raw.where(block: false): set text(font: "Courier New", size: 10pt)

  show raw.where(block: true): it => block(
    fill: plandek-light, inset: 10pt, radius: 4pt, width: 100%,
  )[#set text(font: "Courier New", size: 8.5pt); #it]

  // ── Table styling ──────────────────────────────────────────────────────────
  set table(
    inset: (x: 0.6em, y: 0.5em),
    fill: (_, y) => if y == 0 { plandek-light },
    stroke: (_, y) => (
      bottom: if y == 0 { 1.2pt + plandek-orange } else { 0.4pt + rgb("#E0E0E0") },
    ),
  )
  show table: set text(size: 10pt)
  show table: set par(justify: false, leading: 0.55em)
  show table.cell.where(y: 0): set text(
    weight: "semibold", size: 10.5pt, fill: plandek-dark,
  )
  show table: set table.cell(align: left)

  // Allow table figures to break across pages (pandoc wraps all tables in
  // #figure which is non-breakable by default — large tables overflow the
  // footer or leave excessive whitespace on the previous page).
  show figure.where(kind: table): set block(breakable: true)

  show figure.caption: set text(size: 10.5pt, fill: plandek-dark)

  // Figure captions: breathing room between caption and following text
  show figure: it => {
    it
    v(1.4em)
  }

  body
}

// ── Public: single-document template ─────────────────────────────────────────
// Usage (in a {doc}-book.typ wrapper):
//
//   #show: plandek-doc.with(
//     title:    "New DevX\nVision",
//     subtitle: "The Agentic Software Development Lifecycle",
//     date:     "February 2026",
//   )
//   #include "../build/typst/vision-content.typ"
//
#let plandek-doc(
  title: "",
  subtitle: "",
  date: "",
  cover-style: "split-mesh",
  cover-seed: 0,
  body,
) = {
  _cover-page(title, subtitle, date)

  counter(page).update(1)
  show: apply-body-styles

  body
}

// ── Public: endpiece (last page) ─────────────────────────────────────────────
// Simple closing page: dark background, thank-you, optional contact, flat panel.
//
// contact / qr_label kept for API parity with the Plandek pack (build driver).
#let plandek-endpiece(
  contact:   "",
  qr_label:  "",
) = {
  pagebreak()
  page(
    paper: "a4",
    margin: 0pt,
    footer: none,
    background: rect(width: 100%, height: 100%, fill: plandek-black),
  )[
    #grid(
      columns: (55%, 45%),
      rows: (100%),
      block(width: 100%, height: 100%, inset: (x: 2.4cm, y: 2.2cm))[
        #set text(fill: plandek-white, font: "Outfit")
        #v(0.5em)
        #text(size: 28pt, weight: "bold")[Thank you]
        #v(0.8em)
        #if contact != "" [
          #text(size: 12pt, fill: plandek-gray)[
            #text(fill: plandek-orange, weight: "semibold")[Contact: ]#contact
          ]
        ]
        #v(1fr)
        #text(size: 7.5pt, fill: plandek-gray)[
          Neutral theme · #datetime.today().display()
        ]
      ],
      block(width: 100%, height: 100%, clip: true)[
        #_network-panel
      ],
    )
  ]
}

// ── Part-scoped contents infrastructure ──────────────────────────────────────
// Each part interstitial places a <plandek-part-N> label immediately before
// the first #include of that part.  The contents page for part N uses
// outline(target: selector(<plandek-part-N>).after() & heading) so only
// headings within that part appear.  Part boundaries are set via metadata
// labels injected by plandek-part-divider and plandek-contents-for.

// ── Public: global contents page (for single-doc builds) ─────────────────────
// Call immediately after the cover, before the first #include.
// depth: maximum heading depth shown (default: 2)
#let plandek-contents(depth: 2) = {
  page(
    paper: "a4",
    margin: (top: 2.5cm, bottom: 2cm, left: 2.2cm, right: 2.2cm),
    footer: none,
  )[
    #set text(font: "Outfit", fill: plandek-dark, lang: "en")
    #set par(justify: false)
    #text(size: 20pt, weight: "bold")[Contents]
    #v(0.3em)
    #line(length: 100%, stroke: 2pt + plandek-orange)
    #v(1.2em)
    #outline(
      title: none,
      depth: depth,
      indent: auto,
    )
  ]
}

// ── Public: per-part contents page ───────────────────────────────────────────
// Renders a styled ToC page scoped to headings between two sentinel labels.
// Uses context + query to build a manual list (outline(target: compound-selector)
// is not supported in Typst 0.14 — & intersection is invalid in that position).
//
// part-start-label: Typst label name for the start of this part (string)
// part-end-label:   Typst label name for the start of the next part (string),
//                   or "" to scope to end of document
// heading-label:    human-readable part heading shown above the list
// depth:            max heading depth to include (1-based, default: 2)
#let plandek-part-contents(
  part-start-label: "",
  part-end-label: "",
  heading-label: "Contents",
  depth: 2,
) = {
  page(
    paper: "a4",
    margin: (top: 2.5cm, bottom: 2cm, left: 2.2cm, right: 2.2cm),
    footer: none,
  )[
    #set text(font: "Outfit", fill: plandek-dark, lang: "en")
    #set par(justify: false)
    #text(size: 20pt, weight: "bold")[#heading-label]
    #v(0.3em)
    #line(length: 100%, stroke: 2pt + plandek-orange)
    #v(1.2em)
    #context {
      // Locate the start sentinel
      let start-results = query(label(part-start-label))
      if start-results.len() == 0 { return }
      let start-loc = start-results.first().location()

      // Locate the end sentinel (if given)
      let end-loc = none
      if part-end-label != "" {
        let end-results = query(label(part-end-label))
        if end-results.len() > 0 {
          end-loc = end-results.first().location()
        }
      }

      // Query all headings and filter to those between start and end
      let all-headings = query(heading.where(outlined: true))
      let part-headings = all-headings.filter(h => {
        let loc = h.location()
        let after-start = loc.position().page > start-loc.position().page or (
          loc.position().page == start-loc.position().page and
          loc.position().y >= start-loc.position().y
        )
        let before-end = if end-loc == none { true } else {
          loc.position().page < end-loc.position().page or (
            loc.position().page == end-loc.position().page and
            loc.position().y < end-loc.position().y
          )
        }
        after-start and before-end and h.level <= depth
      })

      // Render the list of headings with page numbers
      for h in part-headings {
        let indent = (h.level - 1) * 1.2em
        let pg = counter(page).at(h.location()).first()
        box(width: 100%,
          grid(
            columns: (indent, 1fr, auto),
            [],
            text(
              size: if h.level == 1 { 10.5pt } else { 9.5pt },
              weight: if h.level == 1 { "semibold" } else { "regular" },
              fill: if h.level == 1 { plandek-dark } else { rgb("#444444") },
            )[#h.body],
            text(size: 9pt, fill: plandek-gray)[#pg],
          )
        )
        v(if h.level == 1 { 0.5em } else { 0.2em })
      }
    }
  ]
}

// ── Public: interstitial part-divider page ────────────────────────────────────
// Used between parts in a multi-document book.
// label:            short descriptor, e.g. "Part 2"
// title:            section name,     e.g. "The Journey"
// contents:         when true, append a per-part contents page after the divider
// part-start-label: sentinel label placed before the part's content (required
//                   when contents: true) — must match the label placed in the
//                   generated book .typ immediately before #include
// part-end-label:   label at the start of the NEXT part (or "" for last part)
// depth:            outline depth for the per-part contents (default: 2)
#let plandek-part-divider(
  label: "",
  title: "",
  contents: false,
  part-start-label: "",
  part-end-label: "",
  depth: 2,
) = {
  page(
    paper: "a4",
    margin: 0pt,
    footer: none,
    background: rect(width: 100%, height: 100%, fill: plandek-black),
  )[
    #set par(justify: false)
    #grid(
      columns: (55%, 45%),
      rows: (100%),
      block(width: 100%, height: 100%, inset: (x: 2.4cm, y: 2.2cm))[
        #set text(fill: plandek-white, font: "Outfit")
        #text(size: 10pt, weight: "semibold")[Part]
        #v(1fr)
        #text(size: 11pt, fill: plandek-gray)[#label]
        #v(0.4em)
        #text(size: 32pt, weight: "bold", hyphenate: false)[#title]
        #v(1fr)
      ],
      block(width: 100%, height: 100%, clip: true)[
        #_network-panel
      ],
    )
  ]
  if contents {
    plandek-part-contents(
      part-start-label: part-start-label,
      part-end-label: part-end-label,
      heading-label: title + " — Contents",
      depth: depth,
    )
  }
}

// ── Public: end-page with authored body text ──────────────────────────────────
// Light closing page with body copy and optional contact (no logo / QR).
#let plandek-endpage(
  contact:  "",
  qr_label: "",
  body,
) = {
  pagebreak()
  page(
    paper: "a4",
    margin: (top: 2cm, bottom: 2cm, left: 2.2cm, right: 2.2cm),
    footer: none,
  )[
    #set text(fill: plandek-dark, font: "Outfit", size: 9pt)
    #set par(justify: false, leading: 0.65em, spacing: 1.4em)
    #set heading(outlined: false)
    #show heading.where(level: 1): it => {
      v(0.6em)
      text(size: 12pt, weight: "bold", fill: plandek-dark)[#it.body]
      v(0.3em)
    }
    #show heading.where(level: 2): it => {
      v(0.6em)
      text(size: 11pt, weight: "bold", fill: plandek-dark)[#it.body]
      v(0.3em)
    }
    #body
    #v(1.2em)
    #if contact != "" [
      #text(size: 8pt, fill: plandek-gray)[
        #text(fill: plandek-orange, weight: "semibold")[Contact: ]#contact
      ]
    ]
    #if qr_label != "" [
      #v(0.4em)
      #text(size: 7pt, fill: plandek-gray)[#qr_label]
    ]
    #v(0.8em)
    #line(length: 40%, stroke: 1pt + plandek-orange)
    #v(0.4em)
    #text(size: 7pt, fill: plandek-gray)[Neutral theme · end page]
  ]
}
