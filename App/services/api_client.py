import httpx
from typing import Dict, Any, Optional
from fastapi import HTTPException

class NFLApiClient:
    """
    Client for interacting with the cached NFL API endpoints
    """
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
        
    async def get_teams(self) -> Dict[str, Any]:
        """Get all NFL teams through the cached API endpoint"""
        return await self._get("/nfl/teams")
    
    async def get_schedule(self, year: int, season_type: str = "REG") -> Dict[str, Any]:
        """Get NFL schedule through the cached API endpoint"""
        return await self._get(f"/nfl/schedule/{year}/{season_type}")
    
    async def get_team_profile(self, team_id: str) -> Dict[str, Any]:
        """Get team profile through the cached API endpoint"""
        return await self._get(f"/nfl/teams/{team_id}")
    
    async def get_player_profile(self, player_id: str) -> Dict[str, Any]:
        """Get player profile through the cached API endpoint"""
        return await self._get(f"/nfl/players/{player_id}")
    
    async def get_game_boxscore(self, game_id: str) -> Dict[str, Any]:
        """Get game boxscore through the cached API endpoint"""
        return await self._get(f"/nfl/games/{game_id}/boxscore")
    
    async def get_standings(self, year: int, season_type: str = "REG") -> Dict[str, Any]:
        """Get standings through the cached API endpoint"""
        return await self._get(f"/nfl/standings/{year}/{season_type}")
    
    async def get_weekly_injuries(self, year: int, season_type: str, week: int) -> Dict[str, Any]:
        """Get weekly injuries through the cached API endpoint"""
        return await self._get(f"/nfl/injuries/{year}/{season_type}/{week}")
    
    async def _get(self, endpoint: str) -> Dict[str, Any]:
        """
        Make a GET request to the API
        
        Args:
            endpoint: API endpoint path
            
        Returns:
            JSON response as dictionary
        """
        try:
            url = f"{self.base_url}{endpoint}"
            response = await self.client.get(url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            detail = f"API error {status_code}: {str(e)}"
            raise HTTPException(status_code=status_code, detail=detail)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error accessing API: {str(e)}")
            
    async def close(self):
        """Close the HTTP client connection"""
        await self.client.aclose()

# Create a singleton instance
nfl_api_client = NFLApiClient()
