import os
import time
import secrets
import logging
import threading
from typing import Dict, Any, List, Optional
import uvicorn
from fastapi import FastAPI, Depends, HTTPException, Security, Header, Request, status
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader, HTTPBasic, HTTPBasicCredentials
from collectors.gcp_collector import collector
from config import settings
from dashboard import get_dashboard_html

logger = logging.getLogger("gcp_bridge")

app = FastAPI(
    title="StackChan GCP Monitor Bridge",
    description="Bridge API aggregating GCP services (GKE, VMs, Cloud Run, Cloud SQL, BigQuery, Billing) for StackChan robot",
    version="1.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

security_basic = HTTPBasic(auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_authentication(
    credentials: HTTPBasicCredentials | None = Depends(security_basic),
    api_key: str | None = Security(api_key_header),
    x_auth_user: str | None = Header(None, alias="X-Auth-User"),
    x_auth_pass: str | None = Header(None, alias="X-Auth-Password"),
):
    """
    Validates either:
    1. HTTP Basic Auth (Authorization: Basic base64(user:pass))
    2. Custom Headers (X-Auth-User & X-Auth-Password)
    3. API Key Header (X-API-Key)
    """
    has_api_key_configured = bool(settings.bridge_api_key)
    has_basic_configured = bool(settings.bridge_username and settings.bridge_password)
    
    # Security: Fail closed by default unless ALLOW_ANONYMOUS is explicitly enabled
    if not has_api_key_configured and not has_basic_configured:
        if os.getenv("ALLOW_ANONYMOUS", "").lower() in ("true", "1", "yes"):
            return True
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: Bridge security credentials not configured",
            headers={"WWW-Authenticate": "Basic realm=\"StackChan GCP Bridge\""},
        )

    # 1. HTTP Basic Authentication
    if credentials:
        user_matches = secrets.compare_digest(credentials.username, settings.bridge_username)
        pass_matches = secrets.compare_digest(credentials.password, settings.bridge_password)
        if user_matches and pass_matches:
            return True

    # 2. Custom X-Auth-User / X-Auth-Password headers
    if x_auth_user and x_auth_pass:
        user_matches = secrets.compare_digest(x_auth_user, settings.bridge_username)
        pass_matches = secrets.compare_digest(x_auth_pass, settings.bridge_password)
        if user_matches and pass_matches:
            return True

    # 3. API Key Header
    if settings.bridge_api_key and api_key and secrets.compare_digest(api_key, settings.bridge_api_key):
        return True

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Unauthorized: Invalid or missing authentication credentials",
        headers={"WWW-Authenticate": "Basic realm=\"StackChan GCP Bridge\""},
    )

class RobotRegistry:
    def __init__(self):
        self._robots: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def record_heartbeat(
        self,
        mac: str,
        ip: str,
        project: Optional[str] = None,
        battery: Optional[str] = None,
        charging: Optional[str] = None,
        version: Optional[str] = None
    ):
        if not mac:
            return
        now = time.time()
        batt_val = None
        if battery is not None and str(battery).isdigit():
            batt_val = max(0, min(100, int(battery)))

        is_charging = charging in ("1", "true", "True", True)

        with self._lock:
            self._robots[mac] = {
                "mac": mac,
                "ip": ip,
                "project": project or "ALL FLEET",
                "battery": batt_val,
                "charging": is_charging,
                "version": version or "1.0.0",
                "last_seen": now,
            }

    def get_robots(self) -> List[Dict[str, Any]]:
        now = time.time()
        result = []
        with self._lock:
            for mac, r in self._robots.items():
                sec_ago = int(now - r["last_seen"])
                is_online = sec_ago < 60
                result.append({
                    **r,
                    "online": is_online,
                    "last_seen_sec_ago": sec_ago
                })
        return sorted(result, key=lambda x: x["last_seen"], reverse=True)

robot_registry = RobotRegistry()

@app.get("/healthz")
async def health_check():
    return {"status": "healthy", "service": "stackchan-gcp-bridge"}

@app.get("/api/v1/gcp/status", dependencies=[Depends(verify_authentication)])
async def get_gcp_status(
    request: Request,
    project: str | None = None,
    x_robot_mac: Optional[str] = Header(None, alias="X-Robot-MAC"),
    x_robot_battery: Optional[str] = Header(None, alias="X-Robot-Battery"),
    x_robot_charging: Optional[str] = Header(None, alias="X-Robot-Charging"),
    x_robot_project: Optional[str] = Header(None, alias="X-Robot-Project"),
    x_robot_version: Optional[str] = Header(None, alias="X-Robot-Version"),
):
    """
    Primary endpoint for StackChan ESP32-S3.
    Returns compact, high-efficiency JSON summary of GCP services (Fleet or specific project).
    Also registers live robot presence, battery, and target project.
    """
    client_ip = request.client.host if request.client else "unknown"
    if x_robot_mac:
        robot_registry.record_heartbeat(
            mac=x_robot_mac,
            ip=client_ip,
            project=x_robot_project or project,
            battery=x_robot_battery,
            charging=x_robot_charging,
            version=x_robot_version
        )
    return collector.get_telemetry(project_id=project)

