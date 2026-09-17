// ─────────────────────────────────────────────────────────────────────────────
// Plandek brand pack (`typst/brands/plandek.typ`)
//
// Exports the `plandek-doc` template function.  Each document wrapper calls:
//
//   #show: plandek-doc.with(
//     title: "New DevX\nVision",
//     subtitle: "The Agentic Software Development Lifecycle",
//     date: "February 2026",
//   )
//
// The title string may contain "\n" to produce a two-line cover heading.
//
// Also exports `plandek-part-divider(label, title)` for book interstitials.
// ─────────────────────────────────────────────────────────────────────────────

#import "@preview/cetz:0.3.4": canvas, draw

// ── Brand colours ─────────────────────────────────────────────────────────────
#let plandek-orange = rgb("#E85D1A")
#let plandek-black  = rgb("#0D0D0D")
#let plandek-white  = rgb("#FFFFFF")
#let plandek-gray   = rgb("#888888")
#let plandek-dark   = rgb("#1A1A1A")
#let plandek-light  = rgb("#F7F7F7")

// ── Geometric network panel (cover right-hand column) ─────────────────────────
#let _W = 94.5
#let _H = 297.0

#let _nodes = (
  ( 8.0, 285.0), (28.0, 290.0), (48.0, 283.0), (68.0, 288.0), (88.0, 281.0),
  (15.0, 272.0), (38.0, 275.0), (58.0, 268.0), (80.0, 274.0), (92.0, 265.0),
  ( 5.0, 255.0), (25.0, 260.0), (46.0, 252.0), (66.0, 258.0), (85.0, 250.0),
  (18.0, 240.0), (40.0, 244.0), (60.0, 237.0), (78.0, 243.0), (93.0, 236.0),
  ( 8.0, 220.0), (30.0, 225.0), (50.0, 218.0), (70.0, 223.0), (90.0, 215.0),
  (20.0, 205.0), (42.0, 210.0), (62.0, 203.0), (82.0, 208.0),
  ( 5.0, 188.0), (28.0, 193.0), (48.0, 186.0), (68.0, 191.0), (88.0, 183.0),
  (15.0, 170.0), (38.0, 175.0), (58.0, 168.0), (78.0, 173.0), (94.0, 166.0),
  ( 8.0, 152.0), (30.0, 157.0), (50.0, 150.0), (70.0, 155.0), (90.0, 148.0),
  (20.0, 135.0), (42.0, 140.0), (62.0, 133.0), (82.0, 138.0),
  ( 5.0, 118.0), (25.0, 123.0), (46.0, 115.0), (66.0, 120.0), (86.0, 113.0),
  (15.0, 100.0), (38.0, 105.0), (58.0,  98.0), (80.0, 103.0), (93.0,  95.0),
  ( 8.0,  82.0), (30.0,  87.0), (50.0,  80.0), (70.0,  85.0), (90.0,  78.0),
  (20.0,  65.0), (42.0,  70.0), (62.0,  63.0), (82.0,  68.0),
  (10.0,  48.0), (32.0,  52.0), (52.0,  45.0), (72.0,  50.0), (90.0,  43.0),
  (22.0,  30.0), (44.0,  34.0), (64.0,  27.0), (84.0,  32.0),
  ( 8.0,  14.0), (30.0,  18.0), (50.0,  12.0), (70.0,  16.0), (90.0,   9.0),
  (35.0, 248.0), (75.0, 230.0), (55.0, 195.0), (22.0, 178.0), (88.0, 160.0),
  (45.0, 145.0), (10.0, 128.0), (78.0, 110.0), (38.0,  90.0), (65.0,  55.0),
)

