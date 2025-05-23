from fastapi import APIRouter, HTTPException, Path, Depends
from typing import Optional
from datetime import datetime, timedelta
import functools

from App.services.nfl_service import nfl_service
from App.models.schemas import ErrorResponse
from App.services.Nfl_query_service import nfl_query_service
from App.models.schemas import NFLQuery, NFLQueryResponse, ErrorResponse

# Simple in-memory cache for API responses
cache = {}
CACHE_EXPIRY = timedelta(minutes=15)  # Cache expiry time

def with_cache(expiry: Optional[timedelta] = None):
    """
    Decorator to cache API responses
    
    Args:
        expiry: Optional time delta for cache expiry (default: 15 minutes)
    """
    if expiry is None:
        expiry = CACHE_EXPIRY
        
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Create a cache key from function name and arguments
            key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Check if we have a cached response and it's still valid
            if key in cache:
                timestamp, value = cache[key]
                if datetime.now() - timestamp < expiry:
                    return value
            
            # Call the original function if no cache hit
            result = await func(*args, **kwargs)
            
            # Cache the result
            cache[key] = (datetime.now(), result)
            return result
        return wrapper
    return decorator

router = APIRouter(prefix="/nfl", tags=["NFL Data"])

@router.get("/teams", response_model=dict, summary="Get NFL Teams Hierarchy")
@with_cache(timedelta(hours=24))  # Teams don't change often, cache for 24 hours
async def get_teams():
    """
    Retrieve all NFL teams organized by conference and division.
    """
    return await nfl_service.get_teams()

@router.get("/schedule/{year}/{season_type}", response_model=dict, summary="Get NFL Schedule")
@with_cache(timedelta(hours=12))  # Schedule might update, cache for 12 hours
async def get_schedule(
    year: int = Path(..., description="The year to get the schedule for (e.g., 2023)"),
    season_type: str = Path(..., description="Season type (REG, PRE, PST)")
):
    """
    Retrieve the NFL schedule for a specific year and season type.
    
    - year: The year to get the schedule for (e.g., 2023)
    - season_type: Season type (REG = Regular Season, PRE = Preseason, PST = Postseason)
    """
    return await nfl_service.get_schedule(year, season_type)

@router.get("/teams/{team_id}", response_model=dict, summary="Get Team Profile")
@with_cache(timedelta(hours=24))  # Team profiles don't change often
async def get_team_profile(
    team_id: str = Path(..., description="The team ID to get the profile for")
):
    """
    Retrieve detailed information about a specific NFL team.
    
    - team_id: The unique identifier for the team
    """
    return await nfl_service.get_team_profile(team_id)

@router.get("/players/{player_id}", response_model=dict, summary="Get Player Profile")
@with_cache(timedelta(hours=24))  # Player profiles don't change often
async def get_player_profile(
    player_id: str = Path(..., description="The player ID to get the profile for")
):
    """
    Retrieve detailed information about a specific NFL player.
    
    - player_id: The unique identifier for the player
    """
    return await nfl_service.get_player_profile(player_id)

@router.get("/games/{game_id}/boxscore", response_model=dict, summary="Get Game Boxscore")
@with_cache(timedelta(hours=1))  # Game data updates frequently
async def get_game_boxscore(
    game_id: str = Path(..., description="The game ID to get the boxscore for")
):
    """
    Retrieve detailed boxscore data for a specific NFL game.
    
    - game_id: The unique identifier for the game
    """
    return await nfl_service.get_game_boxscore(game_id)

@router.delete("/cache", summary="Clear API Cache")
async def clear_cache():
    """
    Clear all cached API responses.
    """
    cache.clear()
    return {"message": "Cache cleared successfully"}


@router.get("/standings/{year}/{season_type}", response_model=dict, summary="Get season standings")
@with_cache(timedelta(hours=1))
async def get_standings(
    year: str = Path(..., description="Year for standings"),
    season_type: str = Path(..., description="Season type (REG, PRE, PST)")
):
    """
    Get standings for a specific season.
    
    - **year**: Year for standings
    - **season_type**: Season type (REG = Regular Season, PRE = Preseason, PST = Postseason)
    """
    return await nfl_service.get_standings(year, season_type)

@router.get("/injuries/{year}/{season_type}/{week}", response_model=dict, summary="Get weekly injuries")
@with_cache(timedelta(hours=1))
async def get_weekly_injuries(
    year: str = Path(..., description="Year for injuries"),
    season_type: str = Path(..., description="Season type (REG, PRE, PST)"),
    week: str = Path(..., description="Week number")
):
    """
    Get injuries for a specific week.
    
    - **year**: Year for injuries
    - **season_type**: Season type (REG = Regular Season, PRE = Preseason, PST = Postseason)
    - **week**: Week number
    """
    return await nfl_service.get_weekly_injuries(year, season_type, week)


@router.post("/query", response_model=NFLQueryResponse, summary="Ask a question about NFL data")
async def ask_nfl_question(query: NFLQuery):
    """
    Ask a natural language question about NFL data and get an AI-powered response.
    
    Examples:
    - "Who are the top quarterbacks this season?"
    - "What's the injury status for the Chiefs this week?"
    - "Show me the Packers' upcoming schedule"
    - "What's the depth chart for the Cowboys?"
    - "Which teams are playing this weekend?"
    """
    response = await nfl_query_service.process_query(query.query)
    return response