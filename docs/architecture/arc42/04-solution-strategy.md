# Solution Strategy

## 🎯 Solution Architecture & Design Strategy

The core architectural strategy of `frappe_printrove` resolves the complexities of integrating a real-time on-demand manufacturing API with an enterprise ERP system through the following core patterns:

### 1. FastStream & Frappe-Controller Orchestration
Instead of traditional blocking cron tasks or unmanaged RQ threads, `frappe_printrove` uses `frappe-controller` with FastStream. This provides:
- **Non-blocking Event Suspension (`frappe.wait_for`)**: When an asynchronous prerequisite (such as missing artwork files, pending design provisioning, or insufficient prepaid credit) is encountered, the worker suspends itself cleanly without blocking the thread pool or busy-polling the database.
- **Deterministic Replay Semantics**: Resumed workflows replay deterministically. By isolating all external HTTP calls and mutating operations inside sub-tasks (`as_child=True`), steps that have already executed successfully are skipped instantly using cached result indexes.
- **Integrated Rate Limiting & Backoff Retries**: All external API jobs are strictly rate-limited (30–60 req/min) and automatically retried upon network timeouts or 5xx server responses.

### 2. Pydantic-Powered Contract Verification
To avoid schema drift or silent serialization failures:
- Every outbound request and inbound response is strictly validated using Pydantic v2 data models ([`frappe_printrove/schemas/`](apps/frappe_printrove/frappe_printrove/schemas/)).
- All dimensional units, courier identifiers, and shipping payload addresses are verified before dispatch.

### 3. Transparent Image Transformation Layer
Printrove requires standard JPEG, JPG, or PNG images. Merchandisers frequently upload diverse image formats:
- The [`ensure_supported_image_format`](apps/frappe_printrove/frappe_printrove/utils/image.py:9) utility uses Pillow to inspect image headers in-memory.
- Any non-standard format (such as WEBP, BMP, or TIFF) is converted to PNG, saved as a new ERPNext `File` record, and dispatched seamlessly.

### 4. Financial Safeguards & Dynamic Freight Calculation
- Freight charges are calculated dynamically at order time via `POST /api/external/serviceability` using the destination pincode and aggregated line item weights.
- Prepaid wallet balances are checked against general ledger entries before order placement. If funds are insufficient, the order fulfillment workflow pauses safely until accounting posts a recharge invoice.
