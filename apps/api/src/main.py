"""FastAPI Application Entrypoint for ClearWayAI."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apps.api.src.config import settings
from apps.api.src.schemas import HealthResponse, SystemStatusResponse, ModuleStatus, utc_now

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="ClearWayAI Backend API: 3D Digital Twin, Multi-Intersection Pre-clearance, and Traffic Optimization System",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Root"])
def root():
    """Root endpoint welcoming API consumers."""
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health",
        "system_status": "/api/v1/system/status",
        "safety_mode": settings.SAFETY_MODE,
        "provenance": settings.DATA_PROVENANCE,
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
@app.get("/api/v1/health", response_model=HealthResponse, tags=["Health"])
def health_check():
    """Health check endpoint to verify backend service readiness."""
    return HealthResponse(
        status="healthy",
        service="clearway-api",
        version=settings.APP_VERSION,
        timestamp=utc_now(),
        environment=settings.ENVIRONMENT,
    )


@app.get("/api/v1/system/status", response_model=SystemStatusResponse, tags=["System"])
def get_system_status():
    """System status endpoint providing operational state and safety boundaries.

    Safety Guarantee:
    - Never reports LIVE public hardware connection unless authenticated and verified.
    - Explicitly labels data provenance as DEMO_FIXTURE or SUMO_SIMULATED.
    """
    return SystemStatusResponse(
        status="operational",
        mode=settings.SAFETY_MODE,  # type: ignore
        simulation_only=settings.SIMULATION_ONLY,
        public_signal_control_permitted=False,
        data_provenance=settings.DATA_PROVENANCE,  # type: ignore
        demo_mode_enabled=settings.DEMO_MODE,
        modules=ModuleStatus(
            simulation="PLANNED",
            ai_clearance="PLANNED",
            traffic_signals="PLANNED",
            digital_twin="PLANNED",
            v2x_telemetry="UNAVAILABLE",
            hardware_bridge="PLANNED",
        ),
        active_scenario="demo-oak-5th-intersection",
        timestamp=utc_now(),
        message="ClearWayAI System Initialized. All live telemetry and control disabled pending verification.",
    )
