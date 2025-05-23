# NFL Data API

A FastAPI application that fetches and displays NFL data from the SportsRadar API.

## Features

- Fetch NFL teams hierarchy
- Get NFL schedules
- View team profiles
- View player profiles
- Access game boxscores
- Intelligent API caching to reduce SportsRadar API calls
- Swagger UI for API documentation and testing

## Project Structure

```
NFL_data_retrieved/
├── .env                  # Environment variables
├── requirements.txt      # Project dependencies
├── main.py               # FastAPI application entry point
├── App/                  # Main application package
│   ├── api/              # API endpoints
│   │   └── routes.py     # Route handlers
│   ├── core/             # Core functionality
│   │   └── config.py     # Application configuration
│   ├── models/           # Data models
│   │   └── schemas.py    # Pydantic schemas
│   └── services/         # Service layer
│       └── nfl_service.py  # NFL data service
```

## Setup

1. Clone the repository
2. Create a `.env` file with your SportsRadar API key:
   ```
   SPORTSRADAR_API_KEY=your_api_key_here
   NFL_BASE_URL=https://api.sportradar.com/nfl/official/trial/v7
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Run the application:
   ```
   uvicorn main:app --reload
   ```

## API Documentation

Once the server is running, you can access:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Endpoints

- `GET /api/nfl/teams` - Get all NFL teams
- `GET /api/nfl/schedule/{year}/{season_type}` - Get NFL schedule
- `GET /api/nfl/teams/{team_id}` - Get team profile
- `GET /api/nfl/players/{player_id}` - Get player profile
- `GET /api/nfl/games/{game_id}/boxscore` - Get game boxscore
- `DELETE /api/nfl/cache` - Clear API cache
