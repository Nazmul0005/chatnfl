from fastapi import FastAPI, HTTPException, Query
from typing import Optional, List, Dict, Any
import httpx
import asyncio
from pydantic import BaseModel
from enum import Enum

app = FastAPI(
    title="FantasyNerds NFL API Client",
    description="FastAPI client for FantasyNerds NFL API endpoints",
    version="1.0.0"
)

# Configuration
API_KEY = "ABWTFKDMZU3G6SDPGMMY"
BASE_URL = "https://api.fantasynerds.com"

class Format(str, Enum):
    standard = "standard"
    ppr = "ppr"
    half_ppr = "half-ppr"

class Position(str, Enum):
    qb = "QB"
    rb = "RB"
    wr = "WR"
    te = "TE"
    k = "K"
    def_st = "DEF"

# Response Models
class APIResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# HTTP Client
async def make_api_request(endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
    """Make an async HTTP request to FantasyNerds API"""
    if params is None:
        params = {}
    
    params["apikey"] = API_KEY
    url = f"{BASE_URL}{endpoint}"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return {"success": True, "data": response.json()}
        except httpx.HTTPError as e:
            return {"success": False, "error": f"HTTP error: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"Request failed: {str(e)}"}

# Draft and Ranking Endpoints
@app.get("/auction", response_model=APIResponse, tags=["Draft & Rankings"])
async def get_auction_values(
    teams: int = Query(12, description="Number of teams in league"),
    budget: int = Query(200, description="Auction budget"),
    format: Format = Query(Format.standard, description="Scoring format")
):
    """Get auction values for fantasy football"""
    params = {"teams": teams, "budget": budget, "format": format.value}
    result = await make_api_request("/v1/nfl/auction", params)
    return APIResponse(**result)

@app.get("/adp", response_model=APIResponse, tags=["Draft & Rankings"])
async def get_average_draft_position(
    teams: int = Query(12, description="Number of teams in league"),
    format: Format = Query(Format.standard, description="Scoring format")
):
    """Get Average Draft Position data"""
    params = {"teams": teams, "format": format.value}
    result = await make_api_request("/v1/nfl/adp", params)
    return APIResponse(**result)

@app.get("/bestball", response_model=APIResponse, tags=["Draft & Rankings"])
async def get_bestball_rankings():
    """Get Best Ball rankings"""
    result = await make_api_request("/v1/nfl/bestball")
    return APIResponse(**result)

@app.get("/draft-projections", response_model=APIResponse, tags=["Draft & Rankings"])
async def get_draft_projections():
    """Get draft projections and injury-risk rankings"""
    result = await make_api_request("/v1/nfl/draft-projections")
    return APIResponse(**result)

@app.get("/draft-rankings", response_model=APIResponse, tags=["Draft & Rankings"])
async def get_draft_rankings(
    format: Format = Query(Format.standard, description="Scoring format")
):
    """Get draft rankings"""
    params = {"format": format.value}
    result = await make_api_request("/v1/nfl/draft-rankings", params)
    return APIResponse(**result)

@app.get("/dynasty", response_model=APIResponse, tags=["Draft & Rankings"])
async def get_dynasty_rankings():
    """Get multi-year dynasty rankings"""
    result = await make_api_request("/v1/nfl/dynasty")
    return APIResponse(**result)

@app.get("/tiers", response_model=APIResponse, tags=["Draft & Rankings"])
async def get_player_tiers(
    format: Format = Query(Format.standard, description="Scoring format")
):
    """Get peer-grouped player tiers"""
    params = {"format": format.value}
    result = await make_api_request("/v1/nfl/tiers", params)
    return APIResponse(**result)

# Weekly/Season Data Endpoints
@app.get("/weekly-projections", response_model=APIResponse, tags=["Weekly & Season Data"])
async def get_weekly_projections(
    week: Optional[int] = Query(None, description="NFL week (1-18)"),
    format: Format = Query(Format.standard, description="Scoring format")
):
    """Get weekly statistical projections"""
    params = {"format": format.value}
    if week:
        params["week"] = week
    result = await make_api_request("/v1/nfl/weekly-projections", params)
    return APIResponse(**result)

@app.get("/weekly-rankings", response_model=APIResponse, tags=["Weekly & Season Data"])
async def get_weekly_rankings(
    week: Optional[int] = Query(None, description="NFL week (1-18)"),
    format: Format = Query(Format.standard, description="Scoring format")
):
    """Get weekly rankings"""
    params = {"format": format.value}
    if week:
        params["week"] = week
    result = await make_api_request("/v1/nfl/weekly-rankings", params)
    return APIResponse(**result)

@app.get("/ros", response_model=APIResponse, tags=["Weekly & Season Data"])
async def get_rest_of_season_projections():
    """Get rest of season projections"""
    result = await make_api_request("/v1/nfl/ros")
    return APIResponse(**result)

@app.get("/playoffs", response_model=APIResponse, tags=["Weekly & Season Data"])
async def get_playoff_projections(
    week: Optional[int] = Query(None, description="NFL week")
):
    """Get playoff projections"""
    params = {}
    if week:
        params["week"] = week
    result = await make_api_request("/v1/nfl/playoffs", params)
    return APIResponse(**result)

@app.get("/leaders", response_model=APIResponse, tags=["Weekly & Season Data"])
async def get_fantasy_leaders(
    format: Format = Query(Format.standard, description="Scoring format"),
    position: Optional[Position] = Query(None, description="Player position"),
    week: Optional[int] = Query(None, description="NFL week")
):
    """Get weekly and season fantasy leaders"""
    params = {"format": format.value}
    if position:
        params["position"] = position.value
    if week:
        params["week"] = week
    result = await make_api_request("/v1/nfl/leaders", params)
    return APIResponse(**result)

# Daily Fantasy Sports (DFS) Endpoints
@app.get("/dfs", response_model=APIResponse, tags=["Daily Fantasy Sports"])
async def get_dfs_data(
    slate_id: Optional[str] = Query(None, description="DFS slate ID")
):
    """Get daily fantasy salaries, projections, and value scores"""
    params = {}
    if slate_id:
        params["slateId"] = slate_id
    result = await make_api_request("/v1/nfl/dfs", params)
    return APIResponse(**result)

@app.get("/dfs-slates", response_model=APIResponse, tags=["Daily Fantasy Sports"])
async def get_dfs_slates():
    """Get list of current DFS slates"""
    result = await make_api_request("/v1/nfl/dfs-slates")
    return APIResponse(**result)

# Team and League Information
@app.get("/teams", response_model=APIResponse, tags=["Team & League Info"])
async def get_nfl_teams():
    """Get NFL team rosters"""
    result = await make_api_request("/v1/nfl/teams")
    return APIResponse(**result)

@app.get("/schedule", response_model=APIResponse, tags=["Team & League Info"])
async def get_nfl_schedule():
    """Get NFL schedule"""
    result = await make_api_request("/v1/nfl/schedule")
    return APIResponse(**result)

@app.get("/standings", response_model=APIResponse, tags=["Team & League Info"])
async def get_nfl_standings():
    """Get NFL standings"""
    result = await make_api_request("/v1/nfl/standings")
    return APIResponse(**result)

@app.get("/byes", response_model=APIResponse, tags=["Team & League Info"])
async def get_bye_weeks():
    """Get team bye weeks"""
    result = await make_api_request("/v1/nfl/byes")
    return APIResponse(**result)

@app.get("/weather", response_model=APIResponse, tags=["Team & League Info"])
async def get_weather_forecasts():
    """Get weather forecasts for each team"""
    result = await make_api_request("/v1/nfl/weather")
    return APIResponse(**result)

# Player Information
@app.get("/players", response_model=APIResponse, tags=["Player Info"])
async def get_players(
    include_inactive: bool = Query(False, description="Include inactive players")
):
    """Get complete player listings"""
    params = {"include_inactive": include_inactive}
    result = await make_api_request("/v1/nfl/players", params)
    return APIResponse(**result)

@app.get("/depth", response_model=APIResponse, tags=["Player Info"])
async def get_depth_charts():
    """Get team depth charts"""
    result = await make_api_request("/v1/nfl/depth")
    return APIResponse(**result)

@app.get("/injuries", response_model=APIResponse, tags=["Player Info"])
async def get_injury_reports():
    """Get real-time injury reports"""
    result = await make_api_request("/v1/nfl/injuries")
    return APIResponse(**result)

@app.get("/add-drops", response_model=APIResponse, tags=["Player Info"])
async def get_player_add_drops():
    """Get recent player adds and drops"""
    result = await make_api_request("/v1/nfl/add-drops")
    return APIResponse(**result)

# IDP (Individual Defensive Player) Endpoints
@app.get("/idp-draft", response_model=APIResponse, tags=["IDP"])
async def get_idp_draft_rankings():
    """Get IDP draft rankings"""
    result = await make_api_request("/v1/nfl/idp-draft")
    return APIResponse(**result)

@app.get("/idp-weekly", response_model=APIResponse, tags=["IDP"])
async def get_idp_weekly_projections():
    """Get IDP weekly projections"""
    result = await make_api_request("/v1/nfl/idp-weekly")
    return APIResponse(**result)

# Defense and Analysis
@app.get("/defense-rankings", response_model=APIResponse, tags=["Defense & Analysis"])
async def get_defensive_rankings():
    """Get defensive unit rankings"""
    result = await make_api_request("/v1/nfl/defense-rankings")
    return APIResponse(**result)

@app.get("/news", response_model=APIResponse, tags=["Defense & Analysis"])
async def get_news():
    """Get news and analysis"""
    result = await make_api_request("/v1/nfl/news")
    return APIResponse(**result)

@app.get("/nfl-picks", response_model=APIResponse, tags=["Defense & Analysis"])
async def get_nfl_picks():
    """Get expert NFL game picks"""
    result = await make_api_request("/v1/nfl/nfl-picks")
    return APIResponse(**result)

# Batch Data Endpoints
@app.get("/fetch-all-draft-data", response_model=List[APIResponse], tags=["Batch Operations"])
async def fetch_all_draft_data():
    """Fetch all draft-related data in parallel"""
    endpoints = [
        ("/v1/nfl/auction", {"teams": 12, "budget": 200, "format": "standard"}),
        ("/v1/nfl/adp", {"teams": 12, "format": "standard"}),
        ("/v1/nfl/bestball", {}),
        ("/v1/nfl/draft-projections", {}),
        ("/v1/nfl/draft-rankings", {"format": "standard"}),
        ("/v1/nfl/dynasty", {}),
        ("/v1/nfl/tiers", {"format": "standard"})
    ]
    
    tasks = [make_api_request(endpoint, params) for endpoint, params in endpoints]
    results = await asyncio.gather(*tasks)
    return [APIResponse(**result) for result in results]

@app.get("/fetch-all-weekly-data", response_model=List[APIResponse], tags=["Batch Operations"])
async def fetch_all_weekly_data(week: Optional[int] = Query(None, description="NFL week")):
    """Fetch all weekly data in parallel"""
    base_params = {"format": "standard"}
    if week:
        base_params["week"] = week
    
    endpoints = [
        ("/v1/nfl/weekly-projections", base_params),
        ("/v1/nfl/weekly-rankings", base_params),
        ("/v1/nfl/ros", {}),
        ("/v1/nfl/leaders", base_params),
        ("/v1/nfl/injuries", {}),
        ("/v1/nfl/add-drops", {})
    ]
    
    tasks = [make_api_request(endpoint, params) for endpoint, params in endpoints]
    results = await asyncio.gather(*tasks)
    return [APIResponse(**result) for result in results]

@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "api_key_configured": bool(API_KEY)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)