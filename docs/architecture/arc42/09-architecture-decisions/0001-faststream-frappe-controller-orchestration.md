# ADR 0001: FastStream and Frappe-Controller Orchestration

## Status
Accepted

## Date
2026-08-13

## Context
Printrove fulfillment involves multi-step asynchronous lifecycles: waiting for high-resolution artwork uploads, product SKU generation, real-time courier rate calculations, and wallet credit top-ups. Traditional cron jobs or blocking worker threads (`time.sleep()`) lead to thread pool exhaustion, duplicate API calls, and race conditions.

## Decision
We adopted `frappe-controller` powered by FastStream to manage background task execution.
- Workflows suspend execution cleanly using `frappe.wait_for` without blocking worker slots.
- Multi-step parent workflows orchestrate isolated child tasks (`frappe.enqueue(..., as_child=True)`) and evaluate deterministic cached results on replay.
- External API calls are guarded with rate limiting and exponential backoff retry policies.

## Consequences
### Positive
- Zero worker thread lockups during external system delays.
- Clean idempotent workflow resumption and replay protection.
- Native telemetry and rate-limit compliance with Printrove's API SLAs.

### Negative & Risks
- Requires workflows to strictly encapsulate mutating side effects inside child jobs.
- Handled through strict coding standards preventing non-deterministic operations in parent orchestrator bodies.
