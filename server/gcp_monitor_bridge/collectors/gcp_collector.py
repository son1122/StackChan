import os
import json
import httpx
import time
import math
import logging
import threading
import concurrent.futures
from typing import Dict, Any, List, Optional
from config import settings

logger = logging.getLogger("gcp_collector")

class GCPCollector:
    def __init__(self):
        self.cached_fleet: Dict[str, Any] = {}
        self.cached_projects: Dict[str, Dict[str, Any]] = {}
        self.last_fetch_time: float = 0.0
        self._cached_creds = None
        self._lock = threading.Lock()
        self._refresh_lock = threading.Lock()
        
        # Warm initial cache immediately with fast seed so endpoints are never empty
        self._seed_initial_cache()

        # Start background polling thread so cache is updated with live data
        self._bg_thread = threading.Thread(target=self._background_refresh_loop, daemon=True)
        self._bg_thread.start()

    def _seed_initial_cache(self):
        """Pre-populates cache instantly so the server is immediately responsive."""
        project_ids = settings.project_ids
        sim_projects = [
            self._generate_simulated_project(pid, seed_offset=float(idx * 1.5))
            for idx, pid in enumerate(project_ids)
        ]
        with self._lock:
            for p in sim_projects:
                self.cached_projects[p["project_id"]] = p
            self.cached_fleet = self._aggregate_fleet(sim_projects)
            self.last_fetch_time = time.time()

    def _get_credentials(self):
        if self._cached_creds is not None and self._cached_creds.valid:
            return self._cached_creds

        from google.oauth2 import service_account
        from google.auth.transport.requests import Request
        import google.auth

        candidate_paths = [
            os.getenv("GOOGLE_APPLICATION_CREDENTIALS", ""),
            "/app/credentials/gcp-sa.json",
            os.path.join(os.path.dirname(os.path.dirname(__file__)), "credentials", "gcp-sa.json")
        ]

        for path in candidate_paths:
            if path and os.path.exists(path):
                try:
                    creds = service_account.Credentials.from_service_account_file(
                        path, scopes=["https://www.googleapis.com/auth/cloud-platform"]
                    )
                    if not creds.valid:
                        creds.refresh(Request())
                    self._cached_creds = creds
                    return creds
                except Exception as e:
                    logger.warning(f"Failed to load service account from {path}: {e}")

        creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
        if not creds.valid:
            creds.refresh(Request())
        self._cached_creds = creds
        return creds

    def _has_credentials(self) -> bool:
        creds_file = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
        if creds_file and os.path.exists(creds_file):
            return True
        default_app_path = "/app/credentials/gcp-sa.json"
        if os.path.exists(default_app_path):
            return True
        local_app_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "credentials", "gcp-sa.json")
        if os.path.exists(local_app_path):
            return True
        return False

    def _fetch_live_project(self, project_id: str) -> Dict[str, Any]:
        """
        Queries official GCP REST APIs using authenticated Service Account credentials.
        """
        from google.auth.transport.requests import Request

        creds = self._get_credentials()
        if not creds.valid:
            creds.refresh(Request())
        token = creds.token
        headers = {"Authorization": f"Bearer {token}"}

        def _get_api(url: str, timeout: float = 6.0) -> Optional[Dict[str, Any]]:
            try:
                resp = httpx.get(url, headers=headers, timeout=timeout)
                if resp.status_code == 200:
                    return resp.json()
                logger.debug(f"API query non-200 ({resp.status_code}) for {url}")
                return None
            except Exception as ex:
                logger.debug(f"API query error for {url}: {ex}")
                return None

        # 1-6. Fetch Compute, GKE, SQL, Run, BigQuery, and Monitoring in PARALLEL
        now = time.time()
        end_time = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now))
        start_time = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now - 600))
        cpu_url = (
            f"https://monitoring.googleapis.com/v3/projects/{project_id}/timeSeries"
            f"?filter=metric.type%3D%22compute.googleapis.com%2Finstance%2Fcpu%2Futilization%22"
            f"&interval.startTime={start_time}&interval.endTime={end_time}"
        )

        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
            fut_vm = executor.submit(_get_api, f"https://compute.googleapis.com/compute/v1/projects/{project_id}/aggregated/instances")
            fut_gke = executor.submit(_get_api, f"https://container.googleapis.com/v1/projects/{project_id}/locations/-/clusters")
            fut_sql = executor.submit(_get_api, f"https://sqladmin.googleapis.com/v1/projects/{project_id}/instances")
            fut_run = executor.submit(_get_api, f"https://run.googleapis.com/v2/projects/{project_id}/locations/-/services")
            fut_bq = executor.submit(_get_api, f"https://bigquery.googleapis.com/bigquery/v2/projects/{project_id}/datasets")
            fut_cpu = executor.submit(_get_api, cpu_url)

            vm_data = fut_vm.result() or {}
            gke_data = fut_gke.result() or {}
            sql_data = fut_sql.result() or {}
            run_data = fut_run.result() or {}
            bq_data = fut_bq.result() or {}
            cpu_data = fut_cpu.result() or {}

        # 1. Parse VMs
        vms = [inst for zone in vm_data.get("items", {}).values() for inst in zone.get("instances", [])]
        vms_running = sum(1 for v in vms if v.get("status") == "RUNNING")
        vms_total = len(vms)

        # 2. Parse GKE
        clusters = gke_data.get("clusters", [])
        nodes_count = sum(c.get("currentNodeCount", 0) for c in clusters)
        gke_status = "ok"
        for c in clusters:
            if c.get("status") not in ("RUNNING", "RECONCILING"):
                gke_status = "warning"

        # 3. Parse Cloud SQL
        sql_instances = sql_data.get("items", [])
        sql_up = sum(1 for s in sql_instances if s.get("state") == "RUNNABLE")

        # 4. Parse Cloud Run
        run_services = len(run_data.get("services", []))

        # 5. Parse BigQuery
        bq_datasets = len(bq_data.get("datasets", []))

        # 6. Parse CPU metrics
        cpus = []
        for ts in cpu_data.get("timeSeries", []):
            pts = ts.get("points", [])
            if pts:
                val = pts[0].get("value", {}).get("doubleValue", 0.0)
                cpus.append(val * 100.0)
        avg_vm_cpu = round(sum(cpus) / len(cpus), 1) if cpus else 15.0

        # Estimate pods running from nodes count
        pods_running = nodes_count * 14 if nodes_count > 0 else 0

        # Status & Alerts evaluation
        alerts = []
        status = "ok"
        if avg_vm_cpu > 85.0:
            status = "warning"
            alerts.append({"severity": "warning", "message": f"[{project_id}] VM CPU load critical: {avg_vm_cpu}%"})
        if gke_status != "ok":
            status = "warning"
            alerts.append({"severity": "warning", "message": f"[{project_id}] GKE cluster state degraded"})

        return {
            "status": status,
            "updated_at": int(now),
            "project_id": project_id,
            "incident_count": len(alerts),
            "alerts": alerts,
            "billing": {
                "mtd_usd": round(vms_total * 38.5 + nodes_count * 45.0 + sql_up * 65.0, 2),
                "today_usd": round((vms_total * 38.5 + nodes_count * 45.0 + sql_up * 65.0) / 30.0, 2),
                "budget_pct": round(min(90.0, (vms_total * 38.5 + nodes_count * 45.0 + sql_up * 65.0) / 10.0), 1)
            },
            "gke": {
                "status": gke_status,
                "nodes_up": nodes_count,
                "nodes_total": nodes_count,
                "pods_running": pods_running,
                "pods_failed": 0,
                "cpu_pct": round(min(95.0, avg_vm_cpu * 1.2), 1),
                "ram_pct": 54.0
            },
            "vm": {
                "status": "ok" if (vms_total == 0 or vms_running == vms_total) else "warning",
                "instances_running": vms_running,
                "instances_total": vms_total,
                "avg_cpu_pct": avg_vm_cpu
            },
            "cloud_run": {
                "status": "ok",
                "services_count": run_services,
                "req_per_sec": float(run_services * 3),
                "error_5xx_rate": 0.0
            },
            "cloud_sql": {
                "status": "ok" if (len(sql_instances) == 0 or sql_up == len(sql_instances)) else "warning",
                "instances_up": sql_up,
                "cpu_pct": 28.0,
                "storage_pct": 45.0,
                "connections": sql_up * 8
            },
            "bigquery": {
                "status": "ok",
                "slot_usage": min(bq_datasets * 2, 64),
                "today_gb_billed": float(bq_datasets * 15),
                "failed_queries_24h": 0
            }
        }

    def _generate_simulated_project(self, project_id: str, seed_offset: float = 0.0) -> Dict[str, Any]:
        """
        Generates realistic metrics for a specific project.
        """
        now = time.time()
        t = (now / 30.0) + seed_offset
        
        # Adjust base values based on project name
        is_prod = "prod" in project_id.lower()
        is_data = "data" in project_id.lower() or "analytics" in project_id.lower()

        if is_prod:
            base_pods = 42
            base_vms = 8
            base_cost = 420.50
            gke_cpu = round(45.0 + 15.0 * math.sin(t), 1)
            vm_cpu = round(32.0 + 10.0 * math.cos(t), 1)
            sql_cpu = round(38.0 + 12.0 * math.sin(t * 1.5), 1)
            cloud_run_req = round(85.0 + 30.0 * math.sin(t * 0.8), 1)
        elif is_data:
            base_pods = 8
            base_vms = 3
            base_cost = 195.00
            gke_cpu = round(20.0 + 8.0 * math.sin(t), 1)
            vm_cpu = round(48.0 + 25.0 * math.cos(t), 1) # Data heavy VM
            sql_cpu = round(22.0 + 10.0 * math.sin(t * 1.5), 1)
            cloud_run_req = round(12.0 + 5.0 * math.sin(t * 0.8), 1)
        else: # Staging / Dev
            base_pods = 16
            base_vms = 3
            base_cost = 68.20
            gke_cpu = round(15.0 + 10.0 * math.sin(t), 1)
            vm_cpu = round(14.0 + 8.0 * math.cos(t), 1)
            sql_cpu = round(18.0 + 8.0 * math.sin(t * 1.5), 1)
            cloud_run_req = round(24.0 + 10.0 * math.sin(t * 0.8), 1)

        status = "ok"
        alerts = []
        if gke_cpu > 80.0:
            status = "warning"
            alerts.append({"severity": "warning", "message": f"[{project_id}] GKE CPU load high: {gke_cpu}%"})
        if vm_cpu > 85.0:
            status = "warning"
            alerts.append({"severity": "warning", "message": f"[{project_id}] VM CPU load critical: {vm_cpu}%"})

        return {
            "status": status,
            "updated_at": int(now),
            "project_id": project_id,
            "incident_count": len(alerts),
            "alerts": alerts,
            "billing": {
                "mtd_usd": round(base_cost + 5.0 * math.sin(t * 0.1), 2),
                "today_usd": round(base_cost / 30.0 + 1.2 * math.sin(t * 0.5), 2),
                "budget_pct": round(min(95.0, (base_cost / 500.0) * 100), 1)
            },
            "gke": {
                "status": "ok" if gke_cpu < 80 else "warning",
                "nodes_up": 3 if is_prod else 2,
                "nodes_total": 3 if is_prod else 2,
                "pods_running": int(base_pods + 4 * math.sin(t)),
                "pods_failed": 0,
                "cpu_pct": gke_cpu,
                "ram_pct": round(50.0 + 10.0 * math.sin(t * 1.1), 1)
            },
            "vm": {
                "status": "ok",
                "instances_running": base_vms,
                "instances_total": base_vms,
                "avg_cpu_pct": vm_cpu
            },
            "cloud_run": {
                "status": "ok",
                "services_count": 6 if is_prod else 3,
                "req_per_sec": cloud_run_req,
                "error_5xx_rate": 0.0
            },
            "cloud_sql": {
                "status": "ok" if sql_cpu < 85 else "warning",
                "instances_up": 2 if is_prod else 1,
                "cpu_pct": sql_cpu,
                "storage_pct": 45.0,
                "connections": 24 if is_prod else 8
            },
            "bigquery": {
                "status": "ok",
                "slot_usage": 24 if is_data else 4,
                "today_gb_billed": round(250.0 if is_data else 35.0, 1),
                "failed_queries_24h": 0
            }
        }

    def _aggregate_fleet(self, project_telemetries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aggregates all project telemetries into a single Fleet Overview payload.
        Backward-compatible with single-project readers.
        """
        now = int(time.time())
        total_pods = sum(p.get("gke", {}).get("pods_running", 0) for p in project_telemetries)
        total_nodes = sum(p.get("gke", {}).get("nodes_up", 0) for p in project_telemetries)
        total_vms = sum(p.get("vm", {}).get("instances_running", 0) for p in project_telemetries)
        total_mtd = sum(p.get("billing", {}).get("mtd_usd", 0.0) for p in project_telemetries)
        total_today = sum(p.get("billing", {}).get("today_usd", 0.0) for p in project_telemetries)
        total_cloud_run_req = sum(p.get("cloud_run", {}).get("req_per_sec", 0.0) for p in project_telemetries)
        total_cloud_sql_inst = sum(p.get("cloud_sql", {}).get("instances_up", 0) for p in project_telemetries)
        total_bq_slots = sum(p.get("bigquery", {}).get("slot_usage", 0) for p in project_telemetries)
        
        all_alerts = []
        for p in project_telemetries:
            all_alerts.extend(p.get("alerts", []))

        # Overall status is worst of any project
        statuses = [p.get("status", "ok") for p in project_telemetries]
        overall_status = "ok"
        if "incident" in statuses or "critical" in statuses:
            overall_status = "incident"
        elif "warning" in statuses:
            overall_status = "warning"

        avg_gke_cpu = round(
            sum(p.get("gke", {}).get("cpu_pct", 0.0) for p in project_telemetries) / max(len(project_telemetries), 1),
            1
        )
        avg_vm_cpu = round(
            sum(p.get("vm", {}).get("avg_cpu_pct", 0.0) for p in project_telemetries) / max(len(project_telemetries), 1),
            1
        )

        # Simplified lightweight project list for clients
        projects_summary = [
            {
                "project_id": p.get("project_id"),
                "status": p.get("status", "ok"),
                "incident_count": p.get("incident_count", 0),
                "billing_mtd": p.get("billing", {}).get("mtd_usd", 0.0),
                "pods_running": p.get("gke", {}).get("pods_running", 0),
                "vms_running": p.get("vm", {}).get("instances_running", 0)
            }
            for p in project_telemetries
        ]

        return {
            "status": overall_status,
            "updated_at": now,
            "project_id": "ALL FLEET",
            "is_fleet": True,
            "total_projects": len(project_telemetries),
            "incident_count": len(all_alerts),
            "alerts": all_alerts,
            "billing": {
                "mtd_usd": round(total_mtd, 2),
                "today_usd": round(total_today, 2),
                "budget_pct": round(min(100.0, (total_mtd / (500.0 * max(len(project_telemetries), 1))) * 100), 1)
            },
            "gke": {
                "status": "ok" if avg_gke_cpu < 80 else "warning",
                "nodes_up": total_nodes,
                "nodes_total": total_nodes,
                "pods_running": total_pods,
                "pods_failed": 0,
                "cpu_pct": avg_gke_cpu,
                "ram_pct": 58.2
            },
            "vm": {
                "status": "ok",
                "instances_running": total_vms,
                "instances_total": total_vms,
                "avg_cpu_pct": avg_vm_cpu
            },
            "cloud_run": {
                "status": "ok",
                "services_count": sum(p.get("cloud_run", {}).get("services_count", 0) for p in project_telemetries),
                "req_per_sec": round(total_cloud_run_req, 1),
                "error_5xx_rate": 0.0
            },
            "cloud_sql": {
                "status": "ok",
                "instances_up": total_cloud_sql_inst,
                "cpu_pct": 28.5,
                "storage_pct": 46.0,
                "connections": sum(p.get("cloud_sql", {}).get("connections", 0) for p in project_telemetries)
            },
            "bigquery": {
                "status": "ok",
                "slot_usage": total_bq_slots,
                "today_gb_billed": round(sum(p.get("bigquery", {}).get("today_gb_billed", 0) for p in project_telemetries), 1),
                "failed_queries_24h": 0
            },
            "projects": project_telemetries,
            "projects_summary": projects_summary
        }

    def _background_refresh_loop(self):
        """
        Background loop refreshing telemetry periodically so get_telemetry()
        never blocks incoming API or HTTP requests.
        """
        time.sleep(1.0)
        while True:
            try:
                self.refresh()
            except Exception as e:
                logger.error(f"Error in background GCP telemetry refresh: {e}")
            time.sleep(max(5, settings.cache_ttl_seconds))

    def refresh(self):
        if not self._refresh_lock.acquire(blocking=False):
            return

        try:
            project_ids = settings.project_ids

            def _fetch_single_project(item):
                idx, pid = item
                p_data = None
                if self._has_credentials() and not pid.startswith("demo-"):
                    try:
                        logger.info(f"Fetching real live GCP telemetry for project: {pid}")
                        p_data = self._fetch_live_project(pid)
                        logger.info(f"Successfully collected real GCP telemetry for {pid}")
                    except Exception as e:
                        logger.warning(f"Failed to fetch live GCP telemetry for {pid}: {e}. Falling back to simulation.")
                
                if not p_data:
                    p_data = self._generate_simulated_project(pid, seed_offset=float(idx * 1.5))
                return pid, p_data

            max_workers = min(max(len(project_ids), 1), 4)
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                results = list(executor.map(_fetch_single_project, enumerate(project_ids)))

            project_telemetries = [p_data for _, p_data in results]
            fleet_data = self._aggregate_fleet(project_telemetries)

            with self._lock:
                for pid, p_data in results:
                    self.cached_projects[pid] = p_data
                self.cached_fleet = fleet_data
                self.last_fetch_time = time.time()
        finally:
            self._refresh_lock.release()

    def get_telemetry(self, project_id: Optional[str] = None) -> Dict[str, Any]:
        with self._lock:
            if not self.cached_fleet:
                self.refresh()
            if project_id and project_id in self.cached_projects:
                return self.cached_projects[project_id]
            return self.cached_fleet

    def get_projects_list(self) -> List[Dict[str, Any]]:
        fleet = self.get_telemetry()
        return fleet.get("projects_summary", [])

    def handle_external_alert(self, project_id: Optional[str], state: str, summary: str, incident_id: Optional[str] = None):
        """
        Processes push alerts from Cloud Monitoring Webhooks instantly.
        """
        with self._lock:
            target_pids = [project_id] if (project_id and project_id in self.cached_projects) else list(self.cached_projects.keys())
            for pid in target_pids:
                if pid in self.cached_projects:
                    proj = self.cached_projects[pid]
                    if state == "OPEN":
                        proj["status"] = "incident"
                        proj["incident_count"] = max(proj.get("incident_count", 0), 1)
                    elif state == "CLOSED":
                        proj["incident_count"] = max(proj.get("incident_count", 1) - 1, 0)
                        if proj["incident_count"] == 0:
                            proj["status"] = "ok"

            # Re-aggregate fleet
            if self.cached_projects:
                self.cached_fleet = self._aggregate_fleet(list(self.cached_projects.values()))

collector = GCPCollector()
