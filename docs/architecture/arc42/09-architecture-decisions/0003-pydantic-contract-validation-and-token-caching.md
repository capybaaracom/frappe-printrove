# ADR 0003: Pydantic Contract Validation and Token Caching

## Status
Accepted

## Date
2024-04-11

## Context
Interacting with third-party fulfillment APIs requires strict payload serialization, attribute coercion, and resilient credential management. Unvalidated dynamic payloads risk malformed HTTP requests and downstream dispatch failures. Frequent token authentication calls introduce unnecessary latency and risk hitting rate limits.

## Decision
We implemented a dedicated [`PrintroveClient`](apps/frappe_printrove/frappe_printrove/client.py:13) wrapper integrated with Pydantic v2 schemas:
- All request/response payloads ([`DesignUrlRequest`](apps/frappe_printrove/frappe_printrove/schemas/design.py:6), [`ProductCreateRequest`](apps/frappe_printrove/frappe_printrove/schemas/product.py:16), [`ServiceabilityRequest`](apps/frappe_printrove/frappe_printrove/schemas/serviceability.py:4), [`OrderCreateRequest`](apps/frappe_printrove/frappe_printrove/schemas/order.py:19)) are strictly validated via Pydantic before HTTP transmission.
- Access tokens retrieved via `POST /api/external/token` are cached in Redis with a 3600-second TTL under `printrove_access_token:{email}` to minimize roundtrips.

## Consequences
### Positive
- Compile-time and runtime type safety preventing malformed request payloads.
- Drastic reduction in authentication overhead against Printrove endpoints.

### Negative & Risks
- Schema evolution on Printrove's API requires corresponding updates to Pydantic models.
- Mitigated via contract integration tests using VCR.py fixtures.
