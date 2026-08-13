# Introduction and Goals

## Requirements Overview
`frappe_printrove` is an enterprise integration extension for ERPNext that bridges digital storefronts, product catalogs, bill of materials (BOM), and order procurement workflows with the Printrove print-on-demand fulfillment network.

The application automates the full lifecycle of custom apparel and merchandise manufacturing:
1. **Automated Artwork & Design Ingestion**: Automatically detects uploaded artwork files on `Item` records, verifies and sanitizes image formats (auto-converting WEBP/BMP/TIFF to PNG via Pillow), and provisions designs on Printrove API.
2. **Dynamic BOM & SKU Configuration**: Automatically maps ERPNext Bill of Materials containing artwork attachments and print coordinates (placement, width, height, offsets) to Printrove custom product SKUs.
3. **Decoupled Purchase Order Fulfillment**: Automatically intercepts retail `Sales Order` documents, spawns supplier-mapped `Purchase Order` documents, queries live shipping serviceability rates, validates available prepaid wallet credit balances, places drop-ship orders with Printrove, and submits procurement records.
4. **Resilient Asynchronous Execution**: Leverages `frappe-controller` and `FastStream` to execute multi-step workflows with non-blocking event suspension (`frappe.wait_for`), automatic retries, rate limiting, and replayable execution semantics.

## Quality Goals

| Priority | Quality Goal | Target Metric / Scenario |
| :--- | :--- | :--- |
| 1 | Fault Tolerance & Resilience | Zero dropped fulfillment jobs during transient Printrove API outages via FastStream exponential backoff retries and non-blocking event suspension. |
| 2 | Data Integrity & Consistency | 100% synchronization between ERPNext DocType states and Printrove upstream IDs (`printrove_id`), guaranteeing idempotency across replayed workflows. |
| 3 | Operational Efficiency | Complete automated order placement, shipping rate computation, and PO submission in < 3 seconds under normal network conditions. |
| 4 | Catalog Interoperability | Seamless conversion of diverse image formats to Printrove-compatible PNG/JPEG formats without operator intervention. |

## Stakeholders

| Department | Expectations |
| :--- | :--- |
| Business | Expand merchandise catalog without carrying inventory; guarantee margin accuracy through automated courier rate calculation. |
| Product | Provide an automated end-to-end drop-shipping pipeline that requires zero manual intervention between customer checkout and factory dispatch. |
| Design & Technology | Ensure seamless ingestion of creative artwork assets with strict coordinate placements and automatic image format sanitization. |
| IT & Infrastructure | Ensure background task isolation, rate limiting compliance (60 req/min), credential security, and zero worker thread exhaustion during external delays. |
| Customer Support | Provide real-time visibility into supplier order numbers (`printrove_order_id`) and delivery serviceability status on procurement records. |
