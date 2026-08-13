# Runtime View

## 1. Scenario 1: Artwork Design Ingestion & Provisioning
Link to BPMN Behavioral Workflow: [Design Provisioning Workflow](../bpmn/01-design-provisioning.md)

### Runtime Interaction & Execution Steps
1. An operator or external API creates or updates an `Item` record with `item_group = "Print Files"`.
2. The [`on_update`](apps/frappe_printrove/frappe_printrove/printrove/doctype/item/item.py:4) document hook schedules `frappe_printrove.jobs.design.create_design` after MariaDB commits.
3. The worker begins execution. If no file is attached, the job suspends itself cleanly via `frappe.wait_for(event_key="after_insert", filters={"doctype": "File", ...})`.
4. When a file is uploaded, the worker wakes up and inspects the image format using [`ensure_supported_image_format`](apps/frappe_printrove/frappe_printrove/utils/image.py:9). Unsupported formats (such as WEBP or BMP) are converted in-memory to PNG.
5. The absolute file URL is formatted into [`DesignUrlRequest`](apps/frappe_printrove/frappe_printrove/schemas/design.py:6) and sent to Printrove via `POST /api/external/designs/url`.
6. The returned design ID is saved into `Item.printrove_id`.

---

## 2. Scenario 2: Bill of Materials (BOM) Product Configuration
Link to BPMN Behavioral Workflow: [Product Provisioning Workflow](../bpmn/02-product-provisioning.md)

### Runtime Interaction & Execution Steps
1. Merchandisers submit an approved `BOM` defining a custom garment with attached artwork print files and print coordinates.
2. The [`on_submit`](apps/frappe_printrove/frappe_printrove/printrove/doctype/bom/bom.py:4) hook schedules `frappe_printrove.jobs.product.create_product`.
3. The worker verifies that all child artwork items have their `printrove_id` generated. If an artwork item is still provisioning, it suspends execution (`frappe.wait_for(event_key="on_update", filters={"doctype": "Item", "name": item_code})`).
4. Once all artwork IDs are resolved, placement coordinates (`print_placement`, `print_width`, `print_height`, `print_top`, `print_left`) and blank product IDs are assembled into [`ProductCreateRequest`](apps/frappe_printrove/frappe_printrove/schemas/product.py:16).
5. The request is dispatched to `POST /api/external/products`. The resulting product ID is saved on both the `BOM` and the parent finished good `Item`.

---

## 3. Scenario 3: Sales Order Fulfillment Trigger
Link to BPMN Behavioral Workflow: [Sales Order Fulfillment Workflow](../bpmn/03-sales-order-fulfillment.md)

### Runtime Interaction & Execution Steps
1. A customer checkout or channel sync submits a retail `Sales Order`.
2. The [`on_submit`](apps/frappe_printrove/frappe_printrove/printrove/doctype/sales_order/sales_order.py:4) hook schedules `create_purchase_order`.
3. The job verifies if a draft `Purchase Order` already exists for this `Sales Order`. If none exists, it initializes a new draft PO mapped to supplier `"Printrove"`, copies line items, and inserts the document into MariaDB.

---

## 4. Scenario 4: Purchase Order Orchestration & Drop-Shipping
Link to BPMN Behavioral Workflow: [Purchase Order Fulfillment Workflow](../bpmn/04-purchase-order-fulfillment.md)

### Runtime Interaction & Execution Steps
1. The insertion of a draft `Purchase Order` triggers the [`on_update`](apps/frappe_printrove/frappe_printrove/printrove/doctype/purchase_order/purchase_order.py:4) hook, scheduling `process_printrove_purchase_order`.
2. **Item Readiness Check**: The orchestrator confirms all line items have upstream `printrove_id` values or suspends execution.
3. **Freight Rate Calculation**: The orchestrator spawns child job `update_po_shipping`, which aggregates weights, queries `GET /api/external/serviceability`, and updates PO taxes.
4. **Credit Verification**: The orchestrator checks available wallet balance via general ledger queries. If insufficient, it suspends until a new `Purchase Invoice` top-up is submitted.
5. **Printrove Order Creation**: The orchestrator spawns child job `create_order`, sending customer address and item IDs to `POST /api/external/orders`. It records `printrove_order_id`.
6. **PO Submission**: The orchestrator spawns child job `submit_po`, transitioning the PO to `docstatus = 1` and finalizing the workflow.
