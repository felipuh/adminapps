# WORM Append-Only Plan

Date: 2026-07-03

## Target Architecture

- Application audit events remain in the primary database for queryability.
- Each event includes actor, tenant, object, action, timestamp, reason, request metadata, previous hash, and event hash.
- Events are streamed to external immutable storage with retention policy lock.
- Periodic checkpoints anchor hash-chain roots outside the application database.

## Candidate Controls

- Object storage with retention lock and legal hold.
- Append-only event stream with restricted producer identity.
- Separate audit-reader role from application administrator role.
- Scheduled integrity verification job.
- Restore drill proving events remain verifiable after recovery.

## Pilot Scope

Do not implement WORM in this phase. Keep local hash-chain/audit controls as defense-in-depth only and document the limitation for all regulated buyers.
