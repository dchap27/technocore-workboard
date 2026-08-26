# Threat model

## Assets to protect

- The operator's encrypted `identity.pem` and its passphrase.
- The integrity of the local event index.
- Users viewing Workboard content.

## Trust boundaries

Technocore verifies an Ed25519 signature but does not verify a real-world
identity, the truth of a message, the safety of a URL, or the permanence of
room history. Every public message, room name, note, and URL is untrusted input.

The Workboard indexer may derive useful display state from these messages. It
must retain the raw source evidence and never turn a claim into authorization,
payment, access, or an irreversible side effect.

## Controls in v1

- Identity files, keys, encrypted archives, databases, and environment files
  are excluded from Git.
- Only canonical, validated event payloads are indexed.
- Signed envelope verification is required before an event is considered valid.
- The UI will escape all user-controlled fields and mark external links.
- SQLite state is an index/cache, not a replacement for public source records.

## Non-goals

- Wallets, tokens, rewards, payments, escrow, or airdrop eligibility.
- Identity proof beyond control of a `did:key`.
- Confidential messaging or private task content.
- Guaranteeing a claim is exclusive, work is completed, or an artifact is safe.
