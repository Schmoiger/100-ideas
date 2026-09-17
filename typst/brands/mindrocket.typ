// Mind Rocket brand pack (`typst/brands/mindrocket.typ`)
//
// Palette derived from sampling `docs/ref/CV of Avi Sinharay.pdf` (dominant
// accent ≈ #69ABB9 on white). Layout mirrors `plandek.typ`: split cover,
// two-column endpiece, part dividers, shared book hooks.
//
// Logos: `docs/assets/mindrocket/icon.svg` (32×32 trace of ref webp), `logo.svg` (vector wordmark)
// (closing pages, right column). Assets live under `docs/assets/mindrocket/`.
//
// Exports the same symbol names as `plandek.typ` so `typst/scripts/build.py` does
// not need per-brand import lists.

// ── Brand colours (CV-inspired) ─────────────────────────────────────────────
#let mr-accent = rgb("#69ABB9")
#let mr-accent-soft = rgb("#9DC8D1")
#let mr-cover = rgb("#0B1F24")
#let mr-cover-mid = rgb("#143842")
#let mr-white = rgb("#FFFFFF")
#let mr-gray = rgb("#8CA8AE")
#let mr-muted = rgb("#5A7A82")
#let mr-body = rgb("#1C3035")
#let mr-light = rgb("#EEF5F6")

