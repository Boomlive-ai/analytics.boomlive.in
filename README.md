Spotify Analysis API
A FastAPI backend for Spotify authentication and music analysis. This API allows users to authenticate with Spotify OAuth, store tokens in the session, and analyze their Spotify data.
Features

Spotify OAuth authentication
Session-based token storage (no database required)
Comprehensive Spotify data analysis:

User's top tracks and artists
Recently played tracks
Saved tracks and playlists
Music taste analysis
Playlist analysis



Project Structure
/
├── app.py              # Main application entry point
├── routers/
│   ├── auth_router.py  # OAuth authentication routes
│   └── spotify_routers.py # Spotify data analysis routes
├── services/
│   ├── token_service.py # Token management
│   └── spotify_service.py # Spotify API interactions
├── models/
│   ├── user.py         # User-related schemas
│   └── spotify_models.py # Spotify data schemas
├── requirements.txt    # Project dependencies
└── .env               # Environment variables (not included in repo)
Setup

Clone the repository
Create a virtual environment and install dependencies:
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

Create a .env file in the root directory with your credentials:
FRONTEND_URL=http://localhost:3000
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
JWT_SECRET=your_random_secure_string

Run the application:
uvicorn app:app --reload


API Endpoints
Authentication

GET /auth/login/spotify - Get the Spotify authorization URL
GET /auth/callback/spotify - Handle the OAuth callback from Spotify
GET /auth/status - Check if the user is authenticated
GET /auth/logout - Log out and clear session

Spotify Data

GET /spotify/profile - Get user's profile information
GET /spotify/top-tracks - Get user's top tracks
GET /spotify/top-artists - Get user's top artists
GET /spotify/recently-played - Get user's recently played tracks
GET /spotify/saved-tracks - Get user's saved tracks
GET /spotify/playlists - Get user's playlists
GET /spotify/playlist/{playlist_id}/tracks - Get tracks from a specific playlist

Analysis

GET /spotify/analyze/taste - Analyze user's music taste
GET /spotify/analyze/playlist/{playlist_id} - Analyze a specific playlist

Authentication Flow

Client calls /auth/login/spotify to get the authorization URL
Client redirects the user to the authorization URL
After authorization, Spotify redirects back to /auth/callback/spotify
The API exchanges the code for tokens and stores them in the session
All subsequent requests to /spotify/* endpoints will use the stored token
If the token expires, it's automatically refreshed using the refresh token

Data Analysis
The API provides various endpoints for analyzing Spotify data:

Music taste analysis based on user's top tracks and artists
Playlist analysis including audio features, mood, and top artists
Detailed audio feature analysis including danceability, energy, valence, etc.

API Documentation
Access the interactive API documentation at /docs after starting the server.