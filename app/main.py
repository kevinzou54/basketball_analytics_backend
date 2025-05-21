from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from nba_api.stats.endpoints import playercareerstats
from nba_api.stats.static import players

app = FastAPI()

class PlayerStats(BaseModel):
    points_per_game: float
    true_shooting_pct: float
    usage_rate: float
    team: str

def get_player_id(name: str):
    # Use NBA API's player search
    player_list = players.get_players()
    name = name.lower().replace("-", " ")
    for player in player_list:
        if player["full_name"].lower() == name:
            return player["id"]
    return None

@app.get("/player/{name}", response_model=PlayerStats)
def get_player_stats(name: str):
    player_id = get_player_id(name)
    if not player_id:
        raise HTTPException(status_code=404, detail="Player not found")

    career = playercareerstats.PlayerCareerStats(player_id=player_id)
    stats = career.get_data_frames()[0].iloc[-1]  # Most recent season

    # Very simplified logic — we'll improve this later
    return {
        "points_per_game": float(stats["PTS"] / stats["GP"]),
        "true_shooting_pct": 0.58,  # Placeholder, not directly available
        "usage_rate": 30.0,         # Placeholder
        "team": stats["TEAM_ABBREVIATION"],
    }

from functools import lru_cache
from nba_api.stats.static import players

@lru_cache(maxsize=128)
def get_player_id(name: str):
    player_list = players.get_players()
    name = name.lower().replace("-", " ")
    for player in player_list:
        if player["full_name"].lower() == name:
            return player["id"]
    return None
