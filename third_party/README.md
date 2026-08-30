# Third-party source policy

This public tree intentionally does not vendor client memory scanners, database
key extractors, client patchers/re-signers or protected-media decoders. A
permissive source-code license is necessary for redistribution but does not
resolve separate vendor contract or technical-protection risk.

Build-time acquisition components may carry their own audited dependencies in
a private `Vendor/` directory. The public archive format, viewer and exporters
do not depend on them.
