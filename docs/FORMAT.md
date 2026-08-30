# Interchange and export formats

The input interchange format is intentionally vendor-neutral. A root object
contains `schemaVersion: 1`, a title and collections. Each collection contains
ordered entries; an entry may represent a message, post, comment, event or
other user-owned social record.

Required fields are defined by `schemas/archive.schema.json`. Extensions are
allowed so an adapter can preserve additional normalized metadata without
changing the core exporter. Source-specific raw database rows, encryption keys
and authentication tokens should not be placed in the interchange document.

## Export directory

| Path | Purpose |
| --- | --- |
| `index.html` | Offline viewer entry point |
| `data/manifest.js` | Collection and chunk index for `file://` use |
| `data/collection-*.js` | Chunked entries, 500 per file |
| `archive.sqlite` | Relational query copy |
| `archive.json` | Optional normalized JSON copy |
| `archive.txt` | Optional human-readable text copy |
| `media/` | Included media selected by kind |
| `manifest.json` | Counts and archive options |
| `integrity.json` | File sizes and SHA-256 digests |

Media source paths are never retained in exported entry JSON. Only copied,
relative archive paths are exposed to the viewer.
