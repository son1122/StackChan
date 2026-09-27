import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    host: str = "0.0.0.0"
    port: int = 8080
    
    # GCP Configuration
    gcp_project_id: str = os.getenv("GCP_PROJECT_ID", "demo-gcp-project")
    google_application_credentials: str = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
    gcp_billing_account_id: str = os.getenv("GCP_BILLING_ACCOUNT_ID", "")
    
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
