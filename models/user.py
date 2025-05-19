from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class SpotifyProfile(BaseModel):
    """
    Spotify user profile information
    """
    id: str
    display_name: Optional[str] = None
    email: Optional[str] = None
    images: Optional[List[Dict[str, Any]]] = None
    country: Optional[str] = None
    product: Optional[str] = None
    followers: Optional[Dict[str, Any]] = None
    external_urls: Optional[Dict[str, str]] = None
    uri: Optional[str] = None
    type: Optional[str] = None

class TokenInfo(BaseModel):
    """
    Spotify token information
    """
    access_token: str
    token_type: str
    expires_in: int  # Seconds until expiration
    refresh_token: str
    scope: str
    expires_at: int  # Timestamp when token expires