# Publication boundary

This file defines what belongs in the public project. It describes publication
categories only and makes no claim about any author's separate implementation.

## Excluded source-specific implementation

- vendor-specific credential acquisition;
- protected-format access;
- version-sensitive binary analysis;
- proprietary storage interpretation;
- vendor-specific client integration.

These areas end at the neutral provider contract in `ADAPTER_BOUNDARY.md`.
Operational procedures and source-specific implementation facts are outside the
public project's specification.

## Excluded because of privacy or confidentiality

- source snapshots and generated archive databases;
- chat transcripts, conversation indexes, contact names and account identifiers;
- posts, comments, locations, raw source payloads and remote access material;
- downloaded or cached images, video, voice and documents;
- credential-store records, logs, captures and generated manifests made from a real account.

## Excluded because authorship or license is not clean for this MIT repository

- cloned reference repositories, their Git histories and their assets;
- reference-derived files whose terms are incompatible with this repository;
- implementations with incompatible, unclear or missing provenance, even where independent concepts may be lawful to reimplement;
- source or assets from unrelated archive viewers. The static viewer here is independently implemented from general web-platform concepts.

## Included after independent rewrite

- a vendor-neutral interchange schema;
- a standard-library-only exporter;
- selective copying of user-authorized local media with containment checks;
- a generic SQLite layout;
- an original static viewer using chunked script data;
- a native macOS shell with a runnable null acquisition component;
- the complete archive browser, newest-window pagination, upward history loading,
  date navigation, message search and result-to-message navigation;
- vendor-neutral SQLite archive queries, structured export reducers and offline
  export viewer generation;
- Keychain inventory and user-confirmed credential reset primitives, without any
  acquisition or decryption implementation;
- timeline HTML rendering from an already normalized user-owned archive;
- archive validation, deterministic redaction and SHA-256 verification;
- a component-contract checker and clean-room agent experiment framework;
- synthetic fixtures, tests and publication-risk documentation.

## Reintroduction rule

Do not add an excluded component merely because it has an open-source license.
Publication requires known provenance, license compatibility and notices,
appropriate authorization, no unresolved access-control concern, no real
personal data, no secret, and no confusing vendor branding. Generic
presentation, archive navigation, export, lifecycle and validation code belongs
here whenever it remains independently useful with the null provider.