// ── Right-hand visual column (gradient + rich geometry) ───────────────────
// Layered: soft washes, dual sonar foci, logarithmic-ish spiral arms, moiré
// line fields, cubic “current” ribbons, and a sparse starfield — still typst-only.
#let _mr-geo-mesh(seed: 0) = {
  let s = calc.rem(calc.abs(seed), 100)
  let s-rot = s * 6deg
  let ink = rgb("#EAF8FC")
  let mist = rgb("#B6E8F4")
  let haze = rgb("#7EBCC8")
  block(width: 100%, height: 100%, clip: true)[
    // ── Ambient washes ──────────────────────────────────────────────────────
    #place(center + horizon, dx: 22%, dy: -18%, rotate(-22deg + s-rot, ellipse(
      width: 62%,
      height: 26%,
      fill: ink.transparentize(94%),
      stroke: none,
    )))
    #place(left + top, dx: -18%, dy: 24%, rotate(41deg - s-rot, ellipse(
      width: 58%,
      height: 48%,
      fill: mist.transparentize(93%),
      stroke: none,
    )))
    #place(right + top, dx: 4%, dy: 4%, rotate(8deg + s-rot * 0.5, ellipse(
      width: 44%,
      height: 22%,
      fill: mr-accent-soft.transparentize(92%),
      stroke: none,
    )))
    #place(center + bottom, dx: -8%, dy: 6%, rotate(-55deg + s-rot, ellipse(
      width: 48%,
      height: 36%,
      fill: haze.transparentize(94%),
      stroke: none,
    )))
    // ── Sonar rings: bottom-right + smaller top-left ───────────────────────
    #let ring-scale = 4.2mm + calc.rem(s, 4) * 0.25mm
    #for i in range(2, 26) [
      #place(
        right + bottom,
        circle(
          radius: i * ring-scale,
          stroke: (0.32pt + 0.018pt * i) + ink.transparentize(84%),
          fill: none,
        ),
      )
    ]
    #for i in range(2, 14) [
      #place(
        left + top,
        circle(
          radius: i * 3.4mm,
          stroke: (0.28pt + 0.02pt * i) + mist.transparentize(87%),
          fill: none,
        ),
      )
    ]
    // ── Moiré families (three shallow angles) ──────────────────────────────
    #let moire-ang = 11deg + calc.rem(s * 5, 25) * 1deg
    #for k in range(-10, 36) [
      #place(
        top + left,
        dx: k * 4.8%,
        dy: -5%,
        rotate(
          moire-ang,
          line(length: 240mm, stroke: 0.16pt + ink.transparentize(91%)),
        ),
      )
    ]
    #for k in range(-10, 36) [
      #place(
        top + left,
        dx: k * 4.8% + 2.2%,
        dy: -5%,
        rotate(
          -8deg - calc.rem(s * 3, 20) * 1deg,
          line(length: 240mm, stroke: 0.14pt + mist.transparentize(92%)),
        ),
      )
    ]
    #for k in range(-6, 28) [
      #place(
        top + left,
        dx: k * 6.2%,
        dy: 8%,
        rotate(
          43deg + s-rot,
          line(length: 200mm, stroke: 0.12pt + haze.transparentize(93%)),
        ),
      )
    ]
    // ── Spiral arms (filled micro-dots) from both corners ───────────────────
    #for i in range(10, 150) [
      #let th = i * 0.118rad
      #let rr = i * 0.52pt
      #let ang = th + 38deg + s-rot
      #place(
        right + bottom,
        dx: -rr * calc.cos(ang),
        dy: -rr * calc.sin(ang),
        circle(
          radius: 0.55pt + 0.12pt * calc.rem(i, 4),
          fill: ink.transparentize(88%),
          stroke: none,
        ),
      )
    ]
    #for i in range(6, 95) [
      #let th = i * 0.152rad
      #let rr = i * 0.44pt
      #let ang = th + 52deg - s-rot
      #place(
        left + top,
        dx: rr * calc.cos(ang),
        dy: rr * calc.sin(ang),
        circle(
          radius: 0.45pt + 0.1pt * calc.rem(i, 3),
          fill: mist.transparentize(89%),
          stroke: none,
        ),
      )
    ]
    // ── Fourth + fifth moiré (finer interference) ───────────────────────────
    #for k in range(-8, 32) [
      #place(
        top + left,
        dx: k * 5.1% + 1.1%,
        dy: 3%,
        rotate(
          27deg + s-rot * 0.5,
          line(length: 220mm, stroke: 0.11pt + ink.transparentize(93%)),
        ),
      )
    ]
    #for k in range(-6, 26) [
      #place(
        top + left,
        dx: k * 6.5%,
        dy: 18%,
        rotate(
          -21deg - s-rot * 0.5,
          line(length: 190mm, stroke: 0.1pt + mist.transparentize(94%)),
        ),
      )
    ]
    // ── “Wave train”: short staggered dashes along curved guides ───────────
    #for seg in range(0, 36) [
      #let px = 4% + seg * 2.6%
      #let py = 22% + 1.8% * calc.sin(seg * 22deg + s-rot)
      #place(
        top + left,
        dx: px,
        dy: py,
        rotate(
          -18deg + seg * 3deg + s-rot * 0.5,
          line(length: 11mm, stroke: 0.42pt + mr-accent-soft.transparentize(84%)),
        ),
      )
    ]
    #for seg in range(0, 32) [
      #let px = 12% + seg * 2.4%
      #let py = 58% + 1.4% * calc.sin(seg * 25deg + 40deg - s-rot)
      #place(
        top + left,
        dx: px,
        dy: py,
        rotate(
          24deg - seg * 2.4deg - s-rot * 0.5,
          line(length: 9mm, stroke: 0.36pt + haze.transparentize(86%)),
        ),
      )
    ]
    // ── Sparse “constellation” (deterministic radii) ────────────────────────
    #for n in range(0, 55) [
      #let col = calc.rem(n * 17 + 3 + s, 14)
      #let row = calc.rem(n * 11 + 5 + calc.rem(s, 7), 20)
      #place(
        top + left,
        dx: col * 7.2% + 1.5%,
        dy: row * 4.9% + 2%,
        circle(
          radius: 0.65pt + 0.35pt * calc.rem(n * 13, 5),
          fill: ink.transparentize(86%),
          stroke: 0.15pt + mist.transparentize(90%),
        ),
      )
    ]
    // ── Light isometric shards (smaller footprint than old full lattice) ────
    #for row in range(0, 14) [
      #for col in range(0, 10) [
        #place(
          top + left,
          dx: col * 9.5% + if calc.rem(row, 2) == 1 { 4.75% } else { 0% },
          dy: row * 6.8% + 12%,
          rotate(
            30deg + s-rot,
            polygon(
              fill: ink.transparentize(93%),
              stroke: 0.22pt + mist.transparentize(88%),
              (0pt, 0pt),
              (9pt, 0pt),
              (4.5pt, 7.8pt),
            ),
          ),
        )
      ]
    ]
  ]
}

