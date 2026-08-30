# Architecture

```text
authorized source
      │
      ▼
private/vendor adapter ──► normalized interchange JSON
                                  │
                                  ▼
                     Local Social Archive exporter
                         ├── archive.sqlite
                         ├── archive.json / archive.txt
                         ├── selected media
                         └── index.html + chunked data
```

The split is intentional:

1. Acquisition is vendor-specific and can carry contractual, intellectual-property, privacy and security risk.
2. Normalization produces a documented, vendor-neutral model.
3. Packaging and viewing operate only on that neutral model and user-selected local media.

Each collection is divided into chunks of 500 entries. The browser loads a collection only when selected. Data is emitted as ordinary script assignments because browsers commonly block `fetch()` from a local `file://` page. No server, browser extension or network request is required.

SQLite is the durable representation. The browser files are replaceable presentation artifacts; rebuilding the viewer should not require reacquiring source data.

## Security properties

- Media source paths must remain under the explicit media root.
- Source paths are removed from exported JSON.
- HTML renders user text through escaping, not raw HTML insertion.
- The package makes no outbound network requests.
- Secrets and authentication material are outside the interchange schema.
