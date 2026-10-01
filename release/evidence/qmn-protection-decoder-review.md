# Native protection decoder — bounded diagnosis

Status: FAIL pending nominal Instrument validation. Scope only cTrader nested position stop decoding using explicit full-symbol digits/rounding. No archive membership, freshness, CT13 row admission, live pump or provider proof.

Initial inspected SHA256: decoder `9b4eabedfa7ddb7262d244c07edf30ef1921f0c82573e543c764dacfa2f0782f`; test `ad54e707da53b87a30a2a93f91cf811787c3ccd4c25f4c759d2b2445a1e8ac6e`. Owner started subsequent correction during this review; current source blob after scoped tests is 3eb0a50d662090a6e94d4342c9c49e12f0d0d3ba, while held test blob remains 530b8ce1587284cc2357cd39008e2a5d506d3bc5. No silent final-byte approval.

Actual finite ordinary nominal Instrument controls on valid nested provider row and exact account/session/PID/symbol pins raise AttributeError: Instrument(None,'EURUSD'), Instrument(valid_venue,{}), and Instrument(VenueId(None),'EURUSD'). The type guard alone does not establish the CT03 instrument before decode_execution_price. Reconstruct venue/symbol with official validators before sanctioned float conversion; owner/root notified.

Fingerprint(None/123) typed-refuses. Raw stop bool/integer/NaN/infinity and absent stop refuse; missing/mismatched native identity and account/session controls are covered. Official QMF price scale bounds are 0..MAX_SCALE (72), not an invented int64 decimal-place bound; 19 is lawful here. Full pinned metadata provenance is the caller's responsibility and is not proven by this primitive. Existing scoped tests independently report 2 passed in 0.86s, but remain insufficient against the nominal crash.

Expected positive remains exact decoded 1.08523 at scale5 =108523 with raw double provenance and declared rounding. This is a local checked-shape fixture, not an actual provider response admission.


## Nominal authority correction — bounded PASS

Exact held source SHA256 `1384cf279d5ae2d882d377e2f8db0c004684025a1e0c4ed7d79a35f2598339a7`; test `8921321aebeb2fa3c803b9611c447146b57c6576d37e36abf5b9e7f9c115da0d`. Independent scoped pytest: **3 passed in 0.81s**.

Original three ordinary malformed Instrument cases now typed-refuse, as do nested mapping-valued VenueId and blank symbol. Official VenueId/Instrument reconstruction precedes price decoding and rejects normalization drift. Independent legal exact stopLoss=1.0 positives at scales0,5,19,MAX_SCALE72 decode to value10**scale with the requested exact scale; no invented int64-digit cap. MAX_SCALE+1, bool digits/account/symbol, foreign subject/account/session, malformed source fingerprint and nonfinite/bool raw stops refuse. The original 1.08523→108523 scale5 positive remains covered.

Approval is only this decode primitive and nominal/numeric refusal boundary. It does not prove source-event archive membership, checked CT13 row containment, freshness, full-symbol metadata provenance, native protection lineage, LIVE pump or provider integration. Other active protection files are excluded.