#let _mr-visual-panel(seed: 0) = block(width: 100%, height: 100%, clip: true)[
  #rect(
    width: 100%,
    height: 100%,
    fill: gradient.linear(
      mr-cover,
      mr-cover-mid,
      mr-accent,
      angle: 135deg + calc.rem(seed * 23, 90) * 1deg,
    ),
  )
  #place(top + left, block(width: 100%, height: 100%)[#_mr-geo-mesh(seed: seed)])
]

// Cover / dividers: light blue tile behind icon on dark panels. Body footer: icon only (no tile).
#let _mr-icon-chip = block(
  width: 46%,
  inset: (x: 11pt, y: 9pt),
  radius: 16pt,
  fill: rgb("#B6E8F4"),
  stroke: 0.6pt + rgb("#D4F4FC").transparentize(35%),
)[
  #align(center)[
    #image("/docs/assets/mindrocket/icon.svg", width: 100%)
  ]
]

// ── Cover Style 1: Split Mesh (55/45 split, procedural geometric panel) ───────
#let _cover-split-mesh(title, subtitle, date, seed: 0) = {
  let title-parts = title.split("\n")
  page(
    paper: "a4",
    margin: 0pt,
    background: rect(width: 100%, height: 100%, fill: mr-cover),
  )[
    #grid(
      columns: (55%, 45%),
      rows: (100%),
      block(width: 100%, height: 100%, inset: (x: 2.4cm, y: 2.2cm))[
        #set text(fill: mr-white, font: "Outfit")
        #align(left)[#_mr-icon-chip]
        #v(0.55em)
        #text(size: 8.5pt, fill: mr-gray)[Mind Rocket Services]
        #v(1fr)
        #text(size: 26pt, weight: "bold", hyphenate: false)[
          #title-parts.join[\
          ]
        ]
        #if subtitle != "" [
          #v(0.85em)
          #text(size: 14pt, fill: mr-accent-soft)[#subtitle]
        ]
        #v(1fr)
        #if date != "" [
          #text(size: 10pt, fill: mr-gray)[#date]
        ]
      ],
      block(width: 100%, height: 100%, clip: true)[
        #_mr-visual-panel(seed: seed)
      ],
    )
  ]
}

// ── Cover Style 2: Minimal Editorial (clean accent stripe, high whitespace) ────
#let _cover-minimal(title, subtitle, date, seed: 0) = {
  let title-parts = title.split("\n")
  let s = calc.rem(calc.abs(seed), 100)
  page(
    paper: "a4",
    margin: 0pt,
    background: rect(width: 100%, height: 100%, fill: mr-cover),
  )[
    // Subtle background watermark: sonar rings in bottom-right corner
    #place(right + bottom, dx: 15%, dy: 15%, block(width: 60%, height: 60%, clip: true)[
      #for i in range(1, 16) [
        #place(
          right + bottom,
          circle(
            radius: i * (11mm + calc.rem(s, 4) * 1mm),
            stroke: 0.35pt + mr-accent.transparentize(94%),
            fill: none,
          ),
        )
      ]
      #for k in range(0, 15) [
        #place(
          right + bottom,
          dx: -k * 18mm,
          line(length: 120mm, angle: 90deg, stroke: 0.22pt + mr-accent-soft.transparentize(96%)),
        )
      ]
    ])

    #grid(
      columns: (10pt, 1fr),
      rows: (100%),
      // Left vertical accent stripe
      rect(width: 100%, height: 100%, fill: gradient.linear(mr-accent, mr-accent-soft, angle: 180deg)),
      // Main content block
      block(width: 100%, height: 100%, inset: (top: 3.2cm, bottom: 2.8cm, left: 2.6cm, right: 2.6cm))[
        #set text(fill: mr-white, font: "Outfit")
        #align(left)[#_mr-icon-chip]
        #v(0.6em)
        #text(size: 8.5pt, fill: mr-gray, tracking: 0.12em)[MIND ROCKET SERVICES]
        #v(1.8fr)
        #text(size: 30pt, weight: "bold", hyphenate: false)[
          #title-parts.join[\
          ]
        ]
        #if subtitle != "" [
          #v(0.8em)
          #line(length: 28%, stroke: 1.5pt + mr-accent)
          #v(0.8em)
          #text(size: 15pt, fill: mr-accent-soft, weight: "medium")[#subtitle]
        ]
        #v(2fr)
        #if date != "" [
          #text(size: 10.5pt, fill: mr-muted)[#date]
        ]
      ],
    )
  ]
}

