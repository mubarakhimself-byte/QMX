# Next task: MA02 candidate persistence only

Planning pointer; no MA02 implementation is included in this candidate.
Source: claude-reconciliation/MINIAPP-IMPLEMENTATION-PACKETS.md, MA-02 section.
Original packet SHA256: `9bafc9762003bf931039b99f52f3887169de8e9a3c0947a32e93db76d9e1e040`.
The packet was prepared at ea65b50d; start the next task from the reviewed final
combined candidate named in SOURCE-REF.json, after parent acceptance. Preserve
the accepted startup and artifact-cap contracts and strict MA01 opt-in.

## MA02 packet

Persist Mini App candidates and maintenance versions

Dependencies: MA-01.

Save/read a data-only composition candidate with daemon-issued identity, immutable content fingerprint, base/current revision CAS, source/asset refs and originating authoring session. Define a named app-candidate extension after checking AM-03 editor payload domain; do not overload an unrelated editor DTO or RefinementProposal. New app and change-to-existing app use the same version chain.

Cross-system impact: QMA core definition/artifact owners, sole-writer daemon projection, QMA wire additive schema. Artifact cap is external prerequisite only for staged bytes; its patch is separately owned.

Acceptance checks:

- Create candidate, stop/reopen installed daemon, recover exact head and version history.
- Two edits from the same base: one accepted, one typed stale-revision refusal without lost data.
- App-use can request change/read permitted state but cannot save/apply/forge authoring authority.
- Long/binary content uses existing stage and fp1 references, never executable inline payload evaluated by daemon.

Decision/amendment: Named candidate schema/owner extension must preserve closed store and sole-writer rules; do not invent a sixth SQLite class.

## Bounded next-task handoff

Inspect AM-03 and the closed editor payload domain before selecting the named
app-candidate extension and existing definition/artifact owner. Record any needed
named schema/ownership amendment; do not disguise the candidate as an unrelated
editor draft or RefinementProposal. Reuse the sole daemon writer/projection and
immutable fp1 content. Do not add another SQLite class, engine or store.

Implement only create/save/read and maintenance version-chain/CAS persistence
for a data-only candidate, with daemon-issued IDs and originating authoring
session. App-use can request a change/read permitted state but cannot save/apply
or forge authoring. Cap is an external prerequisite only when staged bytes are
used. No executable inline evaluation, grant inflation or provider call.

End with clean source, schema/route/capability handoff, installed real-daemon
create/stop/reopen/history recovery, competing same-base edit stale refusal,
app-use/principal/Origin denials, fingerprint/reference checks and preserved
source/installed byte evidence. Parent independently reviews the packet.

The requested first milestone stays MA02 -> MA03 -> MA04 -> MA05:
create/version candidate -> validate pinned catalog/dependencies -> publish,
replace/update and undo via a new receipt -> durable activity/evidence. MA02
alone cannot claim create-to-publish or completed Mini App lifecycle. Leave
MA03-13 implementation, UI wiring, provider/credential access, deployment,
public push and protected merges for their own authorized tasks.
