# CLI reference

## `build`

Builds a directly viewable directory containing `index.html`, chunked data,
`archive.sqlite`, optional JSON/text, selected media and `integrity.json`.

```bash
local-social-archive build input.json output \
  --media-root ./authorized-media \
  --media image,video,audio,file \
  --text
```

The destination must not already exist. Media paths are resolved below
`--media-root`; absolute paths and traversal outside that root are rejected.

## `validate` and `inspect`

Both parse the normalized format and emit machine-readable JSON. `validate`
exits with status 2 for invalid input. `inspect` currently returns the same
validation result plus collection, entry and media counts.

## `verify`

Recomputes every file size and SHA-256 digest recorded in `integrity.json` and
reports missing, changed and unexpected files.

## `redact`

Creates a normalized review copy. Authors and collection titles are replaced
with deterministic pseudonyms derived from a caller-supplied salt. Media is
removed by default; `--drop-text` also replaces message/post text.

Never reuse a public salt across unrelated archives if cross-archive identity
linkage is undesirable.

## `from-csv`

Accepts UTF-8 CSV with these columns: `collection_id`, `collection_title`,
`id`, `timestamp`, `author`, `is_self`, `category`, `text`, `media_path`,
`media_kind`, and `media_name`. Only `text` is routinely needed; missing IDs
receive deterministic row-based fallbacks.
