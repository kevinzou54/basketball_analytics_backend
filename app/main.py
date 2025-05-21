# main.py
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


# Temporary mock database
mock_players = {
    "lebron-james": {
        "points_per_game": 25.4,
        "true_shooting_pct": 0.588,
        "usage_rate": 31.0,
        "team": "Lakers",
    },
    "stephen-curry": {
        "points_per_game": 29.6,
        "true_shooting_pct": 0.647,
        "usage_rate": 30.3,
        "team": "Warriors",
    },
}

class PlayerStats(BaseModel):
    points_per_game: float
    true_shooting_pct: float
    usage_rate: float
    team: str

from fastapi import HTTPException

@app.get("/player/{name}", response_model=PlayerStats)
def get_player_stats(name: str):
    player_key = name.lower().replace(" ", "-")
    if player_key not in mock_players:
        raise HTTPException(status_code=404, detail="Player not found")
    return mock_players[player_key]
