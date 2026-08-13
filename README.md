### Frappe Printrove

Printrove Integration for ERPNext.

## Lifecycle & Source of Truth

The Frappe Printrove integration synchronizes core business models between ERPNext and the Printrove Print-on-Demand platform. The integration operates asynchronously using the **Asymmetric Integration System**, strictly separating internal business logic from external API communications via a Canonical Data Model (CDM) and JSONata translation pipelines.

The codebase is split into two physical boundaries:
1. **Main App (`frappe_printrove/`)**: Contains pure ERPNext symmetric business logic. It emits and consumes only CDM events via asynchronous queues. It knows nothing about external APIs.
2. **Facade Package (`packages/frappe_printrove/`)**: Acts as the Anti-Corruption Layer. It handles HTTP clients, external polling, webhooks, and translates data between the CDM and Printrove's proprietary schema.

### 1. Design Synchronization (Item)
**Outbound Flow (Producer -> Package)**
- **Trigger**: When an `Item` of group "Print Files" is updated with a valid attached image (`file_url`).
- **Internal Action**: The main app evaluates a local JSONata template to convert the raw Item dictionary into a CDM representation. It enqueues this CDM payload as an outbound event to the `frappe_controller`.
- **Facade Action**: The `packages` worker picks up the queue, runs its own JSONata template to translate the CDM into Printrove's endpoint data model, and executes the `Create Design` API call.
- **Fulfillment**: Printrove responds with a `design_id`.
- **Retroactive Action**: The Facade pushes the `design_id` back to the internal app via a CDM event. Updating the design ID will retroactively trigger synchronization for any pending BOMs that were waiting for this design.

### 2. Product Synchronization (BOM)
**Inbound Flow (Poller -> Internal)**
- **Facade Action**: A scheduled job within the `packages` facade polls Printrove for available templates via the `get_products` API. Using a JSONata template, it translates the external API payload into a Canonical Data Model (CDM) event and enqueues it.
- **Internal Action**: The main app's Inbound Consumer receives the CDM event. It executes **Idempotency and Diffing Guardrails**, querying the local database for existing `Specification` and `BOM` records.
- **Fulfillment**: If the delta between the incoming CDM and the local DB is strictly zero, the event is immediately dropped to protect the database. If changes exist, it dynamically generates or updates the ERPNext `Specification` records and `BOM` templates.

### 3. Custom Product Generation (BOM -> Product)
**Outbound Flow (Producer -> Package)**
- **Trigger**: When a `BOM` is submitted, consisting of Printrove components (a Blank/Sub-Assembly and Print File designs).
- **Internal Action**: The system extracts the blank product ID, the variant ID, and the mapping of design IDs to specific placements. It evaluates a JSONata template to convert this into a CDM payload, and enqueues it.
- **Facade Action**: The `packages` worker picks up the queue, evaluates its JSONata template to translate the CDM to Printrove's `Create Product` schema, and executes the API call.
- **Fulfillment**: Printrove responds with a new custom `product_id`.
- **Retroactive Action**: The new `product_id` is pushed back via a CDM event to the BOM and its parent Item. The system then retroactively syncs any pending Sales Orders containing this new finished product.

### 4. Order Fulfillment (Sales Order)
**Outbound Flow (Producer -> Package)**
- **Trigger**: When a `Sales Order` containing Printrove-fulfilled items (out of stock) is submitted.
- **Internal Action**: 
  - The system creates a Draft `Purchase Order` for the Printrove items.
  - It validates that all Printrove items in the order have been synced (they must have a `printrove_id`).
  - It evaluates a local JSONata template to translate the Sales Order and Shipping data into a CDM payload, then enqueues it as an outbound event.
- **Facade Action**: 
  - The `packages` worker picks up the queue and translates the CDM to the proprietary Printrove order schema using its JSONata file.
  - The worker checks serviceability and shipping costs based on the customer's pincode and total weight via the Printrove API.
  - It validates that the company has sufficient Printrove credit to cover the estimated order cost.
  - It pushes the order to Printrove.
- **Fulfillment**: 
  - Printrove returns a final `order_cost` and an `order_id`.
  - The Draft `Purchase Order` is updated with exact per-item rates and actual shipping taxes, linked to the `printrove_order_id`, and automatically submitted.

### Installation

You can install this app using the [bench](https://github.com/frappe/bench) CLI:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app $URL_OF_THIS_REPO --branch main
bench install-app frappe_printrove
```

### Contributing

This app uses `pre-commit` for code formatting and linting. Please [install pre-commit](https://pre-commit.com/#installation) and enable it for this repository:

```bash
cd apps/frappe_printrove
pre-commit install
```

Pre-commit is configured to use the following tools for checking and formatting your code:

- ruff
- eslint
- prettier
- pyupgrade

### License

mit
