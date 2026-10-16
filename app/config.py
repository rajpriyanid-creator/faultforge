import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SERVICE_NAME: str = "faultforge-checkout"
    APP_HOST: str = "0.0.0.0"  # nosec B104
    APP_PORT: int = 8090
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "test")
    REVISION_ID: str = os.getenv("CI_COMMIT_SHA", os.getenv("K_REVISION", "local-dev"))

    # Downstream dependency configuration
    # In test/chaos, this points to Toxiproxy (e.g. http://localhost:8082 or http://toxiproxy:8082)
    # Under direct mode, points to mock shipping service (http://localhost:8081)
    SHIPPING_SERVICE_URL: str = os.getenv("SHIPPING_SERVICE_URL", "http://127.0.0.1:8082")

    # Resilience configuration (Hardening parameters)
    # Unpatched baseline uses excessive timeout (10.0s) and no fallback.
    # Hardened version enforces strict SLA budget (0.8s) + circuit breaker + graceful fallback.
    HTTP_TIMEOUT_SECONDS: float = float(os.getenv("HTTP_TIMEOUT_SECONDS", "0.8"))
    CIRCUIT_BREAKER_ENABLED: bool = os.getenv("CIRCUIT_BREAKER_ENABLED", "true").lower() in ("true", "1", "yes")
    CIRCUIT_BREAKER_FAIL_MAX: int = int(os.getenv("CIRCUIT_BREAKER_FAIL_MAX", "3"))
    CIRCUIT_BREAKER_RESET_TIMEOUT: float = float(os.getenv("CIRCUIT_BREAKER_RESET_TIMEOUT", "10.0"))
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "2"))
    FALLBACK_ENABLED: bool = os.getenv("FALLBACK_ENABLED", "true").lower() in ("true", "1", "yes")

    # SLA and chaos budget (Max permissible latency before considered a failure in ms)
    LATENCY_BUDGET_MS: float = float(os.getenv("LATENCY_BUDGET_MS", "1500.0"))

    model_config = {"env_file": ".env", "extra": "allow"}

settings = Settings()
