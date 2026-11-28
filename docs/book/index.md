# konis: an archive, and what it taught us

!!! warning "Unofficial and independent"
    This book is not public health or medical advice and is not affiliated with or endorsed
    by the EPA, the U.S. Army, or any state agency. For official information, use the links
    on the project [README](https://github.com/Hefrock/konis#readme).

!!! info "Edition"
    As of: 2026-11-28 · Pinned to: `99ef1e0` · Status: outline

On 25 November 2026 the U.S. Army carried out a controlled detonation of degraded lead azide
at the Iowa Army Ammunition Plant. Agencies published updates on pages and maps that show only
the latest version. **konis** keeps every version, and this book tells the story of building
it: what we believed at each step, what the data and the code showed instead, and what that
taught.

It is a teaching account, in time order. It is also a worked example of a way of working:
store the source first, say what a number does and does not mean, write the question down
before looking at the answer, and re-check your own documents against your own code.

## How the book is organised

- **Part I, the first day.** The archive's first problems: a page that is never the same
  twice, a zero that does not mean zero, a secret hidden in a public page, and an event whose
  time nobody agreed on.
- **Part II, what the data could not say.** Monitors in the wrong place, evidence hidden
  behind a link, and an analysis that turned out to be impossible.
- **Part III, keeping the archive honest.** Alerts people stop reading, a README that outran
  the build, a diagnosis that read the wrong line, a gap in the record, and what it takes to
  make something citable.

Each chapter opens with an **edition box** (as-of date, the commit it was checked against, and
a status) so you can tell how old a claim is. Each ends with its **sources**. The decisions
themselves live in the [ADRs](appendix/adr-index.md); this book narrates, it does not replace
them.

!!! note "Status"
    Every chapter is currently an outline: the structure, the sources and the questions are
    set, the prose is not. Chapter 11 is blocked on evidence that has not been checked yet.
