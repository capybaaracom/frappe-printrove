# Architecture Constraints

## Technical Constraints

1. **Python 3.14+ & Frappe Ecosystem**:
   - The application is built for Python 3.14+ within the Frappe / ERPNext bench environment.
   - Indentation style is strictly tab-based per Ruff configuration with double quotes for strings.
   - All database interactions must adhere to Frappe ORM and Document lifecycle hooks (`validate`, `on_update`, `on_submit`).
2. **Frappe Controller & FastStream Queueing**:
   - Direct invocation of background workers or blocking delays (`time.sleep`) is strictly forbidden.
   - All asynchronous tasks must be registered under controller events configuration with explicit rate limits and retry counts.
   - Multi-step workflows must use `frappe.wait_for` to suspend worker execution cleanly rather than polling database tables or external endpoints.
   - Replayed workflows must remain deterministic; side effects (such as external HTTP API calls) must be isolated within child jobs (`as_child=True`).
3. **Pydantic Validation**:
   - All communication with external Printrove REST endpoints must pass through strictly typed Pydantic v2 serialization schemas.
4. **Image Format & Dimension Standards**:
   - Printrove accepts JPEG, JPG, and PNG formats. Unsupported formats (such as WEBP or TIFF) must be automatically converted in-memory via Pillow before transmission.

## Organizational & Business Constraints

1. **Supplier Coupling**:
   - Procurement records must be linked to the designated supplier entity representing Printrove Products Private Limited (GSTIN: `33AAICP8487B1Z9`).
2. **Prepaid Wallet Credit Enforcement**:
   - Fulfillment jobs must never place orders against Printrove without verifying sufficient available balance in the company's prepaid ledger account (`printrove_credit_account`).

## Regulatory & Security Constraints

1. **API Credential Protection**:
   - API tokens and client secrets must never be hardcoded; they must be managed via encrypted configuration or Printrove Settings.
2. **GST Compliance**:
   - Downstream purchase orders and item definitions must adhere to Indian GST HSN coding standards (e.g. HSN `999900` or product-specific codes).
