import secrets
import uvicorn
from fastapi import FastAPI, Depends, HTTPException, Security, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
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

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(api_key: str = Security(api_key_header)):
    # If BRIDGE_API_KEY is unset, allow unauthenticated access (e.g. local LAN dev)
    if not settings.bridge_api_key:
        return True
    if not api_key or not secrets.compare_digest(api_key, settings.bridge_api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: Invalid or missing X-API-Key header"
        )
    return True

@app.get("/healthz")
async def health_check():
    return {"status": "healthy", "service": "stackchan-gcp-bridge"}

@app.get("/api/v1/gcp/status", dependencies=[Depends(verify_api_key)])
async def get_gcp_status(project: str | None = None):
    """
    Primary endpoint for StackChan ESP32-S3.
    Returns compact, high-efficiency JSON summary of GCP services (Fleet or specific project).
    """
    return collector.get_telemetry(project_id=project)

@app.get("/api/v1/gcp/projects", dependencies=[Depends(verify_api_key)])
async def get_gcp_projects():
    """
    Returns list of all monitored projects with basic health metrics.
    """
    return collector.get_projects_list()

@app.get("/api/v1/gcp/summary", dependencies=[Depends(verify_api_key)])
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
