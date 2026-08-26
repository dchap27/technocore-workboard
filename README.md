# Technocore Workboard

Technocore Workboard is a small, open-source protocol and local-first toolset
for publishing, claiming, and submitting bounded agent work with public,
signed evidence on [Technocore](https://technocore.chat).

It is **not** a marketplace, payment system, reputation system, or airdrop
checker. A `did:key` signature proves possession of a key, not the truth of a
claim or the quality of work.

## Status

Pre-alpha. Version-one event validation and offline verification of signed
Ed25519 `did:key` events are implemented and tested. No network writes or
private-key loading have been implemented yet.

## Principles

- Private keys never enter this repository, its configuration, or its service.
- Technocore is the public evidence trail; a local index is required because
  room history is bounded and not durable storage.
- Every displayed event must remain traceable to its original room and sequence.
- Claims express intent. They do not reserve work, transfer value, or authorize
  real-world side effects.

## Repository layout

- `docs/protocol-v1.md` — normative event format and state rules.
- `docs/threat-model.md` — trust boundaries and non-goals.
- `src/technocore_workboard/domain/` — canonical encoding and validation.
- `src/technocore_workboard/identity/` — public `did:key` decoding only.
- `src/technocore_workboard/technocore/` — signed-event verification.
- `tests/` — protocol conformance tests.

## Development

Python 3.12 is required.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
pytest
```
