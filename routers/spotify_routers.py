from fastapi import APIRouter, Request, HTTPException
from services.spotify_service import get_spotify_auth_url, exchange_spotify_token, get_user_artists, refresh_spotify_token_if_needed

router = APIRouter()

@router.get("/spotify/auth")
def spotify_auth():
    """Generate Spotify authentication URL"""
    return {"auth_url": get_spotify_auth_url()}

@router.get("/spotify/callback")
def spotify_callback(request: Request, code: str):
    """Exchange authorization code for access token"""
    token_info = exchange_spotify_token(request, code)
    return {"message": "Authentication successful", "token_info": token_info}

@router.get("/spotify/auth/status")
async def spotify_auth_status(request: Request):
    """Check authentication status for Spotify services"""
    try:
        token_info = refresh_spotify_token_if_needed(request)  # Refresh if needed
        return {
            "authenticated": True,
            "token_type": token_info.get("token_type"),
            "expires_at": token_info.get("expires_at"),
            "has_refresh_token": bool(token_info.get("refresh_token"))
        }
    except HTTPException:
        return {"authenticated": False}
    

@router.get("/spotify/artists")
def spotify_followed_artists(request: Request):
    """Fetch followed artists for authenticated user"""
    artists = get_user_artists(request)
    if not artists:
        raise HTTPException(status_code=400, detail="Failed to retrieve artists")
    return {"followed_artists": artists}
