# Authoring the book (not published)

This folder is excluded from the build (`exclude_docs` in `mkdocs.yml`).

## Build

```
nix-shell -p python3Packages.mkdocs-material --run "mkdocs build"   # NixOS
pip install mkdocs-material && mkdocs build                          # elsewhere
mkdocs serve                                                         # live preview
```

`strict: true` means a broken link fails the build. Output goes to `site-book/` (gitignored).
Publishing is not wired up: `site.yml` deploys `site/` (the status page) and Pages allows one
site per repository. The plan is to deploy the book under `/book` in the same job (see the
branch description).

## Rules (these are the point of the book)

1. **Every chapter carries an edition box**: `As of` date, `Pinned to` commit, `Status`.
   `Status` is one of `outline`, `draft`, `checked`. Only `checked` chapters may be released.
2. **Every factual sentence cites a source** in the Sources list: an ADR number, a file path
   with the commit, or a capture-log run id. No source, no sentence.
3. **Link the ADRs, never copy them.** ADRs are the immutable record; the book narrates.
4. **Tell it in time order and say what we believed at the time**, including when we were
   wrong. A chapter that only reports the final answer teaches nothing.
5. **Before a release, rerun repo-pincer on the book**: each claim is Confirmed, Drift or
   Aspirational against the code and data at the pinned commit. Update the pin, or fix the
   claim. Do not release a chapter whose pin is older than the files it cites.
6. **Release with the data.** A book edition is built from the same commit as a
   `data-YYYY-MM-DD` tag (ADR 0015). The tag is the edition name.
7. Plain language. The README rule applies: claim only what the code and data support. Not
   public-health guidance; keep the disclaimer on the preface.
8. Personal motives and reflections stay in the private vault. Only what teaches belongs here.

## Chapter template

```markdown
# Title

!!! info "Edition"
    As of: YYYY-MM-DD · Pinned to: `abc1234` · Status: outline

## What we believed

## What we found

## What it taught

## Sources
- docs/lessons.md #N
- ADR 00NN
```

## Pin the toolchain

The Material theme prints a warning about MkDocs 2.0, which is announced as incompatible with
current themes and plugins. When wiring up CI, pin `mkdocs<2` and `mkdocs-material` to exact
versions (checked: mkdocs 1.6.1, mkdocs-material 9.7.7 build this skeleton in strict mode).