// ── Cover Style 3: Full-Bleed Atmospheric (page-wide wash & geometry) ──────────
#let _cover-full-bleed(title, subtitle, date, seed: 0) = {
  let title-parts = title.split("\n")
  let s = calc.rem(calc.abs(seed), 100)
  page(
    paper: "a4",
    margin: 0pt,
    background: rect(
      width: 100%,
      height: 100%,
      fill: gradient.linear(
        mr-cover,
        mr-cover-mid,
        mr-cover,
        angle: 135deg + calc.rem(s * 19, 90) * 1deg,
      ),
    ),
  )[
    // Full-page atmospheric geometry layer
    #place(top + left, block(width: 100%, height: 100%)[
      #_mr-geo-mesh(seed: seed)
    ])

    // Main layout
    #block(width: 100%, height: 100%, inset: (top: 3.2cm, bottom: 2.8cm, left: 2.8cm, right: 2.8cm))[
      #set text(fill: mr-white, font: "Outfit")
      #align(left)[#_mr-icon-chip]
      #v(0.6em)
      #text(size: 8.5pt, fill: mr-gray, tracking: 0.15em)[MIND ROCKET SERVICES]
      #v(1.6fr)
      #text(size: 32pt, weight: "bold", hyphenate: false)[
        #title-parts.join[\
        ]
      ]
      #if subtitle != "" [
        #v(0.8em)
        #text(size: 16pt, fill: mr-accent-soft, weight: "medium")[#subtitle]
      ]
      #v(0.8em)
      #line(length: 100%, stroke: 0.6pt + mr-accent.transparentize(50%))
      #v(1.6fr)
      #if date != "" [
        #text(size: 10.5pt, fill: mr-gray)[#date]
      ]
    ]
  ]
}

// ── Dispatcher Cover Page ─────────────────────────────────────────────────────
#let _cover-page(title, subtitle, date, cover-style: "split-mesh", cover-seed: 0) = {
  if cover-style == "minimal" {
    _cover-minimal(title, subtitle, date, seed: cover-seed)
  } else if cover-style == "full-bleed" {
    _cover-full-bleed(title, subtitle, date, seed: cover-seed)
  } else {
    _cover-split-mesh(title, subtitle, date, seed: cover-seed)
  }
}

// ── Footer ────────────────────────────────────────────────────────────────────
#let _footer(page-num) = {
  grid(
    columns: (auto, 1fr, auto),
    align: (left + horizon, center + horizon, right + horizon),
    gutter: 0pt,
    image("/docs/assets/mindrocket/icon.svg", height: 0.42cm),
    text(size: 7pt, fill: mr-muted)[Mind Rocket · confidential draft],
    text(size: 7pt, fill: mr-muted)[#page-num],
  )
}

