# Performance and Scalability Audit

Scope: `POST /api/import/budgets` and `GET /api/ratios/chapters`

## Executive Summary

The import path is linear, not exponential, but it has a high constant cost:

- It performs multiple DB round-trips per line.
- It holds one long SQLite write transaction until the very end.
- It fully materializes the request body and accumulates per-line objects in memory.

For `GET /api/ratios/chapters`, the current implementation is fast enough and benefits from an in-memory cache.

## Measured Results

Benchmark on this checkout with in-memory SQLite and the current `ImportService`:

- `1,000` repeated lines: `1.021s`, `4,006` queries, `4.006` queries/line
- `5,000` repeated lines: `4.807s`, `20,006` queries, `4.001` queries/line
- `10,000` repeated lines: `9.601s`, `40,006` queries, `4.001` queries/line
- `10,000` unique lines: `11.418s`, `50,005` queries, `5.000` queries/line

`GET /api/ratios/chapters` benchmark:

- cold cache: `0.1237s`
- warm cache: `0.0038s`

The import path is therefore `O(N)` with a high constant factor. It is not exponential.

## TOP 3 Bottlenecks

1. Per-line DB lookups in `ImportService`
   - Severity: Critical
   - Each line does at least two `SELECT` calls against `item_master` before the insert path, plus the `ItemInstance` insert.
   - Repeated-key workload still stayed at ~`4 queries/line`; unique-key workload rose to ~`5 queries/line`.

2. Long SQLite write transaction
   - Severity: Critical
   - The code commits only after all lines are processed.
   - Under concurrent imports, SQLite's single-writer model will serialize writers and can produce lock waits/timeouts.

3. Full payload materialization and O(N) in-memory accumulation
   - Severity: Medium
   - `BudgetImportRequest` loads the full `lineas` array into memory.
   - The service also accumulates `seen_keys`, `detalles`, ORM objects, and the response payload.
   - The schema caps imports at `10,000` lines, which prevents runaway growth, but the current design still scales linearly in memory.

## Rate Limiting

There is no rate limiting in the backend code.

Operationally, `100 req/min` would not be the main protection for this endpoint because a single 10k-line import already costs seconds of CPU and thousands of queries. Concurrency control and payload limits matter more than raw request rate.

## SQLite Notes

- `GET /api/ratios/chapters` is fine for the current dataset and cache.
- `get_session()` creates a new engine per request, which is an architectural overhead, but in local timing it was not the main bottleneck.
- The real SQLite risk is concurrent writes during large imports.

## Recommendations

1. Remove the extra `SELECT` in the import loop.
   - Cache the `ItemMaster` lookup in memory for the current batch.
   - Use a single query / upsert path instead of `pre_existing` plus `get_or_create_item_master()`.

2. Batch the writes.
   - Insert `ItemInstance` rows in chunks instead of flushing everything through one giant transaction.
   - Consider `bulk_save_objects` or batch `add_all` where safe.

3. Reduce SQLite contention.
   - If concurrent imports are expected, move to a server-grade DB before production.
   - If SQLite must stay, serialize imports explicitly and tune busy timeout / retry handling.

4. Add hard operational limits.
   - Keep the 10k-line schema cap.
   - Add request size limits at the reverse proxy / app layer.
   - Reject pathological payloads early.

5. Add a performance regression test.
   - Track query count per line.
   - Track a 1k / 5k / 10k import timing budget.
   - Assert that `GET /api/ratios/chapters` remains sub-second on cold cache.
