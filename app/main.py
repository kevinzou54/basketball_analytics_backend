from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from nba_api.stats.endpoints import playercareerstats
from nba_api.stats.static import players
from functools import lru_cache
from typing import Union

app = FastAPI()

class PlayerStats(BaseModel):
    points_per_game: float
    true_shooting_pct: float
    usage_rate: Union[float, str]  # allows either number or "N/A"
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

    try:
        return get_cached_player_stats(player_id)
    except ValueError:
        raise HTTPException(status_code=500, detail="Player data is incomplete")




from nba_api.stats.static import players

@lru_cache(maxsize=128)
def get_player_id(name: str):
    player_list = players.get_players()
    name = name.lower().replace("-", " ")
    for player in player_list:
        if player["full_name"].lower() == name:
            return player["id"]
    return None



@lru_cache(maxsize=128)
def get_cached_player_stats(player_id: int):
    career = playercareerstats.PlayerCareerStats(player_id=player_id)
    stats = career.get_data_frames()[0].iloc[-1]  # most recent season

    gp = stats["GP"]
    pts = stats["PTS"]
    fga = stats["FGA"]
    fta = stats["FTA"]

    # Defensive fallback if stats are missing
    if gp == 0 or fga == 0:
        raise ValueError("Insufficient data for this player")

    # Calculate advanced stats
    ppg = round(pts / gp, 1)
    ts_pct = round(pts / (2 * (fga + 0.44 * fta)), 3)

    return {
        "points_per_game": ppg,
        "true_shooting_pct": ts_pct,
        "usage_rate": "N/A",  # Placeholder until you switch endpoints
        "team": stats["TEAM_ABBREVIATION"],
    }