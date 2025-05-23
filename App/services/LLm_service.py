# filepath: d:\My works(Fuad)\NFL_Allsports_API\App\services\LLm_service.py
import os
import json
import httpx
import hashlib
import time
from typing import Dict, List, Any
from App.core.config import settings

llm_cache = {}
LLM_CACHE_TTL = 60 * 10  # 10 minutes

class LLMService:
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.base_url = "https://api.openai.com/v1/chat/completions"
        self.model = "gpt-4"  # Using GPT-4 for better NFL analysis

    async def generate_response(self, query: str, context_data: Dict[str, Any] = None) -> str:
        """
        Generate a response using OpenAI's GPT model based on the user query and NFL data context
        
        Args:
            query (str): The user's query about NFL data
            context_data (dict): NFL data to provide as context to the LLM
            
        Returns:
            str: The LLM's response
        """
        # Create a cache key based on query and context
        cache_key = hashlib.sha256((query + str(context_data)).encode()).hexdigest()
        now = time.time()
        
        # Check cache
        if cache_key in llm_cache:
            cached_time, cached_response = llm_cache[cache_key]
            if now - cached_time < LLM_CACHE_TTL:
                return cached_response

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        # Preparing the system messages for reply
        system_message = (
            "You are an NFL analytics expert providing insights based on official NFL data. "
            "Focus on providing accurate, data-driven analysis in a conversational tone. "
            "Your responses should be detailed and insightful, drawing both from the provided data "
            "and your general knowledge of NFL. When responding:\n"
            "1. Summarize key information from the data\n"
            "2. Provide relevant statistics and trends\n"
            "3. Offer context about teams, players, or matchups\n"
            "4. Analyze the data to provide meaningful insights\n"
            "5. Make logical inferences based on the data where appropriate\n"
            "6. Cite your sources as 'Based on official NFL data.'"
        )
        
        messages = [{"role": "system", "content": system_message}]
        
        # Process context data if available
        if context_data:
            # Summarize the data to avoid token limits
            summarized_data = self._summarize_context_data(context_data)
            
            # Add instructions on how to use the data
            data_instructions = (
                "The following NFL data is relevant to the user's query. "
                "Use this data to provide detailed insights and statistics in your response. "
                "When the data contains multiple types of information (like standings, schedules, player info), "
                "try to integrate them for a more comprehensive analysis."
            )
            
            messages.append({"role": "system", "content": data_instructions})
            
            # Format and add the summarized context data
            context_str = f"{json.dumps(summarized_data, indent=2)}"
            # Limit context string to avoid token limits
            if len(context_str) > 4000:  # Adjusted for OpenAI context window
                context_str = context_str[:4000] + "...[additional data truncated for size]"
                
            messages.append({"role": "system", "content": context_str})

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.base_url,
                    headers=headers,
                    json={
                        "model": self.model,
                        "messages": messages + [{"role": "user", "content": query}],
                        "temperature": 0.7,
                        "max_tokens": 800,
                    },
                )
                response.raise_for_status()
                
                result = response.json()
                llm_response = result['choices'][0]['message']['content']
                # Store in cache
                llm_cache[cache_key] = (now, llm_response)
                return llm_response
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                return "Rate limit exceeded. Please try again later."
            print(f"Error generating response: {e}")
            return f"Sorry, I couldn't generate a response: {str(e)}"
        except Exception as e:
            print(f"Error generating response: {e}")
            return f"Sorry, I couldn't generate a response: {str(e)}"

    def _summarize_context_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Summarize the context data to a reasonable size for the LLM API, 
        handling combined data from multiple endpoints
        """
        # Create a container for the summarized data
        summarized = {
            "query_type": data.get("query_type", "unknown"),
            "metadata": data.get("metadata", {})
        }
        
        try:
            # Process each type of data in the combined data
            if "league" in data:
                summarized["league_structure"] = self._summarize_league_structure(data["league"])
                
            if "standings" in data:
                summarized["standings"] = self._summarize_standings_data(data["standings"])
                
            if "schedule" in data:
                summarized["schedule"] = self._summarize_schedule_data(data["schedule"])
                
            if "team_profiles" in data:
                summarized["team_profiles"] = {}
                for team_code, profile in data["team_profiles"].items():
                    summarized["team_profiles"][team_code] = self._summarize_team_profile(profile)
                    
            if "injuries" in data:
                summarized["injuries"] = self._summarize_injury_data(data["injuries"])
                
            if "team_injuries" in data:
                summarized["team_injuries"] = {}
                for team_code, injuries in data["team_injuries"].items():
                    summarized["team_injuries"][team_code] = self._summarize_team_injuries(injuries)
                    
            if "relevant_games" in data:
                summarized["relevant_games"] = self._summarize_games(data["relevant_games"])
                
            if "team_games" in data:
                summarized["team_games"] = {}
                for team_code, games in data["team_games"].items():
                    summarized["team_games"][team_code] = self._summarize_games(games)
                    
            if "boxscore" in data:
                summarized["boxscore"] = self._summarize_boxscore(data["boxscore"])
                
            return summarized
        except Exception as e:
            print(f"Error during data summarization: {e}")
            return {"summary": "Data available but could not be summarized due to an error",
                    "error": str(e)}

    def _summarize_league_structure(self, league_data: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize league structure data"""
        if not league_data:
            return {}
            
        summary = {
            "league_name": league_data.get("name", "NFL"),
            "conferences": []
        }
        
        try:
            if "conferences" in league_data:
                for conference in league_data["conferences"]:
                    conf_summary = {
                        "name": conference.get("name", ""),
                        "alias": conference.get("alias", ""),
                        "divisions": []
                    }
                    
                    for division in conference.get("divisions", []):
                        div_summary = {
                            "name": division.get("name", ""),
                            "alias": division.get("alias", ""),
                            "teams": []
                        }
                        
                        for team in division.get("teams", []):
                            div_summary["teams"].append({
                                "name": team.get("name", ""),
                                "market": team.get("market", ""),
                                "alias": team.get("alias", "")
                            })
                        
                        conf_summary["divisions"].append(div_summary)
                    
                    summary["conferences"].append(conf_summary)
            
            return summary
        except Exception as e:
            print(f"Error summarizing league structure: {e}")
            return {"summary": "League structure data available but could not be summarized"}

    def _summarize_team_profile(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize team profile data to essential information"""
        if not profile_data:
            return {}
            
        summary = {
            "team_info": {},
            "coaches": [],
            "key_players": []
        }
        
        try:
            # Basic team info
            summary["team_info"] = {
                "id": profile_data.get("id", ""),
                "name": profile_data.get("name", ""),
                "market": profile_data.get("market", ""),
                "alias": profile_data.get("alias", ""),
                "conference": profile_data.get("conference", ""),
                "division": profile_data.get("division", "")
            }
            
            # Coaches
            if "coaches" in profile_data:
                for coach in profile_data["coaches"][:3]:  # Limit to 3 coaches
                    summary["coaches"].append({
                        "name": coach.get("name", ""),
                        "position": coach.get("position", ""),
                        "experience": coach.get("experience", "")
                    })
            
            # Key players (limited to 10)
            if "players" in profile_data:
                for player in sorted(profile_data["players"], 
                                   key=lambda p: p.get("depth", 99))[:10]:  # Top 10 on depth chart
                    summary["key_players"].append({
                        "name": player.get("name", ""),
                        "position": player.get("position", ""),
                        "jersey_number": player.get("jersey_number", ""),
                        "depth": player.get("depth", 0)
                    })
            
            return summary
        except Exception as e:
            print(f"Error summarizing team profile: {e}")
            return {"summary": "Team profile data available but could not be summarized"}
    
    def _summarize_team_injuries(self, injuries_data: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize team injuries data"""
        if not injuries_data:
            return {}
            
        summary = {
            "team": injuries_data.get("name", ""),
            "alias": injuries_data.get("alias", ""),
            "injured_players": []
        }
        
        try:
            if "players" in injuries_data:
                for player in injuries_data["players"][:10]:  # Limit to 10 players
                    summary["injured_players"].append({
                        "name": player.get("name", ""),
                        "position": player.get("position", ""),
                        "status": player.get("status", ""),
                        "injury": player.get("injury", "")
                    })
            
            return summary
        except Exception as e:
            print(f"Error summarizing team injuries: {e}")
            return {"summary": "Team injuries data available but could not be summarized"}
    
    def _summarize_games(self, games_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Summarize a list of games"""
        if not games_data:
            return []
            
        games_summary = []
        
        try:
            # Take up to 5 games to avoid overloading context
            for game in games_data[:5]:
                game_summary = {
                    "id": game.get("id", ""),
                    "status": game.get("status", ""),
                    "scheduled": game.get("scheduled", ""),
                    "home_team": {
                        "name": game.get("home", {}).get("name", ""),
                        "alias": game.get("home", {}).get("alias", ""),
                        "points": game.get("home_points", None)
                    },
                    "away_team": {
                        "name": game.get("away", {}).get("name", ""),
                        "alias": game.get("away", {}).get("alias", ""),
                        "points": game.get("away_points", None)
                    }
                }
                games_summary.append(game_summary)
            
            return games_summary
        except Exception as e:
            print(f"Error summarizing games: {e}")
            return [{"summary": "Games data available but could not be summarized"}]
    
    def _summarize_standings_data(self, standings_data: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize standings data to essential rankings information"""
        if not standings_data:
            return {}
            
        summary = {
            "season": standings_data.get("season", {}).get("year", ""),
            "conferences": []
        }
        
        try:
            if "conferences" in standings_data:
                for conference in standings_data["conferences"]:
                    conf_summary = {
                        "name": conference.get("name", ""),
                        "alias": conference.get("alias", ""),
                        "divisions": []
                    }
                    
                    for division in conference.get("divisions", []):
                        div_summary = {
                            "name": division.get("name", ""),
                            "alias": division.get("alias", ""),
                            "teams": []
                        }
                        
                        for team in division.get("teams", []):
                            div_summary["teams"].append({
                                "name": team.get("name", ""),
                                "alias": team.get("alias", ""),
                                "wins": team.get("wins", 0),
                                "losses": team.get("losses", 0),
                                "ties": team.get("ties", 0),
                                "win_pct": team.get("win_pct", 0),
                                "points_for": team.get("points_for", 0),
                                "points_against": team.get("points_against", 0)
                            })
                        
                        conf_summary["divisions"].append(div_summary)
                    
                    summary["conferences"].append(conf_summary)
            
            return summary
        except Exception as e:
            print(f"Error summarizing standings: {e}")
            return {"summary": "Standings data available but could not be summarized"}
    
    def _summarize_schedule_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize schedule data to essential games info"""
        summarized = {
            "year": data.get("year", ""),
            "type": data.get("type", ""),
            "games": []
        }
        
        try:
            # Take only the first 10 games to limit size
            games = data.get("games", [])[:10]
            for game in games:
                game_summary = {
                    "id": game.get("id", ""),
                    "status": game.get("status", ""),
                    "scheduled": game.get("scheduled", ""),
                    "home_team": {
                        "name": game.get("home", {}).get("name", ""),
                        "alias": game.get("home", {}).get("alias", "")
                    },
                    "away_team": {
                        "name": game.get("away", {}).get("name", ""),
                        "alias": game.get("away", {}).get("alias", "")
                    }
                }
                summarized["games"].append(game_summary)
            
            return summarized
        except Exception as e:
            print(f"Error summarizing schedule data: {e}")
            return {"summary": "Schedule data available but could not be summarized"}

    def _summarize_injury_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize injury report data"""
        summarized = {
            "week": data.get("week", ""),
            "teams_with_injuries": []
        }
        
        try:
            teams = data.get("teams", [])[:10]  # Limit to 10 teams
            for team in teams:
                team_summary = {
                    "name": team.get("name", ""),
                    "alias": team.get("alias", ""),
                    "injuries": []
                }
                
                # Limit to 10 players per team
                players = team.get("players", [])[:10]
                for player in players:
                    player_summary = {
                        "name": player.get("name", ""),
                        "position": player.get("position", ""),
                        "status": player.get("status", ""),
                        "injury": player.get("injury", "")
                    }
                    team_summary["injuries"].append(player_summary)
                
                summarized["teams_with_injuries"].append(team_summary)
            
            return summarized
        except Exception as e:
            print(f"Error summarizing injury data: {e}")
            return {"summary": "Injury data available but could not be summarized"}

    def _summarize_boxscore(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize boxscore data"""
        summarized = {
            "id": data.get("id", ""),
            "status": data.get("status", ""),
            "scheduled": data.get("scheduled", ""),
            "home": {
                "name": data.get("home", {}).get("name", ""),
                "alias": data.get("home", {}).get("alias", ""),
                "points": data.get("home_points", 0),
                "scoring": data.get("home", {}).get("scoring", []),
                "statistics": self._extract_key_stats(data.get("home", {}).get("statistics", {}))
            },
            "away": {
                "name": data.get("away", {}).get("name", ""),
                "alias": data.get("away", {}).get("alias", ""),
                "points": data.get("away_points", 0),
                "scoring": data.get("away", {}).get("scoring", []),
                "statistics": self._extract_key_stats(data.get("away", {}).get("statistics", {}))
            }
        }
        return summarized

    def _extract_key_stats(self, stats: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key team statistics from boxscore"""
        key_stats = {}
        
        if not stats:
            return key_stats
            
        # Team totals
        if "team" in stats:
            team = stats["team"]
            key_stats["team"] = {
                "first_downs": team.get("first_downs", 0),
                "total_yards": team.get("total_yards", 0),
                "penalties": team.get("penalties", 0),
                "penalty_yards": team.get("penalty_yards", 0),
                "turnovers": team.get("turnovers", 0),
                "time_of_possession": team.get("possession_time", "")
            }
        
        # Passing stats
        if "passing" in stats:
            key_stats["passing"] = {
                "completions": stats["passing"].get("completions", 0),
                "attempts": stats["passing"].get("attempts", 0),
                "yards": stats["passing"].get("yards", 0),
                "touchdowns": stats["passing"].get("touchdowns", 0),
                "interceptions": stats["passing"].get("interceptions", 0)
            }
        
        # Rushing stats
        if "rushing" in stats:
            key_stats["rushing"] = {
                "attempts": stats["rushing"].get("attempts", 0),
                "yards": stats["rushing"].get("yards", 0),
                "touchdowns": stats["rushing"].get("touchdowns", 0)
            }
        
        # Receiving stats
        if "receiving" in stats:
            key_stats["receiving"] = {
                "receptions": stats["receiving"].get("receptions", 0),
                "yards": stats["receiving"].get("yards", 0),
                "touchdowns": stats["receiving"].get("touchdowns", 0)
            }
        
        return key_stats

    def _create_generic_summary(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a generic summary for unrecognized data formats"""
        summary = {"data_summary": "NFL data available"}
        
        # Try to extract some useful information
        if isinstance(data, dict):
            # Extract top-level keys and some values
            keys = list(data.keys())[:10]  # First 10 keys
            summary["available_data"] = keys
            
            # If there are lists, report their sizes
            for key in keys:
                if isinstance(data[key], list):
                    summary[f"{key}_count"] = len(data[key])
                    # Sample a few items if they're dictionaries
                    if data[key] and isinstance(data[key][0], dict):
                        sample_keys = list(data[key][0].keys())[:5]
                        summary[f"{key}_contains"] = sample_keys
        
        return summary

llm_service = LLMService()
