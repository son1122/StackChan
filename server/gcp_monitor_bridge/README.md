# StackChan GCP Monitor Bridge

Lightweight API bridge that aggregates telemetry from **Google Cloud Platform (GCP)** and formats it into compact JSON for the **StackChan ESP32-S3 robot**.

## Features
- **Monitored Services**:
  - **GKE**: Node count, Pod health, CPU/RAM utilization %
  - **Compute Engine (VMs)**: Running instance count, average CPU load
  - **Cloud Run**: Services count, requests/sec, 5xx error rate
  - **Cloud SQL**: Instance state, CPU load, storage utilization %, active connections
  - **BigQuery**: Slot utilization, daily bytes scanned/billed, failed queries
  - **Cloud Billing**: Month-to-date spend, daily cost, budget percentage
- **Endpoints**:
  - `GET /healthz`: Health check
  - `GET /api/v1/gcp/status`: Full detailed JSON for StackChan's interactive multi-card dashboard
  - `GET /api/v1/gcp/summary`: 1-line ticker summary for ambient screensaver mode

## Quick Start (Docker)

```bash
docker compose up -d --build
```

Access the API at `http://localhost:8080/api/v1/gcp/status`.
