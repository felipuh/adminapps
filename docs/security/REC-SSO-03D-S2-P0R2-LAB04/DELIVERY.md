# Reviewed incremental delivery

The development checkout starts at `ef71fdac1aff8d653e2b17a36753c96d39b3e65e`.
Its reachable history includes a tracked `.env` with nonempty signing keys and
local virtual environments. LAB04 does not publish that ancestry or modify secrets.

Each objective is committed in the original development checkout first. The
reviewed changed files are then copied to the orphan branch
`lab04/reviewed-delivery-20261021`, committed and pushed normally. That branch
contains an incremental source overlay, **not a standalone application checkout**.
It has no parent from the sensitive history. Its commit IDs therefore differ from
the local development commits; the ledger records both and verifies the remote
delivery ref. Do not merge unrelated histories or treat this as a deployment.

To review the increment, compare the delivered paths with the named baseline in
an authorized local copy. Tests run in the original development checkout with the
complete dependencies. The delivery manifest hashes ensure the published source
overlay is byte-identical to those tested files. A fully sanitized application
history is a separate repository-maintenance task, outside LAB04.
