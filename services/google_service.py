import os
import requests
import json
from fastapi import Request, HTTPException
from datetime import datetime, timedelta
from google_auth_oauthlib.flow import Flow
from services.token_service import save_token_to_session, get_token_from_session
from dotenv import load_dotenv
load_dotenv()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI", "https://f0k0kw0go4g0ko4o0gggoscw.vps.boomlive.in/auth/callback/google")

def create_google_oauth_flow():
    """Create and configure Google OAuth flow"""
    client_config = {
        "web": {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [REDIRECT_URI]
        }
    }

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
        redirect_uri=REDIRECT_URI
    )
    return flow

def get_google_auth_url():
    """Generate Google OAuth authorization URL"""
    flow = create_google_oauth_flow()
    auth_url, _ = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'  # Force prompt to ensure refresh token
    )
    return auth_url

def exchange_google_token(request: Request, code: str):
    """Exchange authorization code for an access token"""
    try:
        flow = create_google_oauth_flow()
        # Exchange code for credentials
        flow.fetch_token(code=code)
        
        # Convert credentials to a dictionary and store in session
        credentials = flow.credentials
        token_info = {
            "access_token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_type": credentials.token_type,
            "expires_at": credentials.expiry.timestamp() if credentials.expiry else None
        }
        
        # Log successful token exchange
        print(f"Successfully exchanged code for token. Access token: {credentials.token[:10]}...")
        
        # Save to session
        save_token_to_session(request, token_info, key="google_token_info")
        
        return token_info
    except Exception as e:
        print(f"Error exchanging Google token: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Failed to exchange Google token: {str(e)}")
    

def refresh_google_token_if_needed(request: Request):
    """Check if token needs refresh and refresh it if necessary"""
    token_info = get_token_from_session(request, key="google_token_info")
    print("Existing Token Info:", token_info)  # Debugging

    # Ensure token has expiry info
    if not token_info or not token_info.get("expiry"):
        print("No expiry timestamp found in session!")
        raise HTTPException(status_code=401, detail="No valid Google token found")

    # Convert expiry timestamp and check expiration
    current_time = datetime.utcnow().timestamp()  # Use UTC for accuracy
    # Convert expiry timestamp correctly
    expiry_str = token_info.get("expiry")
    expiry_time = datetime.strptime(expiry_str, "%Y-%m-%dT%H:%M:%S.%fZ").timestamp()

    if current_time + 300 >= expiry_time:
        print("Token is expired or expiring soon, refreshing...")

        # Get refresh token
        refresh_token = token_info.get("refresh_token")
        if not refresh_token:
            print("Missing refresh token!")
            raise HTTPException(status_code=401, detail="No refresh token available")

        # Prepare refresh request
        token_url = "https://oauth2.googleapis.com/token"
        payload = {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token"
        }

        response = requests.post(token_url, data=payload)
        if response.status_code != 200:
            print("Google OAuth refresh error:", response.json())  # Debugging
            raise HTTPException(status_code=401, detail=f"Failed to refresh Google token: {response.json()}")

        # Update token info
        new_token_info = response.json()
        token_info.update({
            "access_token": new_token_info["access_token"],
            "expires_at": current_time + new_token_info["expires_in"]
        })

        # Save updated token info to session
        save_token_to_session(request, token_info, key="google_token_info")
        print("Token refreshed successfully:", token_info)

    else:
        print("Token is still valid!")

    return token_info

def get_partner_channels(request: Request):
    """Retrieve all YouTube Partner Channels where the user has access"""
    token_info = refresh_google_token_if_needed(request)
    access_token = token_info.get("token")

    url = "https://www.googleapis.com/youtube/partner/v1/contentOwners?fetchMine=true"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        raise HTTPException(status_code=400, detail=f"Failed to retrieve partner channels: {response.text}")

    return response.json()

def get_owner_channel(request: Request):
    """Retrieve the authenticated user's YouTube Channel ID"""
    token_info = refresh_google_token_if_needed(request)
    access_token = token_info.get("token")

    url = "https://www.googleapis.com/youtube/v3/channels?part=id,snippet&mine=true"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        raise HTTPException(status_code=400, detail=f"Failed to retrieve owner's channel: {response.text}")

    return response.json()

