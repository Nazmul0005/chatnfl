import httpx
from fastapi import HTTPException
from App.core.config import settings

class NFLService:
    def __init__(self):
        self.base_url = settings.BASE_URL
        self.api_key = settings.API_KEY
        
    async def get_data(self, endpoint: str):
        """
        Generic method to fetch data from the SportsRadar NFL API
        
        Args:
            endpoint (str): The API endpoint to call
            
        Returns:
            dict: The JSON response from the API
        """
        # Make sure endpoint doesn't start with a slash
        if endpoint.startswith('/'):
            endpoint = endpoint[1:]
            
        # Build the full URL with API key
        url = f"{self.base_url}/{endpoint}.json?api_key={self.api_key}"
        
        # Debug log
        print(f"Calling SportsRadar API: {url}")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url)
                response.raise_for_status()  # Raise an exception for HTTP errors
                return response.json()
        except httpx.TimeoutException:
            raise HTTPException(status_code=408, detail=f"Request to {url} timed out")
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            if status_code == 401:
                detail = "API key invalid or expired"
            elif status_code == 403:
                detail = "Access forbidden. Check API subscription"
            elif status_code == 404:
                detail = f"Resource not found: {endpoint}"
            elif status_code == 429:
                detail = "Rate limit exceeded"
            else:
                detail = f"HTTP error {status_code}: {str(e)}"
            raise HTTPException(status_code=status_code, detail=detail)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
            
    async def get_teams(self):
        """Get all NFL teams"""
        return await self.get_data("en/league/hierarchy")
    
    async def get_schedule(self, year: int, season_type: str = "REG"):
        """
        Get NFL schedule for a specific year and season type
        
        Args:
            year (int): The year to get the schedule for
            season_type (str): The season type (REG, PRE, PST)
            
        Returns:
            dict: Schedule data
        """
        return await self.get_data(f"en/games/{year}/{season_type}/schedule")
    
    async def get_team_profile(self, team_id: str):
        """
        Get detailed information about a specific team
        
        Args:
            team_id (str): The team ID
            
        Returns:
            dict: Team profile data
        """
        return await self.get_data(f"en/teams/{team_id}/profile")
    
    async def get_player_profile(self, player_id: str):
        """
        Get detailed information about a specific player
        
        Args:
            player_id (str): The player ID
            
        Returns:
            dict: Player profile data
        """
        return await self.get_data(f"en/players/{player_id}/profile")
    

    async def get_standings(self, year: str, season_type: str = "REG"):
        """
        Get standings for a specific season
        
        Args:
            year (str): The year for standings
            season_type (str): Season type (REG, PRE, PST)
            
        Returns:
            dict: Season standings data
        """
        return await self.get_data(f"en/seasons/{year}/{season_type}/standings/season")

    async def get_weekly_injuries(self, year: str, season_type: str, week: str):
        """
        Get injuries for a specific week
        
        Args:
            year (str): The year for injuries
            season_type (str): Season type (REG, PRE, PST)
            week (str): Week number
            
        Returns:
            dict: Weekly injuries data
        """
        return await self.get_data(f"en/seasons/{year}/{season_type}/{week}/injuries")
    
    
    async def get_game_boxscore(self, game_id: str):
        """
        Get boxscore data for a specific game
        
        Args:
            game_id (str): The game ID
            
        Returns:
            dict: Game boxscore data
        """
        return await self.get_data(f"en/games/{game_id}/boxscore")

nfl_service = NFLService()
