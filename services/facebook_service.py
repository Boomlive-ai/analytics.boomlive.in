import requests
import os
from fastapi import Request, HTTPException
from services.token_service import save_token_to_session, get_token_from_session
from dotenv import load_dotenv
load_dotenv()
FACEBOOK_CLIENT_ID = os.getenv("FACEBOOK_APP_ID")
FACEBOOK_CLIENT_SECRET = os.getenv("FACEBOOK_APP_SECRET")
REDIRECT_URI = "https://ba9a-58-146-101-17.ngrok-free.app/auth/callback/facebook"

print(REDIRECT_URI, FACEBOOK_CLIENT_ID, FACEBOOK_CLIENT_SECRET)
def get_facebook_auth_url():
    """Generate the Facebook OAuth authorization URL"""
    print(FACEBOOK_CLIENT_ID, FACEBOOK_CLIENT_SECRET)
    return f"https://www.facebook.com/v18.0/dialog/oauth?client_id={FACEBOOK_CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope=pages_read_engagement"

def exchange_facebook_token(request: Request, code: str):
    """Exchange the authorization code for an access token"""
    token_url = f"https://graph.facebook.com/v18.0/oauth/access_token"
    params = {
        "client_id": FACEBOOK_CLIENT_ID,
        "client_secret": FACEBOOK_CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "code": code
    }
    
    response = requests.get(token_url, params=params)
    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to retrieve access token")
    
    token_info = response.json()
    save_token_to_session(request, token_info)
    return token_info

def get_page_insights(request: Request, page_id: str):
    """Retrieve insights for a managed Facebook Page"""
    token_info = get_token_from_session(request)
    access_token = token_info.get("access_token")

    url = f"https://graph.facebook.com/v18.0/{page_id}/insights?metric=page_impressions,page_engaged_users,page_fan_adds&period=day&access_token={access_token}"
    response = requests.get(url)

    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to retrieve page insights")

    return response.json()
