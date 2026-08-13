# Glossary

| Term | Definition |
| :--- | :--- |
| **BOM (Bill of Materials)** | Aggregate specification document linking finished goods, child components (blank apparel + print files), and production print coordinates. |
| **Cash on Delivery (COD)** | Payment method checked during courier serviceability calculations to ensure delivery feasibility. |
| **Design ID (`printrove_id`)** | Unique integer identifier returned by Printrove upon successfully ingesting an artwork image file. |
| **DocType** | Core metadata entity model in Frappe Framework representing database tables and domain aggregates. |
| **FastStream** | Python asynchronous streaming and messaging framework powering the event-driven queue orchestration in `frappe-controller`. |
| **frappe-controller** | Core orchestration extension monkey-patching `frappe.enqueue` and providing non-blocking suspension (`frappe.wait_for`) and job replay semantics. |
| **Print Placement** | Positional alignment of artwork on a garment (e.g. Front, Back, Left Sleeve, Right Sleeve, Neck) with dimensional coordinates (width, height, top, left offsets). |
| **Printrove** | Third-party print-on-demand manufacturing and dropshipping fulfillment provider. |
| **Product ID** | Upstream custom SKU identifier created on Printrove mapping a specific blank garment variant to one or more positioned designs. |
| **Purchase Order (PO)** | Procurement document in ERPNext routed to supplier "Printrove" containing drop-ship customer delivery instructions and order lines. |
| **Sales Order (SO)** | Retail sales transaction in ERPNext initiating the downstream manufacturing and fulfillment pipeline upon submission. |
| **Serviceability** | Real-time verification of postal pincode coverage, courier options, and live shipping rates for a specific consignment weight. |
| **Wallet Credit** | Prepaid financial balance maintained by the merchant in their Printrove account, validated against General Ledger entries prior to order dispatch. |
