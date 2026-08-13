# Cross-cutting Concepts

## 1. Authentication & Token Management
Authentication against the Printrove REST API uses JWT bearer tokens.
- The [`PrintroveClient.get_token`](apps/frappe_printrove/frappe_printrove/client.py:39) method issues `POST /api/external/token` with configured credentials.
- Returned tokens are cached in Redis with a 3600-second (1 hour) TTL under the cache key `printrove_access_token:{email}`.
- Requests automatically inject the cached token into HTTP `Authorization: Bearer {token}` headers.

## 2. Event-Driven Workflow Orchestration & Replay
The background processing subsystem utilizes `frappe-controller`'s event orchestration capabilities:
- **Non-blocking Wait (`frappe.wait_for`)**: When an asynchronous dependency is not ready (such as a pending image upload or low wallet balance), the orchestrator raises `frappe.DeferredJob` internally to suspend worker execution.
- **Child Job Isolation (`as_child=True`)**: Sub-tasks (e.g. calculating shipping, creating orders, submitting documents) are enqueued with `as_child=True` and awaited with `.result()`.
- **Deterministic Replay**: When a parent workflow resumes after suspension, finished child jobs return their cached results immediately without repeating external side effects.

## 3. Image Processing & Sanitization
Printrove requires images to be formatted strictly as JPEG, JPG, or PNG.
- The [`ensure_supported_image_format`](apps/frappe_printrove/frappe_printrove/utils/file.py:9) utility inspects incoming image binary headers using Pillow.
- Unsupported formats (e.g., WEBP, TIFF, BMP) are converted in-memory to standard PNG and re-attached as clean `File` records before external transmission.

## 4. Financial Validation & Prepaid Accounting
Before dispatching drop-ship orders to Printrove:
- The system verifies that the company's prepaid wallet balance in `tabGL Entry` is greater than or equal to the Purchase Order `grand_total`.
- If the balance is insufficient, the workflow pauses execution until an authorized user posts a new `Purchase Invoice` to credit the account.

## 5. Rate Limiting & Error Recovery
All external API jobs registered in [`hooks.py`](apps/frappe_printrove/frappe_printrove/hooks.py:10) specify explicit rate limits (30–60 req/min) and retry limits (3–5 retries).
- Transient errors (HTTP 429, 502, 503, 504, timeouts) raise natural exceptions to let FastStream execute exponential backoff.
- Deterministic errors (e.g. missing items or invalid addresses) throw `frappe.ValidationError` and log error traces to Frappe's Error Log.
