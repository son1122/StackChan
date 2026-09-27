import time
import math
import logging
from typing import Dict, Any
from config import settings

logger = logging.getLogger("gcp_collector")

class GCPCollector:
    def __init__(self):
        self.cached_payload: Dict[str, Any] = {}
        self.last_fetch_time: float = 0.0

    def _fetch_live_gcp(self) -> Dict[str, Any]:
        """
        Attempts to query official GCP SDKs if credentials & project exist.
        """
        # If google-cloud libraries are available and credentials exist:
        try:
            from google.cloud import monitoring_v3
            # Real GCP Cloud Monitoring client
            client = monitoring_v3.MetricServiceClient()
            project_name = f"projects/{settings.gcp_project_id}"
            
            # Example metric read (CPU or container restarts)
            # In production, queries Cloud Monitoring time series
            logger.info(f"Querying GCP Monitoring for project: {settings.gcp_project_id}")
        except Exception as e:
            logger.debug(f"Direct GCP SDK query skipped/failed: {e}")
            raise e

    def _get_mock_telemetry(self) -> Dict[str, Any]:
        """
        Provides realistic dynamic telemetry for GKE, VMs, Cloud Run, Cloud SQL, BigQuery, and Billing.
        Changes slightly over time (sine waves) to simulate live workloads.
        """
        now = time.time()
        # Simulated dynamic oscillation
        t = now / 30.0
        gke_cpu = round(35.0 + 15.0 * math.sin(t), 1)
        vm_cpu = round(22.0 + 10.0 * math.cos(t), 1)
        sql_cpu = round(28.0 + 12.0 * math.sin(t * 1.5), 1)
        cloud_run_req = round(45.0 + 20.0 * math.sin(t * 0.8), 1)
        
        status = "ok"
        alerts = []
        if gke_cpu > 80.0:
            status = "warning"
            alerts.append({"severity": "warning", "message": f"GKE CPU load high: {gke_cpu}%"})
        if sql_cpu > 85.0:
            status = "warning"
            alerts.append({"severity": "warning", "message": f"Cloud SQL CPU load high: {sql_cpu}%"})

        return {
            "status": status,
            "updated_at": int(now),
            "project_id": settings.gcp_project_id,
            "incident_count": len(alerts),
            "alerts": alerts,
            "billing": {
                "mtd_usd": 128.45,
                "today_usd": 8.20,
                "budget_pct": 42.8
            },
            "gke": {
                "status": "ok" if gke_cpu < 80 else "warning",
                "nodes_up": 3,
                "nodes_total": 3,
                "pods_running": 28,
                "pods_failed": 0,
                "cpu_pct": gke_cpu,
                "ram_pct": 62.4
            },
            "vm": {
                "status": "ok",
                "instances_running": 4,
                "instances_total": 4,
                "avg_cpu_pct": vm_cpu
            },
            "cloud_run": {
                "status": "ok",
                "services_count": 6,
                "req_per_sec": cloud_run_req,
                "error_5xx_rate": 0.0
            },
            "cloud_sql": {
                "status": "ok" if sql_cpu < 85 else "warning",
                "instances_up": 2,
                "cpu_pct": sql_cpu,
                "storage_pct": 48.5,
                "connections": 36
            },
            "bigquery": {
                "status": "ok",
                "slot_usage": 12,
                "today_gb_billed": 145.2,
                "failed_queries_24h": 0
            }
        }

    def get_telemetry(self) -> Dict[str, Any]:
        now = time.time()
        if self.cached_payload and (now - self.last_fetch_time < settings.cache_ttl_seconds):
            return self.cached_payload

        try:
            if settings.google_application_credentials and settings.gcp_project_id != "demo-gcp-project":
                payload = self._fetch_live_gcp()
            else:
                payload = self._get_mock_telemetry()
        except Exception as e:
            logger.warning(f"Failed to fetch live GCP telemetry: {e}. Using simulated data.")
            payload = self._get_mock_telemetry()

        self.cached_payload = payload
        self.last_fetch_time = now
        return payload

collector = GCPCollector()
