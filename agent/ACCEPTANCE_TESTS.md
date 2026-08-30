# Acquisition-component acceptance tests

## Public contract tests

- The public repository builds with the stub and no private files.
- The stub opens an exported `index.html` and reports unsupported acquisition
  with a structured error.
- A component is replaceable through `LOCAL_ARCHIVE_COMPONENT_DIR`; it does not
  patch public source files.
- Normalized output passes `local-social-archive validate`.
- Export output passes `local-social-archive verify` after a fresh build.

## Safety and privacy tests

- Source and Git history contain no account IDs, absolute user paths, keys,
  tokens, real message text, contact names or copied application assets.
- Logs contain capability names and counts, never credentials or raw rows.
- Every decryption test uses an independently generated synthetic fixture.
- Input snapshots are opened read-only; output uses a separate private folder.
- Cancellation, timeout and malformed-input tests preserve the last good archive.
- Media collection never performs an implicit network request. Missing media is
  retrieved by the source client under explicit user control, then resolved from
  its local cache.

## Compatibility tests

- Unknown application/database/media versions fail closed.
- Missing optional capabilities do not prevent viewing existing archives.
- Duplicate identifiers, truncated files, schema additions and unavailable
  media yield deterministic errors rather than silent omission.
- Tests cover empty, one-item, multilingual, large-text and large-collection
  archives, plus every supported local media kind.

## Release evidence

Retain a machine-readable test report, dependency/license inventory, clean-tree
status, artifact SHA-256 and the signed-off experiment log. Do not retain raw
private test data in the evidence bundle.
