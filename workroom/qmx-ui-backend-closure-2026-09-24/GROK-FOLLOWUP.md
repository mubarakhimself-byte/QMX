Continue the existing QMX backend-delta architecture session. Read C:/Users/Mubarak/Desktop/QMX/workroom/qmx-ui-backend-closure-2026-09-24/REVIEW.md and resolve only C1/C2 plus necessary consistency edits.

C1: lost host_control recovery currently requires a still-valid copy of the lost token. Define an OS-owner-verified recovery or protected-backup restoration path that preserves local_operator and journals, with lost-file/restart and unauthorized-user traces.

C2: specify both renew/origin-revoke orderings. If renewal commits first, subsequent origin revoke must revoke the new proof as well. If revoke commits first, renewal must refuse. Remove the conflicting generic first-append-wins/loser-no-op rule for this case; distinguish single-record revoke.

Preserve closed draft creation/publication contracts, transfer prerequisites and completed small reconciliations. Update affected spine/companions/UI text, closure map and traces; correct the AM-17 index. Run the reviewer gate and return for focused closure review. Do not implement, run Documentation Factory, start epics or alter factory inputs.
