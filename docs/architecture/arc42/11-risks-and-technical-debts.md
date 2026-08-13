# Risks and Technical Debts

## 1. Single Points of Failure & External API Dependencies
- **Printrove API Downtime**: If the Printrove REST gateway experiences prolonged downtime exceeding worker retry limits, orders will remain suspended in error states.
  - *Mitigation*: Configured FastStream retry counts (up to 5 retries with exponential backoff) and manual re-trigger endpoints to resume stalled jobs upon external recovery.
- **Prepaid Wallet Depletion**: If available prepaid credits in the Printrove merchant account are depleted, procurement workflows are suspended.
  - *Mitigation*: The orchestrator cleanly waits for `Purchase Invoice` submission events; automated low-balance warning alerts should be integrated into accounting dashboards.

## 2. Technical Debt & Codebase Observations
- **Hardcoded Default Fallback Credentials**: In [`PrintroveClient.__init__`](apps/frappe_printrove/frappe_printrove/client.py:17), fallback default test credentials exist when `site_config.json` is missing.
  - *Mitigation*: Deprecate hardcoded fallbacks and enforce mandatory configuration in `site_config.json` or `Printrove Settings`.
- **Public URL Exposure for Private Files**: Printrove's design ingestion endpoint (`/api/external/designs/url`) fetches artwork images via HTTP.
  - *Mitigation*: For private files in ERPNext, ensure presigned S3 URLs or authenticated temporary proxy download links are used in multi-tenant cloud environments.
- **Default Weight & Pincode Assumptions**: In [`update_po_shipping`](apps/frappe_printrove/frappe_printrove/jobs/order.py:47), missing item weights default to 0.2kg and missing pincodes default to `110001`.
  - *Mitigation*: Add explicit validation requiring address pincodes and item gross weights on `Sales Order` validation before submission.
