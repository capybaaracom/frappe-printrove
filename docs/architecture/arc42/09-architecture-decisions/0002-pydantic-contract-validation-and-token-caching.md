# ADR 0002: Pydantic Contract Validation and Token Caching

## Status
Accepted

## Date
2026-08-13

## Context
Interacting with third-party fulfillment APIs requires strict payload serialization, attribute coercion, and resilient credential management. Unvalidated dynamic payloads risk malformed HTTP requests and downstream dispatch failures. Frequent token authentication calls introduce unnecessary latency and risk hitting rate limits.

## Decision
We implemented a dedicated API client wrapper integrated with Pydantic v2 data models:
- All request/response payloads (`DesignUrlRequest`, `ProductCreateRequest`, `ServiceabilityRequest`, `OrderCreateRequest`) are strictly validated via Pydantic schemas before HTTP transmission.
- Access tokens retrieved via `POST /api/external/token` are cached in Redis with a 3600-second TTL under `printrove_access_token:{email}` to minimize roundtrips.

## Consequences
### Positive
- Compile-time and runtime type safety preventing malformed request payloads.
- Drastic reduction in authentication overhead against Printrove endpoints.

### Negative & Risks
- Schema evolution on Printrove's API requires corresponding updates to Pydantic models.
- Mitigated via contract integration tests using recorded VCR fixtures.
