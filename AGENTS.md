# Printrove API Documentation

> REST API documentation for Printrove print-on-demand fulfillment services, including authentication, catalog browsing, design management, pincode serviceability, and order handling.

## Overview
- Base URL: `https://api.printrove.com`
- Authentication: Bearer Token passed via HTTP Header (`Authorization: Bearer {your-token}`)

## Authentication API
- [Generate Token](https://api.printrove.com/docs/#generate-token): Generate an auth token using merchant email and password (`POST /api/external/token`).

## Catalog API
- [List All Categories](https://api.printrove.com/docs/#list-all-categories): Fetch all available product categories (`GET /api/external/categories`).
- [Get Parent Products](https://api.printrove.com/docs/#get-parent-products): Get parent products under a specific category ID (`GET /api/external/categories/{category_id}`).
- [Get Product Variants](https://api.printrove.com/docs/#get-product-variants): Get variant details for a specific product (`GET /api/external/categories/{category_id}/products/{product_id}`).

## Design Library API
- [List All Designs](https://api.printrove.com/docs/#list-all-designs): Retrieve uploaded designs in the library (`GET /api/external/designs`).
- [Add Design](https://api.printrove.com/docs/#add-design): Upload a design file directly (max 15MB, JPG/JPEG/PNG) (`POST /api/external/designs`).
- [Add Design using URL](https://api.printrove.com/docs/#add-design-using-url): Add a design using an image URL (`POST /api/external/designs/url`).
- [Delete Design](https://api.printrove.com/docs/#delete-design): Delete a design by ID (`DELETE /api/external/designs/{design_id}`).

## Orders API
- [Get Pincode Details](https://api.printrove.com/docs/#get-pincode-details): Retrieve region details for a given pincode (`GET /api/external/pincode/{pincode}`).
- [Serviceability](https://api.printrove.com/docs/#serviceability): Check delivery and COD serviceability for a destination pincode and weight (`GET /api/external/serviceability`).
- [List All Orders](https://api.printrove.com/docs/#list-all-orders): Retrieve a list of orders with optional tracking or reference number filters (`GET /api/external/orders`).
- [Get Order](https://api.printrove.com/docs/#get-order): Retrieve order details by order ID (`GET /api/external/orders/{order_id}`).
- [Create Order](https://api.printrove.com/docs/#create-order): Create a new fulfillment order with customer info, designs, and product variants (`POST /api/external/orders`).

## Product Library API
- [List All Products](https://api.printrove.com/docs/#list-all-products): List custom product SKUs saved in the Product Library (`GET /api/external/products`).
- [Get Product](https://api.printrove.com/docs/#get-product): Retrieve details of a specific SKU by ID (`GET /api/external/products/{product_id}`).
- [Create A Product](https://api.printrove.com/docs/#create-a-product): Save a new custom SKU product with print placement and variant mappings (`POST /api/external/products`).

# Rules

## Printrove API Documentation - Documentation & Live Crawl Index

### 🎯 Agent Instructions & Dynamic Crawling Directives

- When answering questions, checking models, or implementing features for `Printrove API Documentation`, DO NOT guess endpoints, parameters, or specifications.
- Use the `crawl4ai` MCP server (tools: `crawl`, `md`, or `read_url`) to dynamically fetch, scrape, and read documentation pages on-demand for accurate, up-to-date API references.
- Root Documentation URL: https://api.printrove.com/docs/

### 📚 Documentation Index (llms.txt)

- [https://api.printrove.com](https://api.printrove.com)