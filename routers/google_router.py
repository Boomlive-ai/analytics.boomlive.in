from fastapi import APIRouter, Request, HTTPException, Query, Depends
from datetime import datetime, timedelta
from services.token_service import is_authenticated
from services.google_service import (
    get_google_auth_url,
    exchange_google_token,
    get_ga4_property,
    get_combined_ga4_analytics,
    get_combined_ga4_analytics_auto,
    get_combined_youtube_analytics_auto,
    get_partner_channels,
    get_owner_channel,
    get_combined_youtube_analytics,
    refresh_google_token_if_needed
)

router = APIRouter()

@router.get("/auth/login/google")
async def login_google():
    """Initiates Google OAuth flow and returns the authorization URL"""
    auth_url = get_google_auth_url()
    return {"auth_url": auth_url}

@router.get("/auth/callback/google")
async def google_callback(request: Request, code: str = None, error: str = None):
    """Handles Google OAuth callback"""
    if error:
        raise HTTPException(status_code=400, detail=f"Google OAuth error: {error}")
    
    if not code:
        raise HTTPException(status_code=400, detail="No authorization code provided for Google")

    try:
        token_info = exchange_google_token(request, code)
        # Return success response with token information (access token hidden for security)
        return {
            "message": "Google Authentication successful", 
            "authenticated": True,
            "token_type": token_info.get("token_type"),
            "expires_at": token_info.get("expires_at")
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to authenticate with Google: {str(e)}")

@router.get("/auth/status")
async def auth_status(request: Request):
    """Check authentication status for Google services"""
    try:
        # This will attempt to refresh token if needed
        token_info = refresh_google_token_if_needed(request)
        print(token_info, "token_info")
        return {
            "authenticated": True,
            "token_type": token_info.get("token_type"),
            "expires_at": token_info.get("expires_at"),
            "has_refresh_token": bool(token_info.get("refresh_token"))
        }
    except HTTPException:
        return {"authenticated": False}



### 📌 FETCH PARTNER CHANNELS ###
@router.get("/google/youtube/partner-channels")
async def fetch_partner_channels(request: Request, _: bool = Depends(is_authenticated)):
    """Retrieve YouTube partner channels where user has access"""
    try:
        return get_partner_channels(request)
    except Exception as e:
        return {"success": False, "error": str(e)}
    
### FETCH OWNED YOUTUBE CHANNEL ###    
@router.get("/google/youtube/owner-channel")
async def fetch_owner_channel(request: Request, _: bool = Depends(is_authenticated)):
    """Retrieve the authenticated user's YouTube channel details"""
    try:
        return get_owner_channel(request)
    except Exception as e:
        return {"success": False, "error": str(e)}

### 📊 FETCH COMBINED YOUTUBE ANALYTICS ###
@router.get("/google/youtube/analytics")
async def fetch_combined_analytics(
    request: Request,
    content_owner_id: str = Query(..., description="Content Owner ID"),
    start_date: str = Query("2024-01-01", description="Start date in YYYY-MM-DD format"),
    end_date: str = Query("2024-04-01", description="End date in YYYY-MM-DD format")
):
    """Retrieve combined monetization, views, engagement, and audience insights"""
    try:
        return get_combined_youtube_analytics(request, content_owner_id, start_date, end_date)
    except Exception as e:
        return {"success": False, "error": str(e)}
    

### 📊 FETCH COMBINED YOUTUBE ANALYTICS (AUTO) ###
@router.get("/google/youtube/analytics/auto")
async def fetch_combined_youtube_analytics_auto(
    request: Request,
    start_date: str = Query("2024-01-01", description="Start date in YYYY-MM-DD format"),
    end_date: str = Query("2024-04-01", description="End date in YYYY-MM-DD format")
):
    """Automatically retrieve YouTube analytics without requiring Content Owner ID"""
    try:
        return get_combined_youtube_analytics_auto(request, start_date, end_date)
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.get("/google/ga4/property")
async def fetch_ga4_property(request: Request, _: bool = Depends(is_authenticated)):
    """Retrieve the authenticated user's GA4 Property ID"""
    try:
        return get_ga4_property(request)
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.get("/google/ga4/analytics")
async def fetch_combined_ga4_analytics(
    request: Request,
    property_id: str = Query(..., description="GA4 Property ID"),
    start_date: str = Query("2024-01-01", description="Start date in YYYY-MM-DD format"),
    end_date: str = Query("2024-04-01", description="End date in YYYY-MM-DD format"),
    has_admin_access: bool = Query(False, description="Indicates whether the user has Admin access")
):
    """Retrieve GA4 analytics with available metrics based on user permissions"""
    try:
        return get_combined_ga4_analytics(request, property_id, start_date, end_date, has_admin_access)
    except Exception as e:
        return {"success": False, "error": str(e)}


### 📊 FETCH COMBINED GA4 ANALYTICS (AUTO) ###
@router.get("/google/ga4/analytics/auto")
async def fetch_combined_ga4_analytics_auto(
    request: Request,
    start_date: str = Query("2024-01-01", description="Start date in YYYY-MM-DD format"),
    end_date: str = Query("2024-04-01", description="End date in YYYY-MM-DD format"),
    has_admin_access: bool = Query(False, description="Indicates whether the user has Admin access")
):
    """Automatically retrieve GA4 analytics without requiring Property ID"""
    try:
        return get_combined_ga4_analytics_auto(request, start_date, end_date, has_admin_access)
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.get("/auth/logout")
async def logout(request: Request):
    """
    Logs out from Google services by clearing session tokens
    """
    request.session.pop("google_token_info", None)
    return {"message": "Logged out successfully from Google services"}