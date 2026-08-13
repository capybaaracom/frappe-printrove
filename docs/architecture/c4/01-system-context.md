# C1: System Context Diagram

## 🎯 System Boundaries
This document defines the high-level system context, primary actors, and external system boundaries for the `frappe_printrove` application within the ERPNext ecosystem.

## 📊 Context ERD

```mermaid
erDiagram
    Customer ||--o{ SalesOrder : "places"
    OperationsTeam ||--o{ Item : "configures"
    OperationsTeam ||--o{ BOM : "defines"
    SalesOrder ||--|| PurchaseOrder : "triggers_fulfillment"
    PurchaseOrder }|--|| PrintroveAPI : "fulfilled_by"
    Item }|--|| PrintroveAPI : "registers_design"
    BOM }|--|| PrintroveAPI : "registers_product"
    FinanceTeam ||--o{ PurchaseInvoice : "recharges_wallet"
    PurchaseInvoice ||--o{ PurchaseOrder : "unblocks_credit"

    Customer {
        string customer_id PK
        string full_name
        string email
        string phone
    }

    SalesOrder {
        string sales_order_id PK
        string customer FK
        string shipping_address FK
        decimal grand_total
        string docstatus
    }

    PurchaseOrder {
        string purchase_order_id PK
        string sales_order FK
        string supplier FK
        string printrove_order_id
        decimal grand_total
        string docstatus
    }

    Item {
        string item_code PK
        string item_group
        string printrove_id
        string printrove_category_id
    }

    BOM {
        string bom_id PK
        string item FK
        string printrove_id
        int docstatus
    }

    PurchaseInvoice {
        string invoice_id PK
        string company
        decimal grand_total
        int docstatus
    }

    OperationsTeam {
        string role "Catalog & Fulfillment Operator"
    }

    FinanceTeam {
        string role "Accounts Payable & Credit Manager"
    }

    PrintroveAPI {
        string external_service "Print-on-Demand REST API"
        string endpoint "api.printrove.com"
    }
```

## 📝 Entity Descriptions

- **Customer**: End-user placing retail orders resulting in Sales Order records.
- **OperationsTeam**: Merchandising and warehouse personnel managing Item catalog assets, print file attachments, and Bill of Materials (BOM) specifications.
- **FinanceTeam**: Accounting personnel maintaining the Printrove prepaid wallet credit balance through Purchase Invoices and GL entries.
- **SalesOrder**: ERPNext transactional order document capturing items and destination customer shipping address.
- **PurchaseOrder**: Automated downstream procurement record routing fulfilled items directly to supplier "Printrove".
- **Item**: Core ERPNext inventory entity representing designs (item group "Print Files") and finished print-on-demand goods.
- **BOM**: Bill of Materials aggregate combining blank apparel garments with artwork files and positional print coordinates.
- **PurchaseInvoice**: Accounting invoice reflecting cash recharges and supplier settlement to maintain positive available credit balance.
- **PrintroveAPI**: External print-on-demand fulfillment gateway providing design upload, SKU mapping, courier serviceability checks, and drop-ship order placement.