def get_combined_youtube_analytics(request: Request, content_owner_id: str, start_date: str, end_date: str):
    """Retrieve monetization, views, engagement, and audience demographics in a single response"""
    token_info = refresh_google_token_if_needed(request)
    access_token = token_info.get("token")
    headers = {"Authorization": f"Bearer {access_token}"}

    # API URLs for different data types
    urls = {
        "monetization": f"https://youtubeanalytics.googleapis.com/v2/reports?ids=contentOwner=={content_owner_id}&startDate={start_date}&endDate={end_date}&metrics=estimatedRevenue,estimatedAdRevenue,estimatedRedPartnerRevenue&dimensions=month&sort=-month",
        "audience_insights": f"https://youtubeanalytics.googleapis.com/v2/reports?ids=contentOwner=={content_owner_id}&startDate={start_date}&endDate={end_date}&metrics=views,estimatedMinutesWatched,averageViewDuration,subscribersGained,likes,comments&dimensions=day&sort=-day",
        "demographics": f"https://youtubeanalytics.googleapis.com/v2/reports?ids=contentOwner=={content_owner_id}&startDate={start_date}&endDate={end_date}&metrics=viewerPercentage&dimensions=ageGroup,gender"
    }

    # Make all API requests
    combined_data = {}
    for key, url in urls.items():
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            combined_data[key] = response.json()
        else:
            combined_data[key] = {"error": f"Failed to fetch {key} data: {response.text}"}

    return combined_data

def get_combined_youtube_analytics_auto(request: Request, start_date: str, end_date: str):
    """Automatically retrieve YouTube analytics without requiring content_owner_id"""
    token_info = refresh_google_token_if_needed(request)
    access_token = token_info.get("token")
    headers = {"Authorization": f"Bearer {access_token}"}

    # Fetch the authenticated user's content owner ID automatically
    url_owner = "https://www.googleapis.com/youtube/partner/v1/contentOwners?fetchMine=true"
    owner_response = requests.get(url_owner, headers=headers)

    if owner_response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to fetch YouTube content owner ID")

    content_owner_id = owner_response.json().get("items", [{}])[0].get("id", None)
    if not content_owner_id:
        raise HTTPException(status_code=404, detail="No YouTube content owner ID found")

    # Use fetched content_owner_id for analytics requests
    urls = {
        "monetization": f"https://youtubeanalytics.googleapis.com/v2/reports?ids=contentOwner=={content_owner_id}&startDate={start_date}&endDate={end_date}&metrics=estimatedRevenue,estimatedAdRevenue,estimatedRedPartnerRevenue&dimensions=month&sort=-month",
        "audience_insights": f"https://youtubeanalytics.googleapis.com/v2/reports?ids=contentOwner=={content_owner_id}&startDate={start_date}&endDate={end_date}&metrics=views,estimatedMinutesWatched,averageViewDuration,subscribersGained,likes,comments&dimensions=day&sort=-day",
        "demographics": f"https://youtubeanalytics.googleapis.com/v2/reports?ids=contentOwner=={content_owner_id}&startDate={start_date}&endDate={end_date}&metrics=viewerPercentage&dimensions=ageGroup,gender"
    }

    combined_data = {}
    for key, url in urls.items():
        response = requests.get(url, headers=headers)
        combined_data[key] = response.json() if response.status_code == 200 else {"error": f"Failed to fetch {key} data: {response.text}"}

    return combined_data


def get_ga4_property(request: Request):
    """Retrieve the authenticated user's GA4 Property ID using accountSummaries"""
    token_info = refresh_google_token_if_needed(request)
    access_token = token_info.get("token")

    url = "https://analyticsadmin.googleapis.com/v1beta/accountSummaries"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        raise HTTPException(status_code=400, detail=f"Failed to retrieve GA4 properties: {response.text}")

    account_summaries = response.json()
    
    if not account_summaries.get("accountSummaries"):
        raise HTTPException(status_code=404, detail="No GA4 properties found for the authenticated user.")

    # Extract property details
    ga4_properties = []
    for account in account_summaries["accountSummaries"]:
        for property_summary in account.get("propertySummaries", []):
            ga4_properties.append({
                "account_id": account["account"],
                "account_name": account["displayName"],
                "property_id": property_summary["property"],
                "property_name": property_summary["displayName"],
                "property_type": property_summary["propertyType"]
            })

    return {"success": True, "properties": ga4_properties}

