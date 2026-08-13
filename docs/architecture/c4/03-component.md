# C3: Component Diagram

## 🎯 Component Architecture
This document specifies the internal software components, Document controller hooks, background task handlers, Pydantic data schemas, file transformation utilities, and API client wrappers within `frappe_printrove`.

## 📊 Component ERD

```mermaid
erDiagram
    ItemHook ||--|| DesignJob : "enqueues on_update"
    BOMHook ||--|| ProductJob : "enqueues on_submit"
    SalesOrderHook ||--|| OrderJob : "enqueues on_submit"
    PurchaseOrderHook ||--|| OrderJob : "enqueues on_update"
    
    DesignJob ||--|| FileUtils : "converts format"
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
        string component "Item Lifecycle Hook"
        string event "on_update"
    }

    BOMHook {
        string component "BOM Lifecycle Hook"
        string event "on_submit"
    }

    SalesOrderHook {
        string component "Sales Order Lifecycle Hook"
        string event "on_submit"
    }

    PurchaseOrderHook {
        string component "Purchase Order Lifecycle Hook"
        string event "on_update"
    }

    DesignJob {
        string task "Design Creation Task"
        int rate_limit_per_minute 60
        int retries 3
    }

    ProductJob {
        string task "Product Configuration Task"
        int rate_limit_per_minute 60
        int retries 3
    }

    OrderJob {
        string task "Purchase Order Orchestrator"
        int rate_limit_per_minute 30
        int retries 5
    }

    FileUtils {
        string utility "Image Normalization Engine"
        string function "ensure_supported_image_format"
    }

    PrintroveClient {
        string service "Printrove API Client"
        string auth "Bearer Token Session Manager"
    }

    PrintroveSettings {
        string entity "Printrove Settings"
        string role "Configuration & Credential Storage"
    }

    DesignUrlRequest {
        string contract "Design Ingestion Schema"
    }

    ProductCreateRequest {
        string contract "Product Creation Schema"
    }

    ServiceabilityRequest {
        string contract "Serviceability Query Schema"
    }

    OrderCreateRequest {
        string contract "Order Placement Schema"
    }
```

## 📝 Component Descriptions

- **ItemHook**: Document lifecycle hook detecting changes to Items in the "Print Files" category and scheduling design synchronization after transaction commit.
- **BOMHook**: Document lifecycle hook triggering automated product catalog generation on Printrove API upon Bill of Materials approval.
- **SalesOrderHook**: Document lifecycle hook initiating draft Purchase Order generation for drop-ship fulfillment upon Sales Order submission.
- **PurchaseOrderHook**: Document lifecycle hook detecting unfulfilled draft Purchase Orders assigned to supplier "Printrove" and launching the background fulfillment pipeline.
- **DesignJob**: Asynchronous worker task validating file attachments, waiting for upload events, normalizing image formats, and registering artwork designs on Printrove.
- **ProductJob**: Asynchronous worker task validating design readiness across component print files, mapping coordinate placement vectors, and creating custom SKUs.
- **OrderJob**: Comprehensive fulfillment orchestrator and sub-tasks (shipping quote calculation, order placement, and PO submission) managing the multi-step procurement and drop-shipping process.
- **FileUtils**: Image and file manipulation helper converting unsupported image formats (such as WEBP or BMP) to standard PNG format using Pillow.
- **PrintroveClient**: Resilient HTTP client wrapper managing token acquisition, TTL caching in Redis, and typed communication with Printrove REST endpoints.
- **PrintroveSettings**: Single DocType storing API credentials, supplier links, Chart of Accounts configurations, and available credit validation logic.
- **Pydantic Schemas**: Strict serialization and validation contracts defining API request and response structures (`DesignUrlRequest`, `ProductCreateRequest`, `ServiceabilityRequest`, `OrderCreateRequest`).
