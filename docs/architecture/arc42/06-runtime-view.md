# Runtime View

## 1. Scenario 1: Artwork Design Ingestion & Provisioning
Link to BPMN Behavioral Workflow: [Design Provisioning Workflow](../bpmn/01-design-provisioning.md)

### Runtime Interaction & Execution Steps
1. An operator or external API creates or updates an `Item` record with `item_group = "Print Files"`.
2. The Item document hook schedules design synchronization after MariaDB transaction commit.
3. The worker begins execution. If no file is attached, the job suspends itself cleanly via non-blocking event listening (`frappe.wait_for`).
4. When a file is uploaded, the worker wakes up and inspects the image format. Unsupported formats (such as WEBP or BMP) are converted in-memory to PNG.
5. The absolute file URL is formatted into the `DesignUrlRequest` schema and sent to Printrove via `POST /api/external/designs/url`.
6. The returned design ID is saved into `Item.printrove_id`.

---

## 2. Scenario 2: Bill of Materials (BOM) Product Configuration
Link to BPMN Behavioral Workflow: [Product Provisioning Workflow](../bpmn/02-product-provisioning.md)

### Runtime Interaction & Execution Steps
1. Merchandisers submit an approved `BOM` defining a custom garment with attached artwork print files and print coordinates.
2. The BOM hook schedules product catalog creation on the background queue.
3. The worker verifies that all child artwork items have their `printrove_id` generated. If an artwork item is still provisioning, it suspends execution (`frappe.wait_for`).
4. Once all artwork IDs are resolved, placement coordinates (`print_placement`, `print_width`, `print_height`, `print_top`, `print_left`) and blank product IDs are assembled into `ProductCreateRequest`.
5. The request is dispatched to `POST /api/external/products`. The resulting product ID is saved on both the `BOM` and the parent finished good `Item`.

---

## 3. Scenario 3: Sales Order Fulfillment Trigger
Link to BPMN Behavioral Workflow: [Sales Order Fulfillment Workflow](../bpmn/03-sales-order-fulfillment.md)

### Runtime Interaction & Execution Steps
1. A customer checkout or channel sync submits a retail `Sales Order`.
2. The Sales Order hook schedules draft Purchase Order creation.
3. The job verifies if a draft `Purchase Order` already exists for this `Sales Order`. If none exists, it initializes a new draft PO mapped to supplier `"Printrove"`, copies line items, and inserts the document into MariaDB.

---

## 4. Scenario 4: Purchase Order Orchestration & Drop-Shipping
Link to BPMN Behavioral Workflow: [Purchase Order Fulfillment Workflow](../bpmn/04-purchase-order-fulfillment.md)

### Runtime Interaction & Execution Steps
1. The insertion of a draft `Purchase Order` triggers the Purchase Order hook, scheduling the fulfillment orchestrator.
2. **Item Readiness Check**: The orchestrator confirms all line items have upstream `printrove_id` values or suspends execution.
3. **Freight Rate Calculation**: The orchestrator spawns a child job that aggregates weights, queries `GET /api/external/serviceability`, and updates PO taxes.
4. **Credit Verification**: The orchestrator checks available wallet balance via general ledger queries. If insufficient, it suspends until a new `Purchase Invoice` top-up is submitted.
5. **Printrove Order Creation**: The orchestrator spawns a child job sending customer address and item IDs to `POST /api/external/orders`. It records `printrove_order_id`.
6. **PO Submission**: The orchestrator spawns a child job to submit the document, transitioning the PO to `docstatus = 1` and finalizing the workflow.

---

## 5. Scenario 5: Chart of Accounts & Purchase Invoice Wallet Recharge
Link to BPMN Behavioral Workflow: [Wallet Credit Accounting & Purchase Invoice Recharge Workflow](../bpmn/05-chart-of-accounts-and-purchase-invoice.md)

### Runtime Interaction & Execution Steps
1. **Initial Credit Verification Failure**: During credit validation, the orchestrator detects that available credit (`GL Balance - Unbilled POs`) is less than the Purchase Order total.
2. **Non-blocking Job Suspension**: The FastStream worker calls `frappe.wait_for`, saving the job state and unblocking worker threads.
3. **Finance Team Action**: The finance department posts a payment entry or records an advance recharge by creating and submitting a `Purchase Invoice` linked to supplier `"Printrove"`.
4. **Ledger Posting**: Submitting the invoice posts `tabGL Entry` records debiting the Printrove Wallet Credit asset account (`printrove_credit_account`).
5. **Event Emission & Resumption**: The Purchase Invoice submission event satisfies the orchestrator match condition, automatically promoting and waking up the suspended task.
6. **Re-validation & Order Placement**: The orchestrator re-evaluates the wallet credit balance, validates that funds are now sufficient, and seamlessly proceeds to child job order placement.
