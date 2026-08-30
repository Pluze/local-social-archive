# Clean-room reconstruction specification

This document is the functional specification for rebuilding a compatible
acquisition component without access to any private repository, private binary,
database key utility or unpublished schema notes. It states observable behavior,
interfaces, experiments and acceptance criteria. It deliberately does not state
vendor offsets, symbols, table names, key locations, patch instructions,
authentication algorithms or protected-media transforms.

The target is behavioral compatibility with the public desktop shell, not a
line-for-line recreation of any existing component.

## Deliverable shape

A reconstructed component is a standalone directory containing:

```text
component/
├── Adapter.swift
├── component-contract.json
├── Info.plist                 # optional branding/bundle identity
├── prepare.sh                 # optional opaque dependency build hook
└── Tools/                     # optional runtime helpers
```

`Adapter.swift` implements `ArchiveBridge` and exports:

```swift
func makeArchiveBridge() -> ArchiveBridge
```

The public repository must never be patched to install a component. A successful
build uses only:

```zsh
LOCAL_ARCHIVE_COMPONENT_DIR=/absolute/path/to/component \
  zsh desktop/macos/build.sh
```

## Observable bridge contract

Every request is a WebKit message with `id`, `action` and `payload`. Every reply
resolves the same `id` with a JSON-serializable object. Unsupported operations
return `{ "ok": false, "error": "...", "code": "capability-unavailable" }`.

| Action | Required observable result |
| --- | --- |
| `bootstrap` | Counts, readiness, capability state and normalized conversation summaries; never a credential |
| `readConversation` | Stable paginated normalized messages or a compatible text page |
| `search` | Bounded local full-text results with collection identity and escaped snippets |
| `readMedia` | A bounded local preview or an explicit too-large/unavailable result |
| `openResource` | Opens one already-authorized local resource |
| `momentsPage` | Reverse-chronological self-authored posts, counts and local/missing media status |
| `readMomentMedia` | Local preview only; no implicit network request |
| `openMomentMedia` | Opens one already-resolved local file |
| `exportSelected` | Portable archive for selected collections and requested media kinds |
| `exportMoments` | Portable structured post archive with selectable media inclusion |
| `refreshChats` | Immutable snapshot → validated open → normalization → atomic archive replacement |
| `refreshMoments` | Same pipeline, limited to the operator's own posts |
| `openMomentsSource` | Opens the installed source client and provides cache-hydration instructions |
| `rescanMomentsMedia` | Resolves only files already written to the local source cache |
| `taskStatus` | `running`, `action`, `done` or `error`, with no raw secret or private row |
| credential-related action | Capability/status transition only; secrets remain in the OS credential store |

The public Web UI is the executable consumer specification. When a response
field is unclear, add a synthetic response to the null adapter and observe the
UI rather than consulting a private implementation.

## State machine

```text
component-unavailable
        │ install compatible component
        ▼
needs-authorization ──declined──► capability-unavailable
        │ granted for exact source/device
        ▼
needs-key-provider ──unsupported/version changed──► unsupported-version
        │ approved provider returns opaque handle
        ▼
ready ──► snapshotting ──► opening ──► normalizing ──► indexing ──► ready
  ▲             │              │             │             │
  └─────────────┴──────────────┴─────────────┴─────────────┘
         any failure preserves the last good archive and returns error
```

No transition may silently downgrade completeness. Missing shards or media are
reported as counts and capability gaps.

## Reconstruction work packages

### R0 — public-only baseline

Build the null component, run all public tests, open the synthetic example and
record the expected UI and JSON bridge traffic. Run `tools/audit_public_independence.py`.
This proves no private artifact is accidentally acting as an oracle.

### R1 — normalized fixture provider

Implement `bootstrap`, pagination, search and export against `examples/demo.json`.
No vendor data is involved. This establishes the bridge, storage and atomic
replacement behavior before acquisition research begins.

### R2 — authorized snapshot provider

Use an OS file picker or a caller-supplied directory. Inventory files with
`agent/lab/snapshot_diff.py`, copy to a new private directory, then reopen the
copy read-only. Reject symlinks escaping the selected root, changing source
files, unknown versions and partial copies. Never edit the installed client or
its live storage.

### R3 — storage-engine characterization

Use public dependency notices, documented file signatures and errors from
opening a disposable copy to form hypotheses. Reproduce each hypothesis with a
synthetic database generated by the suspected engine's official tooling. The
acceptance test is a synthetic encrypted fixture that opens only through an
opaque key handle and passes a structural integrity check. Do not infer that a
working cipher configuration authorizes acquiring a real key.

### R4 — independent KeyProvider

Treat key acquisition as a replaceable provider with this conceptual contract:

```text
request:  account fingerprint, database fingerprint, source version
result:   opaque credential-store handle OR a structured unavailable/error state
forbidden output: plaintext key in logs, JSON, command line, archive or Git
```

Supported provider inputs, in preferred order:

1. official export/API or documented recovery flow;
2. explicit user-supplied key stored by this component in the OS credential store;
3. documented OS/application credential interfaces authorized for this account.

Process inspection, client modification, authentication reconstruction and
protected-format acquisition are outside this specification. If the supported
inputs above are unavailable, return a structured capability error and stop at
the provider boundary. The public tests exercise a fake provider and therefore
require no external key utility.

### R5 — schema discovery by controlled deltas

Create a disposable test account or official export containing one controlled
change at a time: one text item, one self/peer direction change, one group item,
one timestamp boundary and one example of each media category. Compare only
file hashes/sizes first. After a caller-supplied provider opens synthetic or
copied test data,
inspect schema metadata dynamically and map observable fields to the neutral
format. Record semantic facts, never vendor table/column names, in public notes.

Required invariants:

- every source row has a deterministic source identity;
- ordering is stable across repeated imports;
- sender/self/group classification is test-derived, not guessed from names;
- unknown record types are preserved as labeled opaque records;
- malformed fields cannot inject HTML or escape media roots.

### R6 — local media resolution

Use self-authored fixtures with known plaintext hashes. Test ordinary image,
video, audio and file resolution before any protected container. Match using
stable IDs or verified hashes and mark ambiguity instead of choosing the first
candidate. Any protected transform is outside this public specification.

### R7 — incremental and failure-safe sync

Run repeated no-change syncs, additions, deletions, interruption, corrupt-copy,
unknown-version and low-disk tests. Build into a transaction/staging directory,
verify counts and integrity, then atomically select the new archive. Never delete
the last valid archive during acquisition.

## What an Agent may infer versus publish

An Agent may formulate and test hypotheses in an authorized local lab. Public
commits may contain provider interfaces, synthetic fixtures, neutral behavioral
observations, failure modes and independently written generic code. Public
commits must not contain real keys/data, proprietary identifiers, executable
bypass recipes, copied/disassembled expression, fixed offsets/signatures,
patched bundles, credential-reconstruction algorithms or protected access
parameters.

## Completion criteria

The component is behaviorally complete when all public UI actions either work
or return an honest capability error; synthetic decrypt/open tests pass without
an external private dependency; self-authored delta fixtures normalize without
silent loss; media status distinguishes local/missing; failure injection
preserves the previous archive; and the component passes the public acceptance,
privacy and independence audits.
