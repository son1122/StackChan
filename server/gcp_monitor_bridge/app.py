import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from collectors.gcp_collector import collector
from config import settings

app = FastAPI(
    title="StackChan GCP Monitor Bridge",
    description="Bridge API aggregating GCP services (GKE, VMs, Cloud Run, Cloud SQL, BigQuery, Billing) for StackChan robot",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/healthz")
async def health_check():
    return {"status": "healthy", "service": "stackchan-gcp-bridge"}

@app.get("/api/v1/gcp/status")
async def get_gcp_status():
    """
    Primary endpoint for StackChan ESP32-S3.
    Returns compact, high-efficiency JSON summary of all GCP services.
    """
    return collector.get_telemetry()

@app.get("/api/v1/gcp/summary")
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
    
    return {
        "status": status_str,
        "ticker": f"[{status_str}] GKE: {gke_pods} Pods | VM: {vm_count} Up | Cost: ${mtd:.2f} | Alerts: {alerts}",
        "incident_count": alerts
    }

if __name__ == "__main__":
    uvicorn.run("app:app", host=settings.host, port=settings.port, reload=False)
