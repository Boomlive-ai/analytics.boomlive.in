# Export routers from the routers package
from .auth_router import router as auth_router
from .spotify_routers import router as spotify_router
from .google_router import router as google_router
from .facebook_router import router as facebook_router
__all__ = [
    "auth_router",
    "spotify_router",
    "google_router",
    "facebook_router",
]