#let _edges = (
  (0,1),(1,2),(2,3),(3,4),
  (0,5),(1,5),(1,6),(2,6),(2,7),(3,7),(3,8),(4,8),(4,9),
  (5,6),(6,7),(7,8),(8,9),
  (5,10),(6,10),(6,11),(7,11),(7,12),(8,12),(8,13),(9,13),(9,14),
  (10,11),(11,12),(12,13),(13,14),
  (10,15),(11,15),(11,16),(12,16),(12,17),(13,17),(13,18),(14,18),(14,19),
  (15,16),(16,17),(17,18),(18,19),
  (15,20),(16,20),(16,21),(17,21),(17,22),(18,22),(18,23),(19,23),(19,24),
  (20,21),(21,22),(22,23),(23,24),
  (20,25),(21,25),(21,26),(22,26),(22,27),(23,27),(23,28),(24,28),
  (25,26),(26,27),(27,28),
  (25,29),(26,29),(26,30),(27,30),(27,31),(28,31),(28,32),(29,33),
  (29,30),(30,31),(31,32),(32,33),
  (29,34),(30,34),(30,35),(31,35),(31,36),(32,36),(32,37),(33,37),(33,38),
  (34,35),(35,36),(36,37),(37,38),
  (34,39),(35,39),(35,40),(36,40),(36,41),(37,41),(37,42),(38,42),(38,43),
  (39,40),(40,41),(41,42),(42,43),
  (39,44),(40,44),(40,45),(41,45),(41,46),(42,46),(42,47),(43,47),
  (44,45),(45,46),(46,47),
  (44,48),(45,48),(45,49),(46,49),(46,50),(47,50),(47,51),
  (48,49),(49,50),(50,51),
  (48,52),(49,52),(49,53),(50,53),(50,54),(51,54),
  (52,53),(53,54),
  (52,55),(53,55),(53,56),(54,56),(54,57),(55,58),(56,58),(57,58),
  (55,56),(56,57),
  (1,7),(2,8),(6,12),(7,13),(11,17),(12,18),(16,22),(17,23),
  (21,27),(22,28),(26,31),(30,36),(35,41),(40,46),(45,50),(49,54),
  (0,6),(3,9),(5,11),(8,14),(10,16),(13,19),(15,21),(18,24),
  (20,26),(23,28),(25,30),(27,32),(29,35),(31,37),(34,40),(36,42),
  (59,11),(59,12),(59,16),(60,22),(60,23),(60,27),
  (61,26),(61,27),(61,31),(62,15),(62,16),(62,20),
  (63,32),(63,33),(63,38),(64,39),(64,40),(64,44),
  (65,41),(65,42),(65,46),(66,10),(66,11),(66,15),
  (67,47),(67,43),(67,42),(68,35),(68,36),(68,40),
)

