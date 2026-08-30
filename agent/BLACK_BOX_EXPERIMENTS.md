# Black-box experiment catalogue

These experiments discover behavior without private source or implementation
details. Use only synthetic data, official exports or a disposable account owned
by the operator.

| Experiment | One controlled change | Observe | Contract fact produced |
| --- | --- | --- | --- |
| Empty baseline | Fresh authorized source | File inventory and zero counts | Required/optional stores |
| Text direction | One sent, one received marker string | Count/time/hash deltas | Self-direction invariant |
| Conversation type | One direct and one group collection | Normalized membership | Collection classification |
| Time boundary | Items around day/month/DST boundary | Stored/order timestamps | Timestamp unit/timezone rule |
| Record taxonomy | One self-authored item per UI type | Row/count deltas | Unknown-type preservation |
| Media variants | Known generated image/video/audio/file | Hash and size mapping | Local resource preference |
| Repeat import | No source change | Output hashes | Idempotency |
| Interrupted copy | Cancel at controlled point | Last archive and staging dir | Atomicity/cleanup |
| Unknown version | Alter synthetic version marker | Error only | Fail-closed behavior |
| Malformed payload | Truncated synthetic record | Structured error | Parser bounds |

Use random marker text that contains no personal information. Record hashes,
counts, timestamps and error codes rather than raw rows. A result that requires
copying a vendor identifier or secret into the public specification is rejected;
express the behavior at the neutral contract level instead.
