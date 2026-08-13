# Risks and Technical Debts

## 1. Single Points of Failure & External API Dependencies
- **Printrove API Downtime**: If the Printrove REST gateway experiences prolonged downtime exceeding worker retry limits, orders will remain suspended in error states.
  - *Mitigation*: Configured FastStream retry counts (up to 5 retries with exponential backoff) and manual re-trigger endpoints to resume stalled jobs upon external recovery.
- **Prepaid Wallet Depletion**: If available prepaid credits in the Printrove merchant account are depleted, procurement workflows are suspended.
  - *Mitigation*: The orchestrator cleanly waits for Purchase Invoice submission events; automated low-balance warning alerts should be integrated into accounting dashboards.

## 2. Technical Debt & Observations
- **Hardcoded Default Fallback Credentials**: Fallback default test credentials should be strictly removed in production environments.
  - *Mitigation*: Enforce mandatory configuration via site configurations or Printrove Settings.
- **Public URL Exposure for Private Files**: Printrove's design ingestion endpoint fetches artwork images via HTTP.
  - *Mitigation*: For private files in ERPNext, ensure presigned S3 URLs or authenticated temporary proxy download links are used in multi-tenant cloud environments.
- **Default Weight & Pincode Assumptions**: Missing item weights or destination pincodes in customer address records default to fallback constants during shipping calculation.
  - *Mitigation*: Add explicit validation requiring address pincodes and item gross weights on Sales Order validation before submission.