def get_combined_ga4_analytics(request: Request, property_id: str, start_date: str, end_date: str, has_admin_access: bool):
    """Retrieve GA4 analytics with available metrics based on user permissions"""
    token_info = refresh_google_token_if_needed(request)
    access_token = token_info.get("token")

    # Define metrics based on user permissions
    viewer_metrics = [
        "activeUsers", "newUsers", "sessions", "engagedSessions", "screenPageViews", "bounceRate",
        "engagementRate", "averageSessionDuration", "eventCount"
    ]
    
    admin_metrics = [
        "totalRevenue", "retentionRate", "newVsReturningUsers", "sessionConversionRate",
        "audienceCategoryAffinity", "sessionQuality"
    ]

    # Select metrics based on access level
    metrics = viewer_metrics if not has_admin_access else viewer_metrics + admin_metrics

    # Define dimensions based on user permissions
    viewer_dimensions = ["date", "deviceCategory", "country", "city", "browser"]
    
    admin_dimensions = ["sessionDefaultChannelGroup", "landingPage", "previousPagePath", "exitPage",
                        "userEngagementDuration", "interests", "videoTitle", "contentType"]

    dimensions = viewer_dimensions if not has_admin_access else viewer_dimensions + admin_dimensions

    # Prepare API request body
    request_body = {
        "dateRanges": [{"startDate": start_date, "endDate": end_date}],
        "metrics": [{"name": metric} for metric in metrics],
        "dimensions": [{"name": dim} for dim in dimensions]
    }

    url = f"https://analyticsdata.googleapis.com/v1beta/properties/{property_id}:runReport"
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

    response = requests.post(url, headers=headers, json=request_body)
    print(request_body, "request_body")
    if response.status_code != 200:
        raise HTTPException(status_code=400, detail=f"GA4 Analytics request failed: {response.text}")

    return response.json()

def get_combined_ga4_analytics_auto(request: Request, start_date: str, end_date: str, has_admin_access: bool):
    """Automatically retrieve GA4 analytics without requiring property_id"""
    token_info = refresh_google_token_if_needed(request)
    access_token = token_info.get("token")

    # Fetch the authenticated user's GA4 property ID automatically
    url_property = "https://analyticsadmin.googleapis.com/v1beta/accountSummaries"
    headers = {"Authorization": f"Bearer {access_token}"}

    property_response = requests.get(url_property, headers=headers)

    if property_response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to fetch GA4 property ID")

    account_summaries = property_response.json()
    property_id = account_summaries.get("accountSummaries", [{}])[0].get("propertySummaries", [{}])[0].get("property", None).split("/")[-1]

    if not property_id:
        raise HTTPException(status_code=404, detail="No GA4 property ID found")

    # Define metrics based on user permissions
    viewer_metrics = ["activeUsers", "newUsers", "sessions", "engagedSessions", "screenPageViews", "bounceRate", "engagementRate", "averageSessionDuration", "eventCount"]
    admin_metrics = ["totalRevenue", "retentionRate", "newVsReturningUsers", "sessionConversionRate", "audienceCategoryAffinity", "sessionQuality"]
    metrics = viewer_metrics if not has_admin_access else viewer_metrics + admin_metrics

    viewer_dimensions = ["date", "deviceCategory", "country", "city", "browser"]
    admin_dimensions = ["sessionDefaultChannelGroup", "landingPage", "previousPagePath", "exitPage", "userEngagementDuration", "interests", "videoTitle", "contentType"]
    dimensions = viewer_dimensions if not has_admin_access else viewer_dimensions + admin_dimensions

    request_body = {
        "dateRanges": [{"startDate": start_date, "endDate": end_date}],
        "metrics": [{"name": metric} for metric in metrics],
        "dimensions": [{"name": dim} for dim in dimensions]
    }

    url = f"https://analyticsdata.googleapis.com/v1beta/properties/{property_id}:runReport"
    response = requests.post(url, headers=headers, json=request_body)

    if response.status_code != 200:
        raise HTTPException(status_code=400, detail=f"GA4 Analytics request failed: {response.text}")

    return response.json()
