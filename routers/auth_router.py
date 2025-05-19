from fastapi import APIRouter, Request, HTTPException, status
from fastapi.responses import RedirectResponse, JSONResponse
import os
from services.token_service import create_google_oauth, save_token_to_session, is_authenticated
# from services.facebook_service import get_facebook_auth_url, exchange_facebook_token
from services.google_service import get_google_auth_url, exchange_google_token
from services.spotify_service import exchange_spotify_token  # Import Spotify token exchange logic
router = APIRouter()

@router.get("/login")
async def login_sequence():
    """
    Begins OAuth flow for Spotify, Facebook, and Google, returning authorization URLs
    """
    # spotify_url = spotify_oauth.get_authorize_url()
    # facebook_url = get_facebook_auth_url()
    google_url = get_google_auth_url()
    
    return {
        # "spotify_auth_url": spotify_url,
        # "facebook_auth_url": facebook_url,
        "google_auth_url": google_url
    }

@router.get("/callback/spotify")
async def spotify_callback(request: Request, code: str = None, error: str = None):
    """
    Handles Spotify OAuth callback and stores tokens in session.
    """
    if error:
        raise HTTPException(status_code=400, detail=f"Spotify OAuth error: {error}")
    
    if not code:
        raise HTTPException(status_code=400, detail="No authorization code provided for Spotify")

    try:
        token_info = exchange_spotify_token(request, code)  # Use dedicated service function
        save_token_to_session(request, token_info, key="spotify_token_info")
        return {"message": "Spotify Authentication successful", "authenticated": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to get Spotify token: {str(e)}")

# @router.get("/callback/facebook")
# async def facebook_callback(request: Request, code: str = None, error: str = None):
#     """
#     Handles Facebook OAuth callback and stores tokens in session
#     """
#     if error:
#         raise HTTPException(status_code=400, detail=f"Facebook OAuth error: {error}")
    
#     if not code:
#         raise HTTPException(status_code=400, detail="No authorization code provided for Facebook")

#     token_info = exchange_facebook_token(request, code)
#     return {"message": "Facebook Authentication successful", "authenticated": True}

@router.get("/callback/google")
async def google_callback(request: Request, code: str = None, error: str = None):
    """Handles Google OAuth callback and stores tokens in session"""
    if error:
        raise HTTPException(status_code=400, detail=f"Google OAuth error: {error}")
    
    if not code:
        raise HTTPException(status_code=400, detail="No authorization code provided for Google")

    flow = create_google_oauth()
    flow.fetch_token(code=code)

    token_info = flow.credentials.to_json()
    save_token_to_session(request, token_info)

    return {"message": "Google Authentication successful", "authenticated": True}

@router.get("/status")
async def auth_status(request: Request):
    """
    Check authentication status for Spotify, Facebook & Google
    """
    spotify_authenticated = is_authenticated(request)
    facebook_authenticated = "token_info" in request.session  # Checking session for Facebook tokens
    google_authenticated = "google_token_info" in request.session  # Checking session for Google tokens

    return {
        "spotify_authenticated": spotify_authenticated,
        "facebook_authenticated": facebook_authenticated,
        "google_authenticated": google_authenticated
    }

@router.get("/logout")
async def logout(request: Request):
    """
    Logs out from Spotify, Facebook & Google by clearing session tokens
    """
    request.session.pop("token_info", None)  # Spotify
    request.session.pop("facebook_token_info", None)  # Facebook
    request.session.pop("google_token_info", None)  # Google
    return {"message": "Logged out successfully from all services"}
