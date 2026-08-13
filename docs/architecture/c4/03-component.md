# C3: Component Diagram

## 🎯 Component Architecture
This document specifies the internal software components, Document controller hooks, background task handlers, Pydantic data schemas, image transformation utilities, and API client wrappers within `frappe_printrove`.

## 📊 Component ERD

```mermaid
erDiagram
    ItemHook ||--|| DesignJob : "enqueues on_update"
    BOMHook ||--|| ProductJob : "enqueues on_submit"
    SalesOrderHook ||--|| OrderJob : "enqueues on_submit"
    PurchaseOrderHook ||--|| OrderJob : "enqueues on_update"
    
    DesignJob ||--|| ImageUtils : "converts format"
    DesignJob ||--|| PrintroveClient : "calls create_design_from_url"
    DesignJob ||--|| DesignUrlRequest : "constructs payload"
    
    ProductJob ||--|| PrintroveClient : "calls create_product"
    ProductJob ||--|| ProductCreateRequest : "constructs payload"
    
    OrderJob ||--|| PrintroveClient : "calls get_serviceability & create_order"
    OrderJob ||--|| ServiceabilityRequest : "constructs payload"
    OrderJob ||--|| OrderCreateRequest : "constructs payload"
    OrderJob ||--|| PrintroveSettings : "reads supplier & accounts"
    
    PrintroveClient ||--|| PrintroveSettings : "fetches credentials"
    
    ItemHook {
        string module "frappe_printrove.printrove.doctype.item.item"
        string event "on_update"
    }

    BOMHook {
        string module "frappe_printrove.printrove.doctype.bom.bom"
        string event "on_submit"
    }

    SalesOrderHook {
        string module "frappe_printrove.printrove.doctype.sales_order.sales_order"
        string event "on_submit"
    }

    PurchaseOrderHook {
        string module "frappe_printrove.printrove.doctype.purchase_order.purchase_order"
        string event "on_update"
    }

    DesignJob {
        string function "frappe_printrove.jobs.design.create_design"
        int rate_limit_per_minute 60
        int retries 3
    }

    ProductJob {
        string function "frappe_printrove.jobs.product.create_product"
        int rate_limit_per_minute 60
        int retries 3
    }

    OrderJob {
        string orchestrator "frappe_printrove.jobs.order.process_printrove_purchase_order"
        string helper "frappe_printrove.jobs.order.create_purchase_order"
        int rate_limit_per_minute 30
        int retries 5
    }

    ImageUtils {
        string module "frappe_printrove.utils.image"
        string function "ensure_supported_image_format"
    }

    PrintroveClient {
        string module "frappe_printrove.client"
        string class "PrintroveClient"
    }

    PrintroveSettings {
        string doctype "Printrove Settings"
        string role "Configuration & Credential Storage"
    }

    DesignUrlRequest {
        string schema "frappe_printrove.schemas.design.DesignUrlRequest"
    }

    ProductCreateRequest {
        string schema "frappe_printrove.schemas.product.ProductCreateRequest"
    }

    ServiceabilityRequest {
        string schema "frappe_printrove.schemas.serviceability.ServiceabilityRequest"
    }

    OrderCreateRequest {
        string schema "frappe_printrove.schemas.order.OrderCreateRequest"
    }
```

## 📝 Component Descriptions

- **ItemHook**: Document lifecycle hook [`on_update`](frappe_printrove/printrove/doctype/item/item.py:4) detecting changes to Items in item group "Print Files" and scheduling design synchronization after transaction commit.
- **BOMHook**: Document lifecycle hook [`on_submit`](frappe_printrove/printrove/doctype/bom/bom.py:4) triggering automated product catalog generation on Printrove API upon BOM approval.
- **SalesOrderHook**: Document lifecycle hook [`on_submit`](frappe_printrove/printrove/doctype/sales_order/sales_order.py:4) initiating draft Purchase Order generation for drop-ship fulfillment.
- **PurchaseOrderHook**: Document lifecycle hook [`on_update`](frappe_printrove/printrove/doctype/purchase_order/purchase_order.py:4) detecting unfulfilled draft Purchase Orders assigned to supplier "Printrove" and launching the background fulfillment pipeline.
- **DesignJob**: Asynchronous worker task [`create_design`](frappe_printrove/jobs/design.py:8) checking for file attachments, waiting for upload events, normalizing image formats, and registering designs on Printrove.
- **ProductJob**: Asynchronous worker task [`create_product`](frappe_printrove/jobs/product.py:7) checking design readiness across print files, structuring coordinate placement vectors, and creating custom SKUs.
- **OrderJob**: Comprehensive fulfillment orchestrator [`process_printrove_purchase_order`](frappe_printrove/jobs/order.py:141) and sub-tasks (`update_po_shipping`, `create_order`, `submit_po`) managing the multi-step procurement and drop-shipping process.
- **ImageUtils**: Image manipulation helper [`ensure_supported_image_format`](frappe_printrove/utils/image.py:9) converting unsupported image formats (e.g., WEBP, BMP) to standard PNG using Pillow.
- **PrintroveClient**: Resilient HTTP client wrapper [`PrintroveClient`](frappe_printrove/client.py:13) managing token acquisition, TTL caching in Redis, and typed communication with Printrove REST endpoints.
- **PrintroveSettings**: Single DocType [`Printrove Settings`](frappe_printrove/printrove/doctype/printrove_settings/printrove_settings.py:8) storing API keys, supplier links, GL accounts, and available credit validation logic.
- **Pydantic Schemas**: Strict serialization and validation models defining API payloads ([`DesignUrlRequest`](frappe_printrove/schemas/design.py:6), [`ProductCreateRequest`](frappe_printrove/schemas/product.py:16), [`ServiceabilityRequest`](frappe_printrove/schemas/serviceability.py:4), [`OrderCreateRequest`](frappe_printrove/schemas/order.py:19)).
