import os
import time
import secrets
import logging
import threading
from typing import Dict, Any, List, Optional
import uvicorn
from pydantic import BaseModel, Field
from fastapi import FastAPI, Depends, HTTPException, Security, Header, Request, status
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader, HTTPBasic, HTTPBasicCredentials
from collectors.gcp_collector import collector
from config import settings
from dashboard import get_dashboard_html
from robot_store import robot_store

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
    request: Request,
    credentials: HTTPBasicCredentials | None = Depends(security_basic),
    api_key: str | None = Security(api_key_header),
    x_auth_user: str | None = Header(None, alias="X-Auth-User"),
    x_auth_pass: str | None = Header(None, alias="X-Auth-Password"),
    x_robot_mac: str | None = Header(None, alias="X-Robot-MAC"),
):
    """
    Validates either:
    1. UI / Dashboard bypass (when skip_auth_for_ui is enabled)
    2. Physical Robot identity (X-Robot-MAC)
    3. HTTP Basic Auth (Authorization: Basic base64(user:pass))
    4. Custom Headers (X-Auth-User & X-Auth-Password)
    5. API Key Header (X-API-Key)
    """
    # 0. Skip authentication for Web UI / Browser requests if configured
    if settings.skip_auth_for_ui:
        referer = request.headers.get("referer", "")
        sec_fetch_site = request.headers.get("sec-fetch-site", "")
        x_requested_with = request.headers.get("x-requested-with", "")
        accept_header = request.headers.get("accept", "")
        
        is_ui_request = (
            x_requested_with == "StackChan-UI"
            or "/dashboard" in referer
            or referer.rstrip("/").endswith("stackchan.achtix.com")
            or referer.endswith("/")
            or sec_fetch_site in ("same-origin", "none")
            or "text/html" in accept_header
        )
        if is_ui_request:
            return True

    # Allow connecting physical StackChan robots via MAC identity
    if x_robot_mac:
        return True

    # Anonymous access mode fallback
    if os.getenv("ALLOW_ANONYMOUS", "").lower() in ("true", "1", "yes"):
        return True

    has_api_key_configured = bool(settings.bridge_api_key)
    has_basic_configured = bool(settings.bridge_username and settings.bridge_password)
    
    # If security credentials are not configured, allow anonymous
    if not has_api_key_configured and not has_basic_configured:
        return True

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

class RobotConfigPayload(BaseModel):
    name: Optional[str] = Field(None, max_length=50)
    assigned_project: Optional[str] = None
    sound_alerts: Optional[bool] = None
    show_billing: Optional[bool] = None
    poll_interval_sec: Optional[int] = Field(None, ge=5, le=300)
    display_mode: Optional[str] = Field(None, pattern="^(standard|ticker|avatar_only)$")

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
    Also handles multi-robot configuration routing and telemetry masking.
    """
    client_ip = request.client.host if request.client else "unknown"
    robot_cfg = None

    if x_robot_mac:
        robot_store.record_heartbeat(
            mac=x_robot_mac,
            ip=client_ip,
            requested_project=x_robot_project or project,
            battery=x_robot_battery,
            charging=x_robot_charging,
            version=x_robot_version
        )
        effective_project, robot_cfg = robot_store.get_effective_project(x_robot_mac, explicit_project=project)
        telemetry = collector.get_telemetry(project_id=effective_project)
    else:
        telemetry = collector.get_telemetry(project_id=project)

    # Security / Privacy: If robot config specifies hiding billing on physical screen, mask it
    if robot_cfg and not robot_cfg.get("show_billing", True):
        telemetry = dict(telemetry)
        telemetry["billing"] = {
            "mtd_usd": 0.0,
            "today_usd": 0.0,
            "budget_pct": 0.0,
            "hidden": True
        }

    # Inject robot configuration block if called by a robot (without exposing any credentials)
    if robot_cfg:
        telemetry = dict(telemetry)
        telemetry["robot_config"] = {
            "mac": robot_cfg.get("mac"),
            "name": robot_cfg.get("name"),
            "assigned_project": robot_cfg.get("assigned_project", "ALL FLEET"),
            "sound_alerts": robot_cfg.get("sound_alerts", True),
            "show_billing": robot_cfg.get("show_billing", True),
            "poll_interval_sec": robot_cfg.get("poll_interval_sec", 15),
            "display_mode": robot_cfg.get("display_mode", "standard"),
        }

    return telemetry

@app.get("/api/v1/gcp/robots", dependencies=[Depends(verify_authentication)])
async def get_connected_robots():
    """
    Returns list of connected and configured physical StackChan robots with battery, IP,
    assigned project, and feature configurations. Never exposes credentials.
    """
    return {
        "projects": ["ALL FLEET"] + settings.project_ids,
        "robots": robot_store.get_all_robots()
    }

@app.post("/api/v1/gcp/robots/{mac}/config", dependencies=[Depends(verify_authentication)])
async def update_robot_config(mac: str, payload: RobotConfigPayload):
    """
    Updates the per-robot configuration (friendly name, assigned project, alerts, billing).
    Persists configuration in real-time.
    """
    updates = {k: v for k, v in payload.dict().items() if v is not None}
    if "assigned_project" in updates:
        valid_projects = ["ALL FLEET"] + settings.project_ids
        if updates["assigned_project"] not in valid_projects:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid project '{updates['assigned_project']}'. Must be one of: {valid_projects}"
            )
    updated = robot_store.update_config(mac, updates)
    return {"status": "success", "robot": updated}

@app.delete("/api/v1/gcp/robots/{mac}", dependencies=[Depends(verify_authentication)])
async def delete_robot(mac: str):
    """
    Deletes a robot from the registry.
    """
    removed = robot_store.delete_robot(mac)
    return {"status": "success", "deleted": removed, "mac": mac}

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
async def get_gcp_summary(
    x_robot_mac: Optional[str] = Header(None, alias="X-Robot-MAC"),
):
    """
    Shorter 1-line summary for ambient screensaver and text tickers.
    Automatically customized to the querying StackChan's assigned project.
    """
    effective_project = None
    robot_cfg = None
    if x_robot_mac:
        effective_project, robot_cfg = robot_store.get_effective_project(x_robot_mac)

    data = collector.get_telemetry(project_id=effective_project)
    status_str = data.get("status", "ok").upper()
    gke_pods = data.get("gke", {}).get("pods_running", 0)
    vm_count = data.get("vm", {}).get("instances_running", 0)
    mtd = data.get("billing", {}).get("mtd_usd", 0.0)
    alerts = data.get("incident_count", 0)
    total_projects = data.get("total_projects", 1)
    target_name = effective_project or f"Fleet ({total_projects} Projects)"
    
    # Hide billing if configured
    if robot_cfg and not robot_cfg.get("show_billing", True):
        ticker_msg = f"[{status_str}] {target_name}: {gke_pods} Pods | {vm_count} VMs | Alerts: {alerts}"
    else:
        ticker_msg = f"[{status_str}] {target_name}: {gke_pods} Pods | {vm_count} VMs | ${mtd:.2f} MTD | Alerts: {alerts}"

    return {
        "status": status_str,
        "ticker": ticker_msg,
        "incident_count": alerts,
        "project": effective_project or "ALL FLEET",
        "total_projects": total_projects
    }


@app.get("/", response_class=HTMLResponse)
@app.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard():
    """
    Renders interactive web dashboard with animated StackChan avatar and real-time metrics.
    Publicly accessible UI without authentication prompt.
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
