# Durable independent review probe archive

Sol retained 12 successful current probes under `/workspace/qmx-independent-review-archive`, with exact script SHA256 values, argv/environment/cwd, stdout/stderr hashes, reviewed full commits and observed source hashes in `manifest.json`. All 12 reruns exited 0. README and `archive_reviews.py` provide the resumable runner; future runs retain separate timestamped snapshots instead of overwriting the original traces.

Reviewed product slices are native Book full-close `915d225b46737bce636f817310d30c4d45064b21`, ATC checked reconciliation `0fac48d6a361b558f40dd59ea11a210f9aefa28d`, and observer uncertainty retry `626b6cbcb7447b1a895105195cd2c682d9a571ca`. Observed repository HEAD during the archive run was `0e87c49682485c4858b9e5622691cf7c4238bc85`.

Metadata explicitly compares each observed source file to the reviewed commit. The observer's TaskGraph projection dependency was an active working copy differing from commit 626b6cbc; its actual retained bytes match the original recorded SHA256 `dcb3416b621ebdd1ab3a3b1a07171e2c43da068b9a1c4eef922c4620451aaa60`, and its commit diff is retained. HEAD alone does not identify that dependency. The archive preserves this distinction and requires a final frozen rerun/review.

These probes exercise real local filesystem/QMF/SQLite persistence with labeled policy and venue doubles. Negative controls intentionally expect typed refusals. They are bounded source-helper reviews, not final installed execution, provider/L17 evidence, full current-worker acceptance, browser acceptance or blanket security approval. See the corresponding native, ATC and observer review documents for precise coverage and limits.