#let _network-panel = canvas(length: 1mm, {
  draw.rect((0,0),(_W, _H), fill: rgb("#100500"), stroke: none)
  let cx = _W * 0.62
  let cy = _H * 0.52
  for r in (42.0, 32.0, 23.0, 16.0, 10.0, 5.0) {
    let alpha = int(255.0 * (1.0 - r / 44.0) * 0.18)
    draw.circle((cx, cy), radius: r, fill: rgb(70, 15, 0, alpha), stroke: none)
  }
  for (i, j) in _edges {
    let a = _nodes.at(i)
    let b = _nodes.at(j)
    draw.line((a.at(0), a.at(1)), (b.at(0), b.at(1)),
      stroke: (paint: plandek-orange.transparentize(80%), thickness: 0.4pt))
  }
  for (idx, n) in _nodes.enumerate() {
    let r = if calc.rem(idx, 7) == 0 { 1.6 } else { 1.0 }
    draw.circle((n.at(0), n.at(1)), radius: r,
      fill: plandek-orange.transparentize(78%), stroke: none)
  }
  for (idx, n) in _nodes.enumerate() {
    let r = if calc.rem(idx, 7) == 0 { 0.9 } else { 0.55 }
    draw.circle((n.at(0), n.at(1)), radius: r,
      fill: plandek-orange, stroke: none)
  }
})

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
        #image("/docs/assets/plandek-logo.svg", width: 55%)
        #v(0.4em)
        #text(size: 8.5pt, fill: plandek-gray)[Empowering teams to deliver software better]
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
    image("/docs/assets/plandek-logo.svg", height: 0.5cm),
    text(size: 7pt, fill: plandek-gray)[Copyright © Plandek. All rights reserved.],
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

  // Inline code from Markdown (`…`) should match body size so prose beside
  // bold terms and parentheses does not read as a smaller “band”.
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

  // Figure captions: match body size (defaults read smaller next to headings).
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
// A branded closing page in the RACER-deck style:
// dark background, logo top-left, "Get in touch" contact in orange centre,
// QR code top-right, network panel bottom-right, copyright bottom-left.
//
// contact: e.g. "wlytle@plandek.com"
// qr_label: caption below the QR code
#let plandek-endpiece(
  contact:   "wlytle@plandek.com",
  qr_label:  "Learn more at plandek.com",
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
      // ── Left column: text + QR code ──
      block(width: 100%, height: 100%, inset: (x: 2.4cm, y: 2.2cm))[
        #set text(fill: plandek-white, font: "Outfit")
        #image("/docs/assets/plandek-logo.svg", width: 55%)
        #v(1fr)
        #text(size: 28pt, weight: "bold")[Thank you]
        #v(0.8em)
        #text(size: 12pt, fill: plandek-gray)[
          #text(fill: plandek-orange, weight: "semibold")[Get in touch: ]#contact
        ]
        #v(0.8em)
        #box(fill: white, inset: 6pt, radius: 4pt)[
          #image("/docs/assets/plandek-qr.png", width: 3.2cm)
        ]
        #v(0.3em)
        #text(size: 7.5pt, fill: plandek-gray)[#qr_label]
        #v(1fr)
        #text(size: 7.5pt, fill: plandek-gray)[
          © Plandek #datetime.today().year(). All rights reserved.
        ]
      ],
      // ── Right column: network panel ──
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
        #image("/docs/assets/plandek-logo.svg", width: 55%)
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
// Renders a dark-background closing page with the network panel, logo,
// QR code, and free-form body content (bio, about Plandek, contact).
// body: Typst content block — rendered in white on the left column
// contact:   contact line shown in orange below the body
// qr_label:  caption below the QR code
#let plandek-endpage(
  contact:  "wlytle@plandek.com",
  qr_label: "Learn more at plandek.com",
  body,
) = {
  pagebreak()
  page(
    paper: "a4",
    margin: 0pt,
    footer: none,
    background: rect(width: 100%, height: 100%, fill: plandek-black),
  )[
    #grid(
      columns: (58%, 42%),
      rows: (100%),
      block(width: 100%, height: 100%, inset: (x: 2.4cm, y: 2.2cm))[
        #set text(fill: plandek-white, font: "Outfit", size: 9pt)
        #set par(justify: false, leading: 0.65em, spacing: 1.4em)
        #set heading(outlined: false)
        #show heading.where(level: 1): it => {
          v(0.6em)
          text(size: 12pt, weight: "bold", fill: plandek-white)[#it.body]
          v(0.3em)
        }
        #show heading.where(level: 2): it => {
          v(0.6em)
          text(size: 11pt, weight: "bold", fill: plandek-white)[#it.body]
          v(0.3em)
        }
        #image("/docs/assets/plandek-logo.svg", width: 50%)
        #v(0.8em)
        #body
        #v(1fr)
        #text(size: 8pt, fill: plandek-gray)[
          #text(fill: plandek-orange, weight: "semibold")[Get in touch: ]#contact
        ]
        #v(0.5em)
        #box(fill: white, inset: 5pt, radius: 3pt)[
          #image("/docs/assets/plandek-qr.png", width: 2.8cm)
        ]
        #v(0.3em)
        #text(size: 7pt, fill: plandek-gray)[#qr_label]
        #v(0.5em)
        #text(size: 7pt, fill: plandek-gray)[
          © Plandek #datetime.today().year(). All rights reserved.
        ]
      ],
      block(width: 100%, height: 100%, clip: true)[
        #_network-panel
      ],
    )
  ]
}
