# Private adapter boundary

An adapter may be implemented privately when the operator has a lawful, authorized source. Its only public contract should be the normalized JSON schema.

## Preferred acquisition order

1. Official user export supplied by the service.
2. Documented API with an appropriate user authorization grant.
3. Files the user created or explicitly exported.
4. A separately reviewed local adapter whose legality, contract compliance and consent model have been established for the operator's jurisdiction and use case.

## Adapter responsibilities

- prove that the requesting user controls the source account;
- use read-only access and produce an immutable snapshot;
- distinguish the user's own content from content authored by other people;
- avoid collecting credentials, session tokens or unrelated account data;
- emit provenance, timestamps, schema version and completeness indicators;
- surface missing media honestly instead of guessing associations;
- never place a secret in logs, command output or the normalized archive.

## Intentionally undocumented implementation areas

This public repository does not provide operational instructions for:

- modifying or re-signing a vendor application;
- attaching to another process or reading its memory;
- deriving or capturing database or media-protection keys;
- bypassing integrity, sandbox, access-control or anti-automation mechanisms;
- reproducing private database schemas, wire protocols or token algorithms;
- downloading media through captured authentication material.

If an authorized enterprise integration needs one of these areas, treat it as a separate security and legal review, not as a feature of the portable archive format.

## Safe testing strategy

Develop adapters against synthetic fixtures or data exported from a test account. Keep fixtures free of real identifiers, messages, URLs, tokens and media. Contract tests should validate only the normalized schema and completeness report.
