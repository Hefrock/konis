# ADR 0004: Credential-shaped strings are redacted before storage

Status: accepted (25 Nov 2026).

The Illinois EPA update page embeds that site's own Mapbox public map token. GitHub push
protection rejected the first push. Public tokens are meant for browsers, but the repo rule is
that no credential-shaped string is committed (K9), and allowing it would mean dismissing a
push-protection alert on every capture.

Decision: before a capture is stored, known token patterns (Mapbox, Google API key, AWS key,
GitHub, Slack, ArcGIS `token=`) are replaced with `[REDACTED:<kind>]`. The manifest records the
sha256 of the bytes as received (`upstream_sha256_before_redaction`) and a sha256 of each
redacted string, so a later capture can be shown to match the original without publishing
the token. This is the second documented exception to K1 (with ADR 0002).
