from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class AudioFeatures(BaseModel):
    """
    Model for Spotify audio features
    """
    danceability: float
    energy: float
    valence: float
    tempo: float
    acousticness: float
    instrumentalness: float

class MusicTasteAnalysis(BaseModel):
    """
    Model for music taste analysis
    """
    avg_audio_features: AudioFeatures
    top_genres: List[tuple]
    mood: str
    most_played_artist: Optional[str] = None
    most_played_track: Optional[str] = None

class PlaylistAnalysis(BaseModel):
    """
    Model for playlist analysis
    """
    playlist_name: str
    total_tracks: int
    total_duration_min: float
    avg_audio_features: AudioFeatures
    top_artists: List[tuple]
    mood: str