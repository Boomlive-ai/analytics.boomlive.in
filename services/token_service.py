
from fastapi import Request, HTTPException
import os
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
import json

# Session keys
GOOGLE_TOKEN_KEY = "google_token_info"

def create_google_oauth():
    """Create and configure Google OAuth flow"""
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    redirect_uri = os.getenv("REDIRECT_URI", "https://f0k0kw0go4g0ko4o0gggoscw.vps.boomlive.in/auth/callback/google")
    
    # Using client_secrets dict instead of file
    client_config = {
        "web": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [redirect_uri]
        }
    }
    
    # Create flow instance
    flow = Flow.from_client_config(
        client_config,
        scopes=[
            "https://www.googleapis.com/auth/analytics.readonly",
            "https://www.googleapis.com/auth/analytics",
            "https://www.googleapis.com/auth/analytics.edit",
            "https://www.googleapis.com/auth/analytics.manage.users",  # Manage users (if needed)
            "https://www.googleapis.com/auth/analytics.manage.users.readonly",  # Read user access levels
            "https://www.googleapis.com/auth/analytics.provision",  # Admin access to GA accounts
            "https://www.googleapis.com/auth/youtube",
            "https://www.googleapis.com/auth/yt-analytics-monetary.readonly",
            "https://www.googleapis.com/auth/youtube.readonly",
            "https://www.googleapis.com/auth/yt-analytics.readonly",
            "https://www.googleapis.com/auth/youtube.force-ssl",
            "https://www.googleapis.com/auth/youtubepartner",
            "https://www.googleapis.com/auth/youtube.channel-memberships.creator"
        ],
        redirect_uri=redirect_uri
    )
    return flow

def save_token_to_session(request: Request, token_info, key=GOOGLE_TOKEN_KEY):
    """Save token information to session"""
    # Convert to dictionary if it's a string
    if isinstance(token_info, str):
        token_info = json.loads(token_info)
    
    # If it's a Credentials object, convert to dict
    if isinstance(token_info, Credentials):
        token_info = {
            "access_token": token_info.token,
            "refresh_token": token_info.refresh_token,
            "token_type": token_info.token_type,
            "expires_at": token_info.expiry.timestamp() if token_info.expiry else None
        }
    
    # Store in session
    request.session[key] = token_info
    print(f"Token saved to session with key: {key}")

def get_token_from_session(request: Request, key=GOOGLE_TOKEN_KEY):
    """Get token information from session"""
    token_info = request.session.get(key)
    if not token_info:
        raise HTTPException(status_code=401, detail=f"No {key.replace('_', ' ')} found. Please authenticate first.")
    return token_info

def is_authenticated(request: Request, key=GOOGLE_TOKEN_KEY):
    """Check if user is authenticated"""
    try:
        get_token_from_session(request, key)
        return True
    except HTTPException:
        return False