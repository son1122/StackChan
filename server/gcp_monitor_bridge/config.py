import os
from pydantic_settings import BaseSettings

# Automatically materialize credentials if passed via GCP_SA_JSON env var
_gcp_sa_json = os.getenv("GCP_SA_JSON", "").strip()
_default_creds_path = "/app/credentials/gcp-sa.json"
if _gcp_sa_json and not os.path.exists(_default_creds_path):
    try:
        os.makedirs(os.path.dirname(_default_creds_path), exist_ok=True)
        with open(_default_creds_path, "w") as _f:
            _f.write(_gcp_sa_json)
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = _default_creds_path
    except Exception:
        pass

class Settings(BaseSettings):
    host: str = "0.0.0.0"
    port: int = 8080
    
    # GCP Configuration
    gcp_project_id: str = os.getenv("GCP_PROJECT_ID", "demo-gcp-project")
    google_application_credentials: str = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
    gcp_billing_account_id: str = os.getenv("GCP_BILLING_ACCOUNT_ID", "")
    
    # Security: Optional API Key for Header Authentication (Pangolin / Public reverse proxy)
    bridge_api_key: str = os.getenv("BRIDGE_API_KEY", "").strip()
    
    # Optional Prometheus / OpenTelemetry Gateway
    prometheus_url: str = os.getenv("PROMETHEUS_URL", "")
    
    # Poll cache duration in seconds
    cache_ttl_seconds: int = 15
    
    # Demo / Simulation mode if GCP credentials are not found
    enable_mock_fallback: bool = True

    # Security: Allowed CORS origins
    allowed_origins: list[str] = ["http://localhost", "http://localhost:3000", "http://127.0.0.1", "http://127.0.0.1:8080"]

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
