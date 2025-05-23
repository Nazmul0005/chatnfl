from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import httpx
import asyncio
import json
import openai
from datetime import datetime
import re
import os
from enum import Enum

app = FastAPI(
    title="NFL Fantasy Sports AI Chatbot",
    description="AI-powered chatbot for NFL fantasy sports data using FantasyNerds API",
    version="1.0.0"
)

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your-openai-api-key-here")
FANTASY_NERDS_API_KEY = "ABWTFKDMZU3G6SDPGMMY"
FANTASY_NERDS_BASE_URL = "https://api.fantasynerds.com"

# Initialize OpenAI client
openai.api_key = OPENAI_API_KEY

class ChatMessage(BaseModel):
    message: str
    user_id: Optional[str] = "default"

class ChatResponse(BaseModel):
    response: str
    data_used: Optional[List[str]] = None
    timestamp: str

class Format(str, Enum):
    standard = "standard"
    ppr = "ppr"
    half_ppr = "half-ppr"

class NFLDataFetcher:
    """Handles all NFL API data fetching"""
    
    @staticmethod
    async def make_api_request(endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make an async HTTP request to FantasyNerds API"""
        if params is None:
            params = {}
        
        params["apikey"] = FANTASY_NERDS_API_KEY
        url = f"{FANTASY_NERDS_BASE_URL}{endpoint}"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(url, params=params)
                response.raise_for_status()
                return {"success": True, "data": response.json(), "endpoint": endpoint}
            except Exception as e:
                return {"success": False, "error": f"Failed to fetch {endpoint}: {str(e)}", "endpoint": endpoint}

    @staticmethod
    async def get_auction_values(teams: int = 12, budget: int = 200, format: str = "standard"):
        return await NFLDataFetcher.make_api_request("/v1/nfl/auction", {"teams": teams, "budget": budget, "format": format})
    
    @staticmethod
    async def get_adp_data(teams: int = 12, format: str = "standard"):
        return await NFLDataFetcher.make_api_request("/v1/nfl/adp", {"teams": teams, "format": format})
    
    @staticmethod
    async def get_weekly_projections(week: Optional[int] = None, format: str = "standard"):
        params = {"format": format}
        if week:
            params["week"] = week
        return await NFLDataFetcher.make_api_request("/v1/nfl/weekly-projections", params)
    
    @staticmethod
    async def get_weekly_rankings(week: Optional[int] = None, format: str = "standard"):
        params = {"format": format}
        if week:
            params["week"] = week
        return await NFLDataFetcher.make_api_request("/v1/nfl/weekly-rankings", params)
    
    @staticmethod
    async def get_injury_report():
        return await NFLDataFetcher.make_api_request("/v1/nfl/injuries")
    
    @staticmethod
    async def get_news():
        return await NFLDataFetcher.make_api_request("/v1/nfl/news")
    
    @staticmethod
    async def get_bye_weeks():
        return await NFLDataFetcher.make_api_request("/v1/nfl/byes")
    
    @staticmethod
    async def get_draft_rankings(format: str = "standard"):
        return await NFLDataFetcher.make_api_request("/v1/nfl/draft-rankings", {"format": format})
    
    @staticmethod
    async def get_dynasty_rankings():
        return await NFLDataFetcher.make_api_request("/v1/nfl/dynasty")
    
    @staticmethod
    async def get_dfs_data(slate_id: Optional[str] = None):
        params = {}
        if slate_id:
            params["slateId"] = slate_id
        return await NFLDataFetcher.make_api_request("/v1/nfl/dfs", params)
    
    @staticmethod
    async def get_schedule():
        return await NFLDataFetcher.make_api_request("/v1/nfl/schedule")
    
    @staticmethod
    async def get_standings():
        return await NFLDataFetcher.make_api_request("/v1/nfl/standings")
    
    @staticmethod
    async def get_depth_charts():
        return await NFLDataFetcher.make_api_request("/v1/nfl/depth")
    
    @staticmethod
    async def get_defense_rankings():
        return await NFLDataFetcher.make_api_request("/v1/nfl/defense-rankings")

class NFLChatBot:
    """AI-powered NFL Fantasy Sports Chatbot"""
    
    def __init__(self):
        self.conversation_history = {}
        
    def extract_parameters_from_query(self, query: str) -> Dict[str, Any]:
        """Extract relevant parameters from user query"""
        params = {}
        
        # Extract week number
        week_match = re.search(r'\b(?:week\s*)?(\d{1,2})\b', query.lower())
        if week_match:
            week = int(week_match.group(1))
            if 1 <= week <= 18:
                params['week'] = week
        
        # Extract team count
        team_match = re.search(r'(\d{1,2})\s*team', query.lower())
        if team_match:
            teams = int(team_match.group(1))
            if 8 <= teams <= 16:
                params['teams'] = teams
        
        # Extract scoring format
        if any(term in query.lower() for term in ['ppr', 'point per reception']):
            params['format'] = 'ppr'
        elif any(term in query.lower() for term in ['half ppr', '0.5 ppr', 'half point']):
            params['format'] = 'half-ppr'
        else:
            params['format'] = 'standard'
        
        return params

    async def determine_endpoints_needed(self, query: str) -> List[str]:
        """Use OpenAI to determine which endpoints to call based on user query"""
        
        system_prompt = """You are an NFL Fantasy Sports API assistant. Based on the user's question, determine which specific API endpoints should be called.

Available endpoints:
- auction: For auction values and draft budgets
- adp: For average draft position data
- weekly-projections: For weekly player projections
- weekly-rankings: For weekly player rankings
- injuries: For injury reports
- news: For latest NFL news
- bye-weeks: For team bye week information
- draft-rankings: For draft rankings
- dynasty: For dynasty league rankings
- dfs: For daily fantasy sports data
- schedule: For NFL game schedules
- standings: For NFL team standings
- depth-charts: For team depth charts
- defense-rankings: For defensive unit rankings

Respond with ONLY a JSON array of endpoint names that should be called. For example: ["weekly-projections", "injuries"] or ["auction", "adp"]

User query: {query}"""

        try:
            response = await asyncio.to_thread(
                openai.ChatCompletion.create,
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt.format(query=query)},
                    {"role": "user", "content": query}
                ],
                max_tokens=100,
                temperature=0.1
            )
            
            endpoints_text = response.choices[0].message.content.strip()
            try:
                endpoints = json.loads(endpoints_text)
                return endpoints if isinstance(endpoints, list) else []
            except:
                # Fallback parsing
                return self.fallback_endpoint_detection(query)
                
        except Exception as e:
            print(f"OpenAI API error: {e}")
            return self.fallback_endpoint_detection(query)

    def fallback_endpoint_detection(self, query: str) -> List[str]:
        """Fallback method to detect endpoints using keyword matching"""
        query_lower = query.lower()
        endpoints = []
        
        # Keyword mappings
        keyword_map = {
            'auction': ['auction', 'budget', 'bid', 'dollar'],
            'adp': ['adp', 'average draft position', 'draft position'],
            'weekly-projections': ['projection', 'projected', 'points', 'week'],
            'weekly-rankings': ['ranking', 'rank', 'tier', 'week'],
            'injuries': ['injury', 'injured', 'hurt', 'questionable', 'doubtful'],
            'news': ['news', 'update', 'latest', 'report'],
            'bye-weeks': ['bye', 'bye week', 'off week'],
            'draft-rankings': ['draft', 'draft rank'],
            'dynasty': ['dynasty', 'keeper', 'long term'],
            'dfs': ['dfs', 'daily fantasy', 'draftkings', 'fanduel'],
            'schedule': ['schedule', 'game', 'matchup'],
            'standings': ['standings', 'record', 'wins', 'losses'],
            'depth-charts': ['depth', 'starter', 'backup'],
            'defense-rankings': ['defense', 'dst', 'd/st']
        }
        
        for endpoint, keywords in keyword_map.items():
            if any(keyword in query_lower for keyword in keywords):
                endpoints.append(endpoint)
        
        return endpoints if endpoints else ['weekly-projections']  # Default

    async def fetch_data_for_endpoints(self, endpoints: List[str], params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fetch data from specified endpoints"""
        fetcher = NFLDataFetcher()
        tasks = []
        
        for endpoint in endpoints:
            if endpoint == 'auction':
                tasks.append(fetcher.get_auction_values(
                    teams=params.get('teams', 12),
                    format=params.get('format', 'standard')
                ))
            elif endpoint == 'adp':
                tasks.append(fetcher.get_adp_data(
                    teams=params.get('teams', 12),
                    format=params.get('format', 'standard')
                ))
            elif endpoint == 'weekly-projections':
                tasks.append(fetcher.get_weekly_projections(
                    week=params.get('week'),
                    format=params.get('format', 'standard')
                ))
            elif endpoint == 'weekly-rankings':
                tasks.append(fetcher.get_weekly_rankings(
                    week=params.get('week'),
                    format=params.get('format', 'standard')
                ))
            elif endpoint == 'injuries':
                tasks.append(fetcher.get_injury_report())
            elif endpoint == 'news':
                tasks.append(fetcher.get_news())
            elif endpoint == 'bye-weeks':
                tasks.append(fetcher.get_bye_weeks())
            elif endpoint == 'draft-rankings':
                tasks.append(fetcher.get_draft_rankings(params.get('format', 'standard')))
            elif endpoint == 'dynasty':
                tasks.append(fetcher.get_dynasty_rankings())
            elif endpoint == 'dfs':
                tasks.append(fetcher.get_dfs_data())
            elif endpoint == 'schedule':
                tasks.append(fetcher.get_schedule())
            elif endpoint == 'standings':
                tasks.append(fetcher.get_standings())
            elif endpoint == 'depth-charts':
                tasks.append(fetcher.get_depth_charts())
            elif endpoint == 'defense-rankings':
                tasks.append(fetcher.get_defense_rankings())
        
        if not tasks:
            tasks.append(fetcher.get_weekly_projections(format=params.get('format', 'standard')))
        
        return await asyncio.gather(*tasks)

    async def generate_response(self, query: str, data_results: List[Dict[str, Any]]) -> str:
        """Generate AI response based on query and fetched data"""
        
        # Prepare data summary for the AI
        data_summary = []
        successful_endpoints = []
        
        for result in data_results:
            if result.get('success'):
                successful_endpoints.append(result.get('endpoint', 'unknown'))
                # Limit data size for AI processing
                data_snippet = str(result.get('data', {}))[:2000]
                data_summary.append(f"Data from {result.get('endpoint')}: {data_snippet}")
        
        system_prompt = """You are an expert NFL Fantasy Sports assistant. Answer the user's question using the provided data from FantasyNerds API.

Guidelines:
1. Be conversational and helpful
2. Organize information clearly with bullet points or tables when appropriate
3. Focus on the most relevant information for fantasy football decisions
4. If data is limited, acknowledge it but provide what insights you can
5. Include specific player names, teams, and statistics when available
6. Format numbers clearly (e.g., projections, rankings, percentages)
7. Keep responses informative but concise

Data available: {data_summary}

User question: {query}"""

        try:
            response = await asyncio.to_thread(
                openai.ChatCompletion.create,
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt.format(data_summary='\n'.join(data_summary), query=query)},
                    {"role": "user", "content": query}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # Add data source information
            if successful_endpoints:
                ai_response += f"\n\n*Data sources: {', '.join(successful_endpoints)}*"
            
            return ai_response
            
        except Exception as e:
            return f"I apologize, but I encountered an error generating the response: {str(e)}. However, I was able to fetch data from the following sources: {', '.join(successful_endpoints)}"

    async def process_query(self, query: str, user_id: str = "default") -> ChatResponse:
        """Main method to process user query"""
        try:
            # Extract parameters
            params = self.extract_parameters_from_query(query)
            
            # Determine endpoints needed
            endpoints = await self.determine_endpoints_needed(query)
            
            # Fetch data
            data_results = await self.fetch_data_for_endpoints(endpoints, params)
            
            # Generate response
            response_text = await self.generate_response(query, data_results)
            
            # Track successful endpoints
            successful_endpoints = [r.get('endpoint') for r in data_results if r.get('success')]
            
            return ChatResponse(
                response=response_text,
                data_used=successful_endpoints,
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            return ChatResponse(
                response=f"I apologize, but I encountered an error processing your request: {str(e)}",
                data_used=[],
                timestamp=datetime.now().isoformat()
            )

# Initialize chatbot
chatbot = NFLChatBot()

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(message: ChatMessage):
    """Main chat endpoint"""
    return await chatbot.process_query(message.message, message.user_id)

@app.get("/", response_class=HTMLResponse)
async def get_chat_interface():
    """Serve the chat interface"""
    return """
<!DOCTYPE html>
<html>
<head>
    <title>NFL Fantasy Sports AI Chatbot</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .chat-container { border: 1px solid #ddd; height: 400px; overflow-y: scroll; padding: 10px; margin-bottom: 10px; }
        .message { margin: 10px 0; padding: 10px; border-radius: 5px; }
        .user-message { background-color: #e3f2fd; text-align: right; }
        .bot-message { background-color: #f5f5f5; }
        .input-container { display: flex; }
        .input-container input { flex: 1; padding: 10px; }
        .input-container button { padding: 10px 20px; }
        .data-sources { font-size: 0.8em; color: #666; margin-top: 5px; }
        .examples { background-color: #f9f9f9; padding: 15px; margin: 20px 0; border-radius: 5px; }
        .examples h3 { margin-top: 0; }
        .examples ul { margin: 0; }
        .loading { color: #666; font-style: italic; }
    </style>
</head>
<body>
    <h1>🏈 NFL Fantasy Sports AI Chatbot</h1>
    <p>Ask me anything about NFL fantasy sports! I can help with player projections, rankings, injuries, news, and more.</p>
    
    <div class="examples">
        <h3>Try asking:</h3>
        <ul>
            <li>"What are the top RB projections for week 5?"</li>
            <li>"Show me injury report for this week"</li>
            <li>"Which QBs should I target in my auction draft?"</li>
            <li>"Who are the best dynasty WR prospects?"</li>
            <li>"What teams are on bye this week?"</li>
        </ul>
    </div>
    
    <div id="chat-container" class="chat-container"></div>
    
    <div class="input-container">
        <input type="text" id="message-input" placeholder="Ask about NFL fantasy sports..." onkeypress="handleKeyPress(event)">
        <button onclick="sendMessage()">Send</button>
    </div>

    <script>
        const chatContainer = document.getElementById('chat-container');
        const messageInput = document.getElementById('message-input');
        
        function addMessage(content, isUser = false, dataSources = null) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
            messageDiv.innerHTML = content.replace(/\n/g, '<br>');
            
            if (dataSources && dataSources.length > 0) {
                const sourcesDiv = document.createElement('div');
                sourcesDiv.className = 'data-sources';
                sourcesDiv.textContent = `Data sources: ${dataSources.join(', ')}`;
                messageDiv.appendChild(sourcesDiv);
            }
            
            chatContainer.appendChild(messageDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
        
        async function sendMessage() {
            const message = messageInput.value.trim();
            if (!message) return;
            
            // Disable input while processing
            messageInput.disabled = true;
            
            addMessage(message, true);
            messageInput.value = '';
            
            const loadingMessage = addMessage('🤔 Analyzing your question and fetching data...', false);
            
            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: message })
                });
                
                const data = await response.json();
                
                // Remove the loading message
                chatContainer.removeChild(chatContainer.lastChild);
                
                addMessage(data.response, false, data.data_used);
            } catch (error) {
                // Remove the loading message
                chatContainer.removeChild(chatContainer.lastChild);
                addMessage('Sorry, I encountered an error. Please try again.', false);
            } finally {
                // Re-enable input
                messageInput.disabled = false;
                messageInput.focus();
            }
        }
        
        function handleKeyPress(event) {
            if (event.key === 'Enter') {
                sendMessage();
            }
        }
        
        // Welcome message
        addMessage('Hello! I\'m your NFL Fantasy Sports AI assistant. I can help you with player projections, rankings, injury reports, draft advice, and much more. What would you like to know?', false);
        
        // Focus on input
        messageInput.focus();
    </script>
</body>
</html>
    """

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "openai_configured": bool(OPENAI_API_KEY and OPENAI_API_KEY != "your-openai-api-key-here"),
        "fantasy_nerds_configured": bool(FANTASY_NERDS_API_KEY)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
