# Source provider component placeholder

This directory contains a runnable null implementation and no acquisition
logic. The public desktop shell uses it by default and discovers an optional
replacement at build time through `LOCAL_ARCHIVE_COMPONENT_DIR`.

A compatible separately supplied component provides:

- `Adapter.swift`, implementing `ArchiveBridge` and `makeArchiveBridge()`;
- optional `Info.plist` branding and bundle identity;
- optional `Tools/` executables and scripts;
- optional `prepare.sh` for component-owned runtime dependencies. The public
  repository does not know their implementation details.

Without this component, the public CLI, archive format, offline viewer,
integrity verification, redaction and the macOS shell all build and run. Only
source-specific acquisition and protected-media recovery are unavailable.
