# Local Social Archive

A vendor-neutral toolkit for turning user-authorized, normalized social data into a portable archive that remains useful without the original application.

The output contains:

- `index.html`: a directly viewable offline browser;
- chunked JavaScript data files that work under `file://`;
- `archive.sqlite`: a stable relational representation;
- optional JSON and plain-text copies;
- only the media kinds selected by the user.

This repository deliberately contains no vendor client, logo, database key, account data, memory scanner, binary patch, injection code, proprietary database adapter, authentication-token handler, or media-protection bypass.

## Quick start

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
local-social-archive validate examples/demo.json
local-social-archive build examples/demo.json demo-output --media '' --text
local-social-archive verify demo-output
open demo-output/index.html
```

Input follows [schemas/archive.schema.json](schemas/archive.schema.json). Media paths are resolved only below `--media-root`; traversal outside that directory is rejected.

```bash
local-social-archive build input.json export-output \
  --media-root ./authorized-media \
  --media image,video,file \
  --text
```

The CLI also supports `inspect`, `from-csv`, and deterministic `redact`
commands. Every built archive includes an `integrity.json` SHA-256 manifest;
the generated viewer has no server, framework or network dependency and works
directly through `file://`.

## Included source

- strict normalized-input validation and path containment;
- portable SQLite, JSON and text archive generation;
- selectable image/video/audio/file copying;
- chunked offline web viewer for large collections;
- SHA-256 integrity generation and verification;
- deterministic pseudonymization and review-copy creation;
- a generic CSV adapter and documented adapter contract;
- synthetic fixtures and unit tests with no personal data.

See [docs/CLI.md](docs/CLI.md) and [docs/FORMAT.md](docs/FORMAT.md).

Agents implementing a separately authorized acquisition component should start
with [agent/CLEAN_ROOM_PLAYBOOK.md](agent/CLEAN_ROOM_PLAYBOOK.md) and the
[acceptance tests](agent/ACCEPTANCE_TESTS.md). Those documents preserve the
test-driven reconstruction process while deliberately omitting offsets,
signatures, key-acquisition recipes and protected-format algorithms.

For a from-zero implementation with no private repository or external key-tool
dependency, use the behavioral [reconstruction specification](agent/RECONSTRUCTION_SPEC.md),
[black-box experiment catalogue](agent/BLACK_BOX_EXPERIMENTS.md), and
`tools/audit_public_independence.py`. The public build and test suite exercise
only the null/synthetic providers.

## macOS desktop shell

The public shell is also runnable without a private acquisition component. It
can open the `index.html` of an already exported archive and clearly reports
vendor acquisition capabilities as unavailable.

The desktop lifecycle uses one transactional current backup per data source.
Concurrent clicks share the same task, unchanged source snapshots are reused,
and a successful refresh atomically replaces the previous current backup.
Chat backups supplied by a compatible authorized provider include a directly
openable app-style `index.html`, small compatibility
redirect pages, 500-message data chunks, and UTF-8 transcripts. The viewer opens
at the latest messages, loads older chunks on upward scrolling, and supports
conversation filtering, in-conversation search, and date jumps. The public
shell displays only media already supplied through the normalized archive or
an installed provider. Its bundled stub performs no remote acquisition. A
separately authorized provider may resolve additional media through the
component contract; the public archive layer still validates paths, packages
only user-selected media kinds, records integrity, and marks unresolved items
explicitly missing.

```zsh
zsh desktop/macos/build.sh
```

See [docs/COMPONENTS.md](docs/COMPONENTS.md) for the build-time component
contract. A separately supplied component is an overlay, not a fork.

## Scope and adapter boundary

The public tool starts after data has been obtained through an authorized export, documented API, user-created file, or another lawful source. Vendor-specific acquisition belongs in a separate adapter and is not part of this repository. See [docs/ADAPTER_BOUNDARY.md](docs/ADAPTER_BOUNDARY.md).

## Privacy warning

An archive can contain other people's messages, names, images, voice, location and identifiers. A user's ability to make a private backup does not automatically authorize publishing that backup. Review and redact the output before sharing it.

## Rights review

The conservative publication assessment behind this source split is documented in [docs/RIGHTS_REVIEW.md](docs/RIGHTS_REVIEW.md). It is engineering risk analysis, not legal advice.

## License

Original code in this repository is available under the MIT License. Product and company names belong to their respective owners and are used only for factual compatibility discussion in the documentation.
