# Quality Requirements

## Quality Requirements Overview
This chapter defines the primary non-functional and quality characteristics for `frappe_printrove`, using quantitative metrics and concrete evaluation scenarios.

## Quality Scenarios

| ID | Quality Attribute | Source | Stimulus | Artifact / Environment | Response | Measure |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| QS-01 | Reliability & Recovery | Printrove API | Transient 502 / 504 network error during order creation | Production Worker Cluster | FastStream worker catches HTTP exception, triggers exponential backoff retry up to 5 times without marking job as failed | Zero lost orders; 100% recovery once API recovers |
| QS-02 | Performance & Latency | Sales Order Hook | Sales order submission event | Gunicorn Web Process | Hook schedules asynchronous PO generation after MariaDB commit without blocking HTTP response | User-perceived checkout latency < 150ms |
| QS-03 | Data Integrity | Concurrent Operators | Simultaneous updates to Items or BOMs | FastStream Replay Engine | Job reads cached child results and checks `printrove_id` before invoking external APIs | Zero duplicate SKUs or designs created on Printrove |
| QS-04 | Compatibility | Merchandiser | Upload of WEBP / BMP artwork images | Image Processing Utility | `ensure_supported_image_format` detects non-standard headers and converts to PNG | 100% conversion success rate with zero HTTP 400 rejection on Printrove |
| QS-05 | Financial Safety | Finance Team | Low prepaid wallet balance on order creation | Purchase Order Orchestrator | Workflow suspends non-blockingly until top-up Purchase Invoice is submitted | Zero unbilled overdrafts or rejected orders due to insufficient funds |
