import os
from pydantic_settings import BaseSettings

import base64

# Automatically materialize credentials if passed via GCP_SA_JSON env var
_gcp_sa_json = os.getenv("GCP_SA_JSON", "").strip()
_default_creds_path = "/app/credentials/gcp-sa.json"
if _gcp_sa_json and not os.path.exists(_default_creds_path):
    try:
        os.makedirs(os.path.dirname(_default_creds_path), exist_ok=True)
        content = _gcp_sa_json
        if not content.startswith("{"):
            try:
                content = base64.b64decode(content).decode("utf-8")
            except Exception:
                pass
        with open(_default_creds_path, "w") as _f:
            _f.write(content)
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = _default_creds_path
    except Exception:
        pass

if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
    local_creds = os.path.join(os.path.dirname(__file__), "credentials", "gcp-sa.json")
    if os.path.exists(_default_creds_path):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = _default_creds_path
    elif os.path.exists(local_creds):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = local_creds

class Settings(BaseSettings):
    host: str = "0.0.0.0"
    port: int = 8080
    
    # GCP Configuration
    gcp_project_id: str = os.getenv("GCP_PROJECT_ID", "insurverse-develop")
    gcp_project_ids_raw: str = os.getenv("GCP_PROJECT_IDS", "insurverse-develop,insurverse-uat")
    google_application_credentials: str = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
    gcp_billing_account_id: str = os.getenv("GCP_BILLING_ACCOUNT_ID", "")

    @property
    def project_ids(self) -> list[str]:
        if self.gcp_project_ids_raw.strip():
            return [p.strip() for p in self.gcp_project_ids_raw.split(",") if p.strip()]
        if self.gcp_project_id:
            return [self.gcp_project_id]
        return ["insurverse-develop", "insurverse-uat"]
    
    # Security: Optional API Key for Header Authentication (Pangolin / Public reverse proxy)
    bridge_api_key: str = os.getenv("BRIDGE_API_KEY", "").strip()
    
    # Security: Basic Authentication Credentials
    bridge_username: str = os.getenv("BRIDGE_USERNAME", "stackchan1").strip()
    bridge_password: str = os.getenv("BRIDGE_PASSWORD", "").strip()
    
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
