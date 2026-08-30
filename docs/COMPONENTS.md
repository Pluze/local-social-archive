# Acquisition component contract

The public project owns presentation, portable archive generation, archive
query/navigation, offline rendering, credential lifecycle primitives and the
native process boundary. A private acquisition component is a build-time
overlay, not a fork of the main repository.

`Adapter.swift` must implement the public `ArchiveBridge` protocol and expose:

```swift
func makeArchiveBridge() -> ArchiveBridge
```

The adapter receives WebKit messages locally and must return serializable
objects through the page's bridge resolver. It should keep secrets in an OS
credential store, write snapshots below the app's private application-support
directory, and expose only normalized records to the UI.

Public runtime tools in `desktop/macos/Tools/` are always bundled first. An
optional `prepare.sh <build-dir> <tools-dir>` may compile or copy a
component's own runtime dependencies into the supplied tools directory. The
public build treats it as an opaque component hook: it contains no dependency
name, repository URL, implementation assumption or fallback binary.

Build the public stub:

```zsh
zsh desktop/macos/build.sh
```

Build with a separately supplied component:

```zsh
LOCAL_ARCHIVE_COMPONENT_DIR=/absolute/path/to/component \
  zsh desktop/macos/build.sh
```

The component directory is never copied into the public repository. Only its
compiled adapter and explicitly listed source-acquisition runtime tools enter
the resulting app. A provider must not duplicate or privately fork a generic
tool already owned by the public shell.

An open-source license on a third-party key utility does not by itself resolve
vendor contract, technical-protection or anti-circumvention risk. Components
that scan process memory, recover database keys, patch or re-sign a client, or
decode protected media therefore remain wholly outside this public tree.
