import secrets
import uvicorn
from fastapi import FastAPI, Depends, HTTPException, Security, Header, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader, HTTPBasic, HTTPBasicCredentials
from collectors.gcp_collector import collector
from config import settings

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

if __name__ == "__main__":
    uvicorn.run("app:app", host=settings.host, port=settings.port, reload=False)
