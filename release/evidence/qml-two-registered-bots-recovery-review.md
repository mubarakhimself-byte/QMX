# Two registered Bots recovery journey — bounded review, 2026-10-01

Independent Sol ordinary local test review. Held `qmb/tests/test_two_registered_bots_recovery.py` SHA256 `b02e47c1259d07bcd3dead015a828427dbfe4600a2552db44d960c7cacd53623` matched before reading/running and after completion. The prior `cb192c…` hash was superseded before this active review. No product/test edits, commits, provider calls, credentials or security testing. **Main positive PASS; negative zero-registration/persistence proof FAIL/PENDING. Whole journey is not accepted until corrected negative evidence is reviewed.**

## Genuine positive PASS

Two different actual source manifests define the callbacks, including distinct policy/family reasons. Each manifest mints its actual `LogicIdentity`; Layer 1 uses matching family/confluence/producer/logic catalogs. The real `qmb.host.runner.run_sandbox` selects the manifest's unique `fixture_policy/factory.py:factory` and spawns the isolated worker; `collect_layer2_observations` checks the complete source fingerprint against the declaration's logic reference. The test does not substitute an unrelated Python callback for Layer 2.

The official `gate_registration` yields two distinct candidates. Before QMB registration, the fixture checks the candidate declaration, logic, semantic fingerprint and source manifest equality. Official QMB registration functions and Registrar mint actual family, Confluence and Bot CT-06 records; `RegistryPersistence.persist_record` writes all six records to the actual REPLAY evidence store. The persistence instance closes and a new EvidenceStore/RegistryPersistence opens. Each physical family and Confluence/Bot record is loaded at its CT-06 stable id and reconstructed with typed mint functions.

The test correctly distinguishes identities: Bot semantic fingerprint equals the candidate but differs from the physical CT-06 stable id; CT-34 semantic fingerprint likewise differs from its registration stable id. The restored Bot's semantic Confluence cite equals the reconstructed Confluence semantic fingerprint. Equality of the full restored Bot content to the candidate includes its pinned LogicIdentity; the saved manifest is rehashed against that identity before its actual factory is loaded.

Fresh factory instances execute nonempty three-step traces `[1,1,0]`: entry, full close, then empty. Alpha/Beta trace content differs. Another instance advances one step and writes a JSON snapshot. `BotStateSnapshot.from_mapping` reconstructs the saved bytes; a freshly loaded manifest factory restores and produces exactly the uninterrupted remaining trace. Cross-Bot restore refuses in both directions. Static `restore_bot` checks scope mismatch before `construct_bot`, consistent with the intended refusal boundary; this test does not count constructor/import effects explicitly and proves no OS portability or actual provider action.

## Negative zero-effects proof FAIL/PENDING

**P2 test-proof gap:** `test_failed_conformance_does_not_stamp_or_persist_bot` requests `persistence.load_record(declaration.fingerprint_content())`. That is the semantic CT-33 fingerprint, which the positive test explicitly proves differs from the CT-06 storage key. The lookup would miss even if an actual Bot registration under its proper CT-06 key had been persisted. It therefore cannot establish the claimed absence of registered/persisted Bots.

The refusal itself is real: the forbidden `socket` import yields a Layer-2 refusal through the runner's static scan, and `register_bot_definition(ticket=None)` returns refusal. Current product source checks the missing ticket before `Registrar.register`, so this review does not demonstrate a product side effect. However, the negative assertion provides neither `Registrar.stable_ids()` emptiness nor before/after physical artifact/journal census. The empty store is opened separately after refusal and never asked to persist a returned receipt; probing the wrong identity namespace is not meaningful storage proof. This test's whole zero-registration/persistence claim remains unaccepted.

**Required bounded correction:** directly assert the actual registrar contains no records and compare the real physical registry/evidence artifact census before and after the rejected registration flow, with a genuine persisted-registration positive using the correct CT-06 key. Retain the actual Layer-2 refusal and missing-ticket refusal. Cross-Bot scope refusal may additionally use a genuine factory constructor counter to make its before-callback boundary explicit; that is useful verification, not a new domain requirement. Do not represent a semantic-key lookup miss as CT-06 absence.

The negative source has modified bytes but the original LogicIdentity. Its static forbidden-import refusal occurs before the later manifest equality join; it is a bounded Layer-2 capability rejection, not proof of a separately identity-matched failing source candidate. No callback executes a provider in this fixture.

