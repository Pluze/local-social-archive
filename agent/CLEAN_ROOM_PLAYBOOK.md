# Clean-room acquisition-component playbook for agents

This playbook preserves architecture knowledge without publishing a vendor
adapter or a recipe for bypassing technical protections. It is an engineering
workflow, not a conclusion that any proposed acquisition method is lawful.

Read `RECONSTRUCTION_SPEC.md` next. It is the complete behavioral target for an
Agent that has no private code or external key utility available.

## Non-negotiable gates

Before experimenting, record all of the following in an experiment log:

1. The operator owns or is authorized to access the account and device.
2. The test corpus was created by the operator or consists of synthetic data.
3. The current product agreement and applicable law have been reviewed for the
   intended jurisdiction and distribution model.
4. No vendor binary, asset, secret, real conversation or third-party personal
   information will enter source control, fixtures, logs or issue reports.
5. Process attachment, memory inspection, client modification/re-signing,
   injection, authentication reconstruction and protected-format acquisition
   are outside this public project's specification. An implementation that
   needs one of them stops at the public `KeyProvider`/`MediaProvider` boundary.

An open-source license on a reference tool does not change gates 3 or 5.

## Two-team clean-room rule

Use a specification role and an implementation role. The specification role
may document externally observable behavior from authorized black-box tests:
inputs, outputs, state transitions, error classes and performance bounds. It
must not copy source, disassembly, offsets, signatures, database keys, table
layouts or token algorithms. The implementation role works only from that
neutral specification and synthetic fixtures. Keep provenance notes for every
fact used.

For a one-person project, perform the roles in separate branches and preserve a
written evidence trail. This reduces contamination risk but is not a substitute
for legal review.

## Capability ladder

Implement and test one rung at a time. Never broaden privileges merely because
a later rung is blocked.

1. **Normalized-file adapter** — import a user-created JSON/CSV file and pass
   the public schema and archive tests.
2. **User-selected snapshot** — copy only files explicitly chosen through an OS
   picker; verify copy stability and never modify the source application.
3. **Storage detector** — report format/version capabilities using documented
   metadata or file headers. Unknown versions must fail closed.
4. **KeyProvider boundary** — accept a key handle supplied through an approved
   source such as an official export flow, a user-provided value, or an OS
   credential created by the component itself. The public contract deliberately
   contains no key-acquisition algorithm.
5. **Snapshot decryptor** — operate only on a copy, never log key material, and
   validate the decrypted output using a known synthetic encrypted fixture and
   a structural integrity check before any parser runs.
6. **Schema mapper** — inspect the already-opened test database dynamically,
   map records to the neutral schema, and tolerate additive/unknown fields.
   Vendor table names and packed-field layouts stay in the private component.
7. **MediaProvider boundary** — start with ordinary user-selected files and
   magic-byte/MIME validation. Protected containers or expiring remote access
   parameters are outside this public specification.
8. **Incremental sync** — use immutable snapshots, deterministic identifiers,
   transactions and rollback. A failed sync must leave the last archive usable.

## Agent experiment loop

For each hypothesis:

1. State one observable question, for example “does a new self-authored test
   message create one additional normalized row after an authorized export?”
2. Create the smallest synthetic or self-authored before/after fixture.
3. Record application/OS version and hashes of test inputs, never their secrets.
4. Run the experiment in a disposable copy and collect only counts, types,
   timestamps, error codes and hashes.
5. Write a failing contract test before adding an implementation.
6. Implement behind the narrowest provider interface.
7. Re-run the entire public acceptance suite and a privacy scan.
8. Remove raw experiment artifacts and document what was learned at the neutral
   behavioral level.

Stop at the provider boundary rather than improvise when a test would require
disabling an OS security control, inspecting another process, contacting a
remote endpoint with saved credentials, or using data belonging to another
person.

## Definition of done

A component is releasable only when it passes `ACCEPTANCE_TESTS.md`, returns
structured “capability unavailable” errors for unsupported operations, contains
no personal data or secrets, identifies every third-party license, and has a
documented distribution decision for the specific component. Passing tests
does not by itself make public distribution permissible.