// ── Body style rules ──────────────────────────────────────────────────────────
#let apply-body-styles(body) = {
  set text(font: "Outfit", size: 10.5pt, fill: mr-body, lang: "en")
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
    text(size: 20pt, weight: "bold", fill: mr-body)[#it.body]
    v(0.3em)
    line(length: 100%, stroke: 2pt + mr-accent)
    v(0.8em)
  }
  show heading.where(level: 2): it => {
    pagebreak(weak: true)
    block(breakable: false)[
      #v(0.8em)
      #text(size: 15pt, weight: "bold", fill: mr-body)[#it.body]
      #v(0.4em)
    ]
  }
  show heading.where(level: 3): it => {
    block(breakable: false, sticky: true)[
      #v(0.5em)
      #text(size: 12.5pt, weight: "bold", fill: mr-body)[#it.body]
      #v(0.2em)
    ]
  }
  show heading.where(level: 4): it => {
    block(breakable: false, sticky: true)[
      #v(0.4em)
      #text(size: 11.5pt, weight: "bold", fill: mr-body)[#it.body]
      #v(0.15em)
    ]
  }
  show heading.where(level: 5): it => {
    block(breakable: false, sticky: true)[
      #v(0.3em)
      #text(size: 11pt, weight: "bold", fill: mr-body)[#it.body]
      #v(0.1em)
    ]
  }

  set list(marker: text(fill: mr-accent)[▸], indent: 1em)
  set enum(numbering: n => text(fill: mr-accent)[#n.], indent: 1em)
  show link: it => text(fill: mr-accent, it)

  show raw.where(block: false): set text(font: "Courier New", size: 10pt)

  show raw.where(block: true): it => block(
    fill: mr-light, inset: 10pt, radius: 4pt, width: 100%,
  )[#set text(font: "Courier New", size: 8.5pt); #it]

  set table(
    inset: (x: 0.6em, y: 0.5em),
    fill: (_, y) => if y == 0 { mr-light },
    stroke: (_, y) => (
      bottom: if y == 0 { 1.2pt + mr-accent } else { 0.4pt + rgb("#D8E4E7") },
    ),
  )
  show table: set text(size: 10pt)
  show table: set par(justify: false, leading: 0.55em)
  show table.cell.where(y: 0): set text(
    weight: "semibold", size: 10.5pt, fill: mr-body,
  )
  show table: set table.cell(align: left)

  show figure.where(kind: table): set block(breakable: true)

  show figure.caption: set text(size: 10.5pt, fill: mr-body)

  show figure: it => {
    it
    v(1.4em)
  }

  body
}

// ── Public: single-document template ─────────────────────────────────────────
#let plandek-doc(
  title: "",
  subtitle: "",
  date: "",
  cover-style: "split-mesh",
  cover-seed: 0,
  body,
) = {
  _cover-page(title, subtitle, date, cover-style: cover-style, cover-seed: cover-seed)

  counter(page).update(1)
  show: apply-body-styles

  body
}

// ── Public: endpiece (last page) ─────────────────────────────────────────────
#let plandek-endpiece(
  contact:   "",
  qr_label:  "",
) = {
  pagebreak()
  page(
    paper: "a4",
    margin: 0pt,
    footer: none,
    background: rect(width: 100%, height: 100%, fill: mr-cover),
  )[
    #grid(
      columns: (55%, 45%),
      rows: (100%),
      block(width: 100%, height: 100%, inset: (x: 2.4cm, y: 2.2cm))[
        #set text(fill: mr-white, font: "Outfit")
        #v(1.2em)
        #text(size: 28pt, weight: "bold")[Thank you]
        #v(0.85em)
        #if contact != "" [
          #text(size: 12pt, fill: mr-gray)[
            #text(fill: mr-accent-soft, weight: "semibold")[Contact: ]#contact
          ]
          #v(0.9em)
        ]
        #v(1fr)
        // Wordmark: use full text column width (wide aspect ratio; small % was illegible).
        #block(width: 100%)[
          #image("/docs/assets/mindrocket/logo.svg", width: 100%)
        ]
        #v(0.55em)
        #text(size: 7.5pt, fill: mr-gray)[
          © Mind Rocket #datetime.today().year()
        ]
      ],
      block(width: 100%, height: 100%, clip: true)[
        #_mr-visual-panel()
      ],
    )
  ]
}