## Validation and limits

From `/workspace/QMX-release`:

```text
uv run --no-sync pytest -q -p no:cacheprovider qmb/tests/test_two_registered_bots_recovery.py
2 passed in 2.34s
```

These passing tests do not erase the negative-proof flaw. Positive evidence is genuine local source-bound conformance, registration, physical fresh read and snapshot continuation. `ConformanceTicket` remains a trusted host Boolean summary; the fixture's explicit candidate/body/source checks do not turn that API into an independently identity-bound or unforgeable ticket. No normal second QMA pack, publisher/occupancy, installed runtime, provider, cross-OS deployment, security or whole release acceptance is claimed. Factory coverage floors remain separate and were not waived.

The coordinator and Data received the proof gap while the held bytes were unchanged. Owner correction requires coordinator release followed by a new exact frozen re-review; the verdict above remains bound to the original bytes.

Held test and exact argv/result notes are retained under `/workspace/qmx-independent-review-archive/qma-qmb-local-authority-diagnostics`:

```text
b02e47c1259d07bcd3dead015a828427dbfe4600a2552db44d960c7cacd53623 test_two_registered_bots_recovery.b02e47-held.py
27345d29b147435eb7e56d6c6c1d94ec5a72385ece4d17dfd0edfa2ba3e96b86 two_registered_bots_recovery.b02e47.notes.json
54e4343fde58cf10ddb8cffdce85828ba22fdc4b92b9249b407fa6549104c7c6 SHA256.json (archive snapshot)
```

## Corrected frozen test re-review — bounded PASS, 2026-10-01

The owner explicitly froze `qmb/tests/test_two_registered_bots_recovery.py` SHA256 `16242094f8458f1f2097d4903f08ce576e42da299bc807de66c45c1ec6c4202d`. It matched review entry and completion. The earlier `b02e47…` negative-proof FAIL remains historical evidence; this verdict covers the corrected bytes only. No product/test edits, commits, new probes, provider or security activity.

**Negative census correction PASS.** The negative flow now opens the actual RegistryPersistence before the rejected registration and reads its official `backup_export()` before and after. Each physical registry-room export has `record_count == 0`. The real `Registrar.stable_ids()` is also empty after missing-ticket refusal. The misleading semantic Bot-fingerprint lookup was removed. `backup_export` reads exact stored records through the world-scoped CT-26 backup-input boundary, so these assertions inspect actual physical record contents rather than an unrelated key miss. The genuine positive still writes and physically reopens six official CT-06 registrations under their real stable ids, providing the functioning persistence control.

**Cross-Bot callback boundary PASS.** Each target factory is still loaded from its actual source manifest. A counting wrapper delegates its real `construct` method and counts calls; both cross-Bot restore attempts refuse with `construct_calls == 0`. This confirms refusal precedes bot construction, while the unchanged positive exercises those actual source factories for nonempty traces and successful continuation. It does not claim no import/module-loading effects: loading the module intentionally occurs before the restore call.

A diff against the archived held `b02e47…` file shows only the constructor wrapper/Protocol and real registrar/export census correction. The source-bound positive remains unchanged: distinct actual declared sources, real sandbox/gate candidates, official registration, semantic-vs-CT-06 identity reconstruction, fresh registry read, source-loaded factories and JSON snapshot continuation.

Exact validation from `/workspace/QMX-release`:

```text
uv run --no-sync pytest -q -p no:cacheprovider qmb/tests/test_two_registered_bots_recovery.py
2 passed in 2.51s
```

This is **bounded test journey PASS**. Candidate/source equality is still asserted by the fixture; the low-level product accepts a trusted Boolean ConformanceTicket. The test does not prove a production candidate-bound registration ingress or unforgeable ticket, nor normal second-QMA-pack/publisher/occupancy behavior, factory coverage compliance, installed/provider/cross-OS execution, complete security or release acceptance. Those limits survive the correction.

Archived original/corrected bytes and argv/result binding:

```text
16242094f8458f1f2097d4903f08ce576e42da299bc807de66c45c1ec6c4202d test_two_registered_bots_recovery.162420-held.py
ea86146139cee2f917cedee54f69202828b5814da8c3476441d658f833c6bfb2 two_registered_bots_recovery.162420.notes.json
7f6d420c4072c51b55b383e70b0c8b98187e80e9a70feeb7304091bd76ed9839 SHA256.json (archive snapshot)
```
