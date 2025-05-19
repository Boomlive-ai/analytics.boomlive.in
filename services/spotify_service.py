import os
import requests
from fastapi import Request, HTTPException
from dotenv import load_dotenv

load_dotenv()

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI", "https://f0k0kw0go4g0ko4o0gggoscw.vps.boomlive.in/auth/callback/spotify")

def get_spotify_auth_url():
    """Generate Spotify OAuth authorization URL"""
    scope = "user-follow-read user-read-email user-top-read"
    return (
        f"https://accounts.spotify.com/authorize?client_id={SPOTIFY_CLIENT_ID}&response_type=code"
        f"&redirect_uri={SPOTIFY_REDIRECT_URI}&scope={scope}"
    )
import os
import requests
from fastapi import Request, HTTPException
from datetime import datetime, timedelta
from services.token_service import get_token_from_session, save_token_to_session

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

def refresh_spotify_token_if_needed(request: Request):
    """Check if Spotify token needs refresh and refresh it if necessary"""
    token_info = get_token_from_session(request, key="spotify_token_info")
    print("Existing Spotify Token Info:", token_info)  # Debugging

    # Ensure token has expiry info
    if not token_info or "expires_in" not in token_info:
        print("Missing expiry information!")
        raise HTTPException(status_code=401, detail="No valid Spotify token found")

    # Calculate expiry time dynamically
    current_time = datetime.utcnow().timestamp()
    expiry_time = float(token_info.get("expires_at", current_time + token_info["expires_in"]))

    if current_time + 300 >= expiry_time:  # Refresh if expiring in next 5 minutes
        print("Spotify Token is expired or expiring soon, refreshing...")

        refresh_token = token_info.get("refresh_token")
        if not refresh_token:
            print("Missing refresh token!")
            raise HTTPException(status_code=401, detail="No refresh token available")

        # Prepare refresh request
        token_url = "https://accounts.spotify.com/api/token"
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": SPOTIFY_CLIENT_ID,
            "client_secret": SPOTIFY_CLIENT_SECRET
        }

        response = requests.post(token_url, data=payload)
        if response.status_code != 200:
            print("Spotify OAuth refresh error:", response.json())  # Debugging
            raise HTTPException(status_code=401, detail=f"Failed to refresh Spotify token: {response.json()}")

        # Update token info
        new_token_info = response.json()
        token_info.update({
            "access_token": new_token_info["access_token"],
            "expires_at": current_time + new_token_info["expires_in"]  # Compute expiry time dynamically
        })

        # Save updated token info to session
        save_token_to_session(request, token_info, key="spotify_token_info")
        print("Spotify Token refreshed successfully:", token_info)

    else:
        print("Spotify Token is still valid!")

    return token_info




def exchange_spotify_token(request: Request, code: str):
    """Exchange authorization code for access token"""
    token_url = "https://accounts.spotify.com/api/token"
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": SPOTIFY_REDIRECT_URI,
        "client_id": SPOTIFY_CLIENT_ID,
        "client_secret": SPOTIFY_CLIENT_SECRET
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post(token_url, data=data, headers=headers)
    
    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed     to exchange token")
    
    token_info = response.json()
    request.session["spotify_token_info"] = token_info  # Save token in session
    return token_info

def get_user_artists(request: Request):
    """Fetch followed artists for authenticated user"""
    token_info = request.session.get("spotify_token_info")
    if not token_info:
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    access_token = token_info["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get("https://api.spotify.com/v1/me/following?type=artist", headers=headers)

    return response.json() if response.status_code == 200 else None