// ── Public: global contents page ────────────────────────────────────────────
#let plandek-contents(depth: 2) = {
  page(
    paper: "a4",
    margin: (top: 2.5cm, bottom: 2cm, left: 2.2cm, right: 2.2cm),
    footer: none,
  )[
    #set text(font: "Outfit", fill: mr-body, lang: "en")
    #set par(justify: false)
    #text(size: 20pt, weight: "bold")[Contents]
    #v(0.3em)
    #line(length: 100%, stroke: 2pt + mr-accent)
    #v(1.2em)
    #outline(
      title: none,
      depth: depth,
      indent: auto,
    )
  ]
}

// ── Public: per-part contents page ───────────────────────────────────────────
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
    #set text(font: "Outfit", fill: mr-body, lang: "en")
    #set par(justify: false)
    #text(size: 20pt, weight: "bold")[#heading-label]
    #v(0.3em)
    #line(length: 100%, stroke: 2pt + mr-accent)
    #v(1.2em)
    #context {
      let start-results = query(label(part-start-label))
      if start-results.len() == 0 { return }
      let start-loc = start-results.first().location()

      let end-loc = none
      if part-end-label != "" {
        let end-results = query(label(part-end-label))
        if end-results.len() > 0 {
          end-loc = end-results.first().location()
        }
      }

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
              fill: if h.level == 1 { mr-body } else { rgb("#3D5A62") },
            )[#h.body],
            text(size: 9pt, fill: mr-muted)[#pg],
          )
        )
        v(if h.level == 1 { 0.5em } else { 0.2em })
      }
    }
  ]
}

// ── Public: interstitial part-divider page ────────────────────────────────────
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
    background: rect(width: 100%, height: 100%, fill: mr-cover),
  )[
    #set par(justify: false)
    #grid(
      columns: (55%, 45%),
      rows: (100%),
      block(width: 100%, height: 100%, inset: (x: 2.4cm, y: 2.2cm))[
        #set text(fill: mr-white, font: "Outfit")
        #align(left)[#_mr-icon-chip]
        #v(1fr)
        #text(size: 11pt, fill: mr-gray)[#label]
        #v(0.4em)
        #text(size: 32pt, weight: "bold", hyphenate: false)[#title]
        #v(1fr)
      ],
      block(width: 100%, height: 100%, clip: true)[
        #_mr-visual-panel()
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

// ── Public: end-page with authored body text ─────────────────────────────────
#let plandek-endpage(
  contact:  "",
  qr_label: "",
  body,
) = {
  pagebreak()
  page(
    paper: "a4",
    margin: 0pt,
    footer: none,
    background: rect(width: 100%, height: 100%, fill: mr-cover),
  )[
    #grid(
      columns: (58%, 42%),
      rows: (100%),
      block(width: 100%, height: 100%, inset: (x: 2.4cm, y: 2.2cm))[
        #set text(fill: mr-white, font: "Outfit", size: 9pt)
        #set par(justify: false, leading: 0.65em, spacing: 1.4em)
        #set heading(outlined: false)
        #show heading.where(level: 1): it => {
          v(0.6em)
          text(size: 12pt, weight: "bold", fill: mr-white)[#it.body]
          v(0.3em)
        }
        #show heading.where(level: 2): it => {
          v(0.6em)
          text(size: 11pt, weight: "bold", fill: mr-white)[#it.body]
          v(0.3em)
        }
        #align(left)[#_mr-icon-chip]
        #v(0.75em)
        #body
        #v(1fr)
        #if contact != "" [
          #text(size: 8pt, fill: mr-gray)[
            #text(fill: mr-accent-soft, weight: "semibold")[Contact: ]#contact
          ]
          #v(0.45em)
        ]
        #if qr_label != "" [
          #text(size: 7pt, fill: mr-gray)[#qr_label]
          #v(0.35em)
        ]
        #block(width: 100%)[
          #image("/docs/assets/mindrocket/logo.svg", width: 100%)
        ]
        #v(0.4em)
        #text(size: 7pt, fill: mr-gray)[Mind Rocket · #datetime.today().year()]
      ],
      block(width: 100%, height: 100%, clip: true)[
        #_mr-visual-panel()
      ],
    )
  ]
}
