# filepath: d:\My works(Fuad)\NFL_Allsports_API\App\services\Nfl_query_service.py
from App.services.api_client import nfl_api_client
from App.services.LLm_service import llm_service
import re
import datetime
from typing import Dict, List, Any, Tuple, Optional

class NFLQueryService:
    """
    Service to handle user queries related to NFL data
    """

    def __init__(self):
        self.api_client = nfl_api_client
        self.llm_service = llm_service
        
        # Define team pattern dictionary for better team extraction
        self.team_patterns = {
            "cardinals": "ARI", "falcons": "ATL", "ravens": "BAL", "bills": "BUF",
            "panthers": "CAR", "bears": "CHI", "bengals": "CIN", "browns": "CLE",
            "cowboys": "DAL", "broncos": "DEN", "lions": "DET", "packers": "GB",
            "texans": "HOU", "colts": "IND", "jaguars": "JAX", "chiefs": "KC",
            "raiders": "LV", "chargers": "LAC", "rams": "LA", "dolphins": "MIA",
            "vikings": "MIN", "patriots": "NE", "saints": "NO", "giants": "NYG",
            "jets": "NYJ", "eagles": "PHI", "steelers": "PIT", "seahawks": "SEA",
            "49ers": "SF", "niners": "SF", "buccaneers": "TB", "bucs": "TB", 
            "titans": "TEN", "commanders": "WAS", "washington": "WAS"
        }

    async def process_query(self, query: str):
        """
        Process a natural language query about NFL data
        
        Args:
            query (str): The user's question about NFL data
            
        Returns:
            dict: Response containing the LLM's answer and relevant data
        """
        
        # Determine query type and fetch relevant data
        query_type, params = self._classify_query(query)
        context_data = await self._fetch_relevant_data(query_type, params)

        # Generate a LLM response with the context data
        llm_response = await self.llm_service.generate_response(query, context_data)

        return {
             "query": query,
             "answer": llm_response,
             "data_sources": self.get_data_sources(query_type)
        }
    
    def _classify_query(self, query: str) -> Tuple[str, Dict[str, Any]]:
        """
        Classify the user's query to determine the type of data needed and extract parameters
        
        Args:
            query (str): The user's question about NFL data
            
        Returns:
            tuple: A tuple containing the query type and parameters
        """
        query = query.lower()
        params = {}
        
        # Extract year if present in query
        year_match = re.search(r'20\d{2}', query)
        if year_match:
            params["year"] = year_match.group(0)
        else:
            # Default to current year
            current_year = datetime.datetime.now().year
            params["year"] = str(current_year)
        
        # Extract week if mentioned
        week_match = re.search(r'week (\d+)', query)
        if week_match:
            params["week"] = week_match.group(1)
        else:
            # Determine current week based on the current date
            # This is a simplified approach - in production you would calculate the actual NFL week
            current_month = datetime.datetime.now().month
            current_day = datetime.datetime.now().day
            
            # Regular season typically starts in September
            if current_month < 9:
                params["week"] = "1"  # Preseason
            else:
                # Rough approximation - a better approach would use a lookup table or API
                week_num = ((current_month - 9) * 4) + (current_day // 7) + 1
                params["week"] = str(min(17, max(1, week_num)))  # Ensure between 1-17
        
        # Extract season type if mentioned
        if any(term in query for term in ["preseason", "pre-season", "pre season"]):
            params["season_type"] = "PRE"
        elif any(term in query for term in ["postseason", "post-season", "post season", "playoffs"]):
            params["season_type"] = "PST"
        else:
            # Determine season type based on current date
            current_month = datetime.datetime.now().month
            if current_month < 9:
                params["season_type"] = "PRE"  # Preseason before September
            elif current_month > 12 or current_month < 3:
                params["season_type"] = "PST"  # Postseason Jan-Feb
            else:
                params["season_type"] = "REG"  # Regular season Sep-Dec
            
        # Extract team mentions
        teams_found = []
        for team_name, team_code in self.team_patterns.items():
            if team_name in query:
                teams_found.append(team_code)
                
        if teams_found:
            params["teams"] = teams_found
            
        # Try to extract player names (simplified approach)
        # In a full implementation, you would have a player database to match against
        name_pattern = r'(?:player|quarterback|qb|running back|rb|wide receiver|wr|tight end|te) ([A-Z][a-z]+ [A-Z][a-z]+)'
        player_match = re.search(name_pattern, query)
        if player_match:
            params["player"] = player_match.group(1)
            
        # Classify query type
        if any(term in query for term in ["ranking", "rank", "best", "top", "stats", "statistics", "projections"]):
            return "player_rankings", params
            
        if any(term in query for term in ["matchup", "vs", "versus", "against", "playing against", "face off", "game between"]):
            return "matchups", params
            
        if any(term in query for term in ["injury", "injured", "hurt", "sidelined", "out", "questionable", "probable"]):
            return "injuries", params
            
        if any(term in query for term in ["schedule", "upcoming", "games", "playing", "when", "calendar"]):
            return "schedule", params
            
        if any(term in query for term in ["depth chart", "roster", "lineup", "starters", "bench", "team composition"]):
            return "depth_chart", params
            
        if any(term in query for term in ["standings", "record", "win-loss", "win/loss", "division standing", "conference standing"]):
            return "standings", params
            
        if any(term in query for term in ["boxscore", "score", "result", "game result", "points", "final score"]):
            return "boxscore", params
            
        # Default to general query
        return "general", params

    async def _fetch_relevant_data(self, query_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetch the relevant NFL data based on query type, combining multiple data sources when needed
        
        Args:
            query_type (str): Type of the query (player_rankings, matchups, etc.)
            params (dict): Parameters extracted from the query
            
        Returns:
            dict: Combined data from relevant endpoints
        """
        try:
            # Get the basic parameters from the params dict
            year = params.get("year", "2023")
            season_type = params.get("season_type", "REG")
            week = params.get("week", "1")
            teams = params.get("teams", [])
            
            # Create a dict to store combined data
            combined_data = {
                "query_type": query_type,
                "metadata": {
                    "year": year,
                    "season_type": season_type,
                    "week": week
                }
            }
            
            # Fetch data based on query type with combined relevant sources
            if query_type == "player_rankings":
                # Get league structure for team context
                combined_data["league"] = await self.api_client.get_teams()
                
                # Get standings for rankings context
                combined_data["standings"] = await self.api_client.get_standings(year, season_type)
                
                # If specific teams mentioned, get their profiles too
                if teams:
                    team_profiles = {}
                    for team_code in teams[:2]:  # Limit to first 2 teams to avoid too many requests
                        try:
                            team_profiles[team_code] = await self.api_client.get_team_profile(team_code)
                        except Exception as e:
                            print(f"Error fetching team profile for {team_code}: {e}")
                    combined_data["team_profiles"] = team_profiles
                
            elif query_type == "matchups":
                # Get schedule data
                combined_data["schedule"] = await self.api_client.get_schedule(year, season_type)
                
                # If specific teams mentioned, filter or highlight their games
                if teams:
                    relevant_games = []
                    for game in combined_data.get("schedule", {}).get("games", []):
                        home_alias = game.get("home", {}).get("alias", "")
                        away_alias = game.get("away", {}).get("alias", "")
                        if home_alias in teams or away_alias in teams:
                            relevant_games.append(game)
                    combined_data["relevant_games"] = relevant_games
                
                    # Get team profiles for the mentioned teams
                    team_profiles = {}
                    for team_code in teams[:2]:  # Limit to first 2 teams
                        try:
                            team_profiles[team_code] = await self.api_client.get_team_profile(team_code)
                        except Exception as e:
                            print(f"Error fetching team profile for {team_code}: {e}")
                    combined_data["team_profiles"] = team_profiles
                
            elif query_type == "injuries":
                # Get injury data for the specified week
                combined_data["injuries"] = await self.api_client.get_weekly_injuries(year, season_type, week)
                
                # Get team context
                combined_data["league"] = await self.api_client.get_teams()
                
                # If specific teams mentioned, highlight their injuries
                if teams:
                    team_injuries = {}
                    injury_data = combined_data.get("injuries", {})
                    for team in injury_data.get("teams", []):
                        if team.get("alias") in teams:
                            team_injuries[team.get("alias")] = team
                    combined_data["team_injuries"] = team_injuries
                
            elif query_type == "schedule":
                # Get the full schedule
                combined_data["schedule"] = await self.api_client.get_schedule(year, season_type)
                
                # Get team context
                combined_data["league"] = await self.api_client.get_teams()
                
                # If specific teams mentioned, filter their games
                if teams:
                    team_games = {}
                    for team_code in teams:
                        team_games[team_code] = []
                        
                    for game in combined_data.get("schedule", {}).get("games", []):
                        home_alias = game.get("home", {}).get("alias", "")
                        away_alias = game.get("away", {}).get("alias", "")
                        for team_code in teams:
                            if home_alias == team_code or away_alias == team_code:
                                team_games[team_code].append(game)
                                
                    combined_data["team_games"] = team_games
                
            elif query_type == "depth_chart":
                # For depth charts, we need detailed team profiles
                combined_data["league"] = await self.api_client.get_teams()
                
                if teams:
                    # Get detailed profile for each mentioned team
                    team_profiles = {}
                    for team_code in teams[:2]:  # Limit to first 2 teams
                        try:
                            team_profiles[team_code] = await self.api_client.get_team_profile(team_code)
                        except Exception as e:
                            print(f"Error fetching team profile for {team_code}: {e}")
                    combined_data["team_profiles"] = team_profiles
                else:
                    # If no teams specified, get profiles for a couple of popular teams
                    popular_teams = ["KC", "SF"]  # Example: Chiefs and 49ers
                    team_profiles = {}
                    for team_code in popular_teams:
                        try:
                            team_profiles[team_code] = await self.api_client.get_team_profile(team_code)
                        except Exception as e:
                            print(f"Error fetching team profile for {team_code}: {e}")
                    combined_data["team_profiles"] = team_profiles
            
            elif query_type == "standings":
                # Get standings data
                combined_data["standings"] = await self.api_client.get_standings(year, season_type)
                
                # Get team context
                combined_data["league"] = await self.api_client.get_teams()
                
            elif query_type == "boxscore":
                # For boxscores, we need schedule first to find relevant games
                schedule_data = await self.api_client.get_schedule(year, season_type)
                combined_data["schedule"] = schedule_data
                
                # If teams mentioned, find recent games involving those teams
                if teams:
                    relevant_games = []
                    for game in schedule_data.get("games", []):
                        home_alias = game.get("home", {}).get("alias", "")
                        away_alias = game.get("away", {}).get("alias", "")
                        if home_alias in teams or away_alias in teams:
                            relevant_games.append(game)
                    
                    # Limit to most recent 1-2 games
                    if relevant_games:
                        # Sort by date (descending) - simplified approach
                        relevant_games.sort(key=lambda g: g.get("scheduled", ""), reverse=True)
                        combined_data["relevant_games"] = relevant_games[:2]
                        
                        # Get boxscore for the most recent game
                        try:
                            game_id = relevant_games[0].get("id")
                            if game_id:
                                combined_data["boxscore"] = await self.api_client.get_game_boxscore(game_id)
                        except Exception as e:
                            print(f"Error fetching boxscore: {e}")
                
            else:  # General query
                # For general queries, provide league structure and standings
                combined_data["league"] = await self.api_client.get_teams()
                combined_data["standings"] = await self.api_client.get_standings(year, season_type)
                
                # Add current week's schedule
                combined_data["schedule"] = await self.api_client.get_schedule(year, season_type)
            
            return combined_data
            
        except Exception as e:
            print(f"Error fetching relevant data: {e}")
            return {"error": str(e), "query_type": query_type}
        
    def get_data_sources(self, query_type):
        """
        Return information about data sources used
        """
        data_sources = {
            "player_rankings": ["NFL team data", "NFL player statistics", "Season standings"],
            "matchups": ["NFL schedule data", "Team profiles", "Head-to-head statistics"],
            "injuries": ["NFL injury reports", "Team rosters", "Player status updates"],
            "schedule": ["NFL team schedules", "League calendar", "Game information"],
            "depth_chart": ["NFL team rosters", "Player position data", "Team composition"],
            "standings": ["NFL division standings", "Conference rankings", "Team records"],
            "boxscore": ["Game statistics", "Player performance data", "Match results"],
            "general": ["NFL general information", "League data", "Current season context"]
        }
        return data_sources.get(query_type, ["NFL API data"])

nfl_query_service = NFLQueryService()
