# Security policy

Please do not include real archives, access tokens, credentials, encryption keys, account identifiers or private media in a bug report.

Report path traversal, script injection, secret exposure or unintended network access privately to the repository maintainer. Reproduce issues with the synthetic example whenever possible.

The exporter treats input data as untrusted. Media paths outside the configured media root are ignored. The offline viewer escapes displayed text and does not make network requests.
