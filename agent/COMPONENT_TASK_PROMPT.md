# Suggested agent task for an authorized clean-room component

Use this as a starting prompt after filling in the bracketed facts:

> Implement the next missing acquisition-component capability for data owned by
> [operator] on [device/OS] using only [approved source methods]. Read
> `agent/CLEAN_ROOM_PLAYBOOK.md`, `agent/ACCEPTANCE_TESTS.md`,
> `docs/COMPONENTS.md`, and the component contract first. Work only with
> synthetic or self-authored fixtures. Record each hypothesis and result in the
> experiment-log template. Add a failing contract test before implementation,
> fail closed on unknown versions, never print or commit secrets/raw messages,
> Activities that inspect another process, modify a client, reconstruct
> authentication material, bypass an access control, or decode a protected
> format are outside this public project's scope. Stop at the provider boundary.
> Separately reviewed external research is not specified, automated, or
> documented here. Never weaken OS security or widen the requested scope.

The requested outcome should name one narrow capability, such as normalized
CSV import, user-selected snapshotting, synthetic snapshot decryption given a
caller-supplied key handle, schema normalization, or ordinary local-media
resolution. “Make decryption work by any means” is not an acceptable task
statement because it erases the authorization and method boundary.
