# Cross-cutting Concepts

## 1. Authentication & Token Management
Authentication against the Printrove REST API uses JWT bearer tokens.
- The API client issues `POST /api/external/token` with configured credentials.
- Returned tokens are cached in Redis with a 3600-second (1 hour) TTL under the cache key `printrove_access_token:{email}`.
- Requests automatically inject the cached token into HTTP `Authorization: Bearer {token}` headers.

## 2. Event-Driven Workflow Orchestration & Replay
The background processing subsystem utilizes event orchestration capabilities:
- **Non-blocking Wait (`frappe.wait_for`)**: When an asynchronous dependency is not ready (such as a pending image upload or low wallet balance), the orchestrator raises deferred job signals internally to suspend worker execution.
- **Child Job Isolation (`as_child=True`)**: Sub-tasks (e.g. calculating shipping, creating orders, submitting documents) are enqueued as isolated child tasks and awaited with result getters.
- **Deterministic Replay**: When a parent workflow resumes after suspension, finished child jobs return their cached results immediately without repeating external side effects.

## 3. Image Processing & Sanitization
Printrove requires images to be formatted strictly as JPEG, JPG, or PNG.
- The file manipulation utility inspects incoming image binary headers using Pillow.
- Unsupported formats (e.g., WEBP, TIFF, BMP) are converted in-memory to standard PNG and re-attached as clean File records before external transmission.

## 4. Financial Validation & Prepaid Accounting
Before dispatching drop-ship orders to Printrove:
- The system verifies that the company's prepaid wallet balance in `tabGL Entry` is greater than or equal to the Purchase Order `grand_total`.
- If the balance is insufficient, the workflow pauses execution until an authorized user posts a new Purchase Invoice to credit the account.

## 5. Rate Limiting & Error Recovery
All external API jobs specify explicit rate limits (30–60 req/min) and retry limits (3–5 retries).
- Transient errors (HTTP 429, 502, 503, 504, timeouts) raise natural exceptions to trigger exponential backoff.
- Deterministic errors (e.g. missing items or invalid addresses) throw validation exceptions and record execution errors into the system error log.
