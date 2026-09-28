import secrets
import uvicorn
from fastapi import FastAPI, Depends, HTTPException, Security, Header, status
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader, HTTPBasic, HTTPBasicCredentials
from collectors.gcp_collector import collector
from config import settings
from dashboard import get_dashboard_html

app = FastAPI(
    title="StackChan GCP Monitor Bridge",
    description="Bridge API aggregating GCP services (GKE, VMs, Cloud Run, Cloud SQL, BigQuery, Billing) for StackChan robot",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET"],
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

@app.get("/healthz")
async def health_check():
    return {"status": "healthy", "service": "stackchan-gcp-bridge"}

@app.get("/api/v1/gcp/status", dependencies=[Depends(verify_authentication)])
async def get_gcp_status(project: str | None = None):
    """
    Primary endpoint for StackChan ESP32-S3.
    Returns compact, high-efficiency JSON summary of GCP services (Fleet or specific project).
    """
    return collector.get_telemetry(project_id=project)

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

@app.get("/metrics")
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
