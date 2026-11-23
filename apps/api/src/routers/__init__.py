"""API Routers for ClearWayAI FastAPI Service."""

from apps.api.src.routers.audit import router as audit_router
from apps.api.src.routers.clearance import router as clearance_router
from apps.api.src.routers.corridor import router as corridor_router
from apps.api.src.routers.missions import router as missions_router
from apps.api.src.routers.replay import router as replay_router
from apps.api.src.routers.simulations import router as simulations_router

__all__ = [
    "audit_router",
    "clearance_router",
    "corridor_router",
    "missions_router",
    "replay_router",
    "simulations_router",
]