@app.get("/api/v1/gcp/robots", dependencies=[Depends(verify_authentication)])
async def get_connected_robots():
    """
    Returns list of connected physical StackChan robots with battery, IP, and assigned project.
    """
    return {"robots": robot_registry.get_robots()}

@app.post("/api/v1/gcp/webhook", dependencies=[Depends(verify_authentication)])
async def gcp_alert_webhook(payload: Dict[str, Any]):
    """
    Receives incident push alerts directly from Google Cloud Monitoring Alerting channels.
    Immediately updates the project state so connected StackChans react in real-time.
    """
    incident = payload.get("incident", {})
    state = incident.get("state", "OPEN").upper()
    project_id = incident.get("scoping_project_id") or incident.get("project_id")
    summary = incident.get("summary") or incident.get("condition_name") or "GCP Cloud Monitoring Alert"
    incident_id = incident.get("incident_id")

    logger.warning(f"Received GCP Alert Webhook: state={state}, project={project_id}, summary={summary}")

    collector.handle_external_alert(
        project_id=project_id,
        state=state,
        summary=summary,
        incident_id=incident_id
    )

    return {
        "status": "processed",
        "state": state,
        "project_id": project_id,
        "summary": summary
    }

@app.get("/api/v1/gcp/projects", dependencies=[Depends(verify_authentication)])
async def get_gcp_projects():
    """
    Returns list of all monitored projects with basic health metrics.
    """
    return collector.get_projects_list()

@app.get("/api/v1/gcp/summary", dependencies=[Depends(verify_authentication)])
async def get_gcp_summary():
    """
    Shorter 1-line summary for ambient screensaver and text tickers.
    """
    data = collector.get_telemetry()
    status_str = data.get("status", "ok").upper()
    gke_pods = data.get("gke", {}).get("pods_running", 0)
    vm_count = data.get("vm", {}).get("instances_running", 0)
    mtd = data.get("billing", {}).get("mtd_usd", 0.0)
    alerts = data.get("incident_count", 0)
    total_projects = data.get("total_projects", 1)
    
    return {
        "status": status_str,
        "ticker": f"[{status_str}] Fleet ({total_projects} Projects): {gke_pods} Pods | {vm_count} VMs | ${mtd:.2f} MTD | Alerts: {alerts}",
        "incident_count": alerts,
        "total_projects": total_projects
    }

@app.get("/", response_class=HTMLResponse, dependencies=[Depends(verify_authentication)])
@app.get("/dashboard", response_class=HTMLResponse, dependencies=[Depends(verify_authentication)])
async def get_dashboard():
    """
    Renders interactive web dashboard with animated StackChan avatar and real-time metrics.
    """
    return HTMLResponse(content=get_dashboard_html(), status_code=200)

@app.get("/metrics", dependencies=[Depends(verify_authentication)])
async def get_prometheus_metrics():
    """
    Prometheus metrics exporter for GCP fleet monitoring.
    """
    telemetry = collector.get_telemetry()
    lines = [
        "# HELP stackchan_gcp_status 1 if fleet is healthy, 0 if warning or incident",
        "# TYPE stackchan_gcp_status gauge",
        f"stackchan_gcp_status {1 if telemetry.get('status') == 'ok' else 0}",
        "# HELP stackchan_gcp_incident_count Total active alerts and incidents",
        "# TYPE stackchan_gcp_incident_count gauge",
        f"stackchan_gcp_incident_count {telemetry.get('incident_count', 0)}",
    ]
    for p in telemetry.get("projects", []):
        pid = p.get("project_id", "unknown")
        vm_running = p.get("vm", {}).get("instances_running", 0)
        vm_total = p.get("vm", {}).get("instances_total", 0)
        vm_cpu = p.get("vm", {}).get("avg_cpu_pct", 0.0)
        nodes = p.get("gke", {}).get("nodes_up", 0)
        pods = p.get("gke", {}).get("pods_running", 0)
        sql = p.get("cloud_sql", {}).get("instances_up", 0)
        run = p.get("cloud_run", {}).get("services_count", 0)
        mtd = p.get("billing", {}).get("mtd_usd", 0.0)
        lines.append(f'stackchan_gcp_instances_running{{project="{pid}"}} {vm_running}')
        lines.append(f'stackchan_gcp_instances_total{{project="{pid}"}} {vm_total}')
        lines.append(f'stackchan_gcp_vm_cpu_utilization_pct{{project="{pid}"}} {vm_cpu}')
        lines.append(f'stackchan_gcp_gke_nodes{{project="{pid}"}} {nodes}')
        lines.append(f'stackchan_gcp_gke_pods{{project="{pid}"}} {pods}')
        lines.append(f'stackchan_gcp_cloud_sql_instances{{project="{pid}"}} {sql}')
        lines.append(f'stackchan_gcp_cloud_run_services{{project="{pid}"}} {run}')
        lines.append(f'stackchan_gcp_billing_mtd_usd{{project="{pid}"}} {mtd}')
    return PlainTextResponse("\n".join(lines) + "\n")

if __name__ == "__main__":
    uvicorn.run("app:app", host=settings.host, port=settings.port, reload=False)
