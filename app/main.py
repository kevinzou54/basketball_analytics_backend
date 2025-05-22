from fastapi import FastAPI, HTTPException, Query, Body
from pydantic import BaseModel
from nba_api.stats.endpoints import playercareerstats
from nba_api.stats.static import players
from functools import lru_cache
from typing import Union, List, Optional

app = FastAPI()


class PlayerStats(BaseModel):
    points_per_game: float
    true_shooting_pct: float
    rebounds_per_game: float
    assists_per_game: float
    steals_per_game: float
    blocks_per_game: float
    turnovers_per_game: float
    fg_pct: float
    fg3_pct: float
    ft_pct: float
    minutes_per_game: float
    usage_rate: Union[str, float]
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
        "rebounds_per_game": round(stats["REB"] / gp, 1),
        "assists_per_game": round(stats["AST"] / gp, 1),
        "steals_per_game": round(stats["STL"] / gp, 1),
        "blocks_per_game": round(stats["BLK"] / gp, 1),
        "turnovers_per_game": round(stats["TOV"] / gp, 1),
        "fg_pct": round(stats["FG_PCT"], 3),
        "fg3_pct": round(stats["FG3_PCT"], 3),
        "ft_pct": round(stats["FT_PCT"], 3),
        "minutes_per_game": round(stats["MIN"] / gp, 1),
        "usage_rate": "N/A",
        "team": stats["TEAM_ABBREVIATION"],
}

@app.get("/compare")


def compare_players(
    player1: str = Query(...), 
    player2: str = Query(...)
):
    p1_id = get_player_id(player1)
    p2_id = get_player_id(player2)

    if not p1_id or not p2_id:
        raise HTTPException(
            status_code=404, 
            detail="One or both players not found")

    try:
        p1_stats = get_cached_player_stats(p1_id)
        p2_stats = get_cached_player_stats(p2_id)
    except ValueError:
        raise HTTPException(
            status_code=500, 
            detail="Failed to retrieve stats for one or both players")

    # Use capitalized names in output for readability
    def format_name(slug):
        return " ".join(word.capitalize() for word in slug.split("-"))

    return {
        "player1": {**p1_stats, "name": format_name(player1)},
        "player2": {**p2_stats, "name": format_name(player2)}
    }


@app.post("/lineup")


def get_lineup_stats(
    players: List[str] = Body(...),
    metric: str = Query("avg", pattern="^(avg|total)$"),
    stats: Optional[str] = Query(None)
):
    player_stats = []
    names = []

    for player_slug in players:
        player_id = get_player_id(player_slug)
        if not player_id:
            raise HTTPException(
                status_code=404, 
                detail=f"Player '{player_slug}' not found")

        try:
            stats_data = get_cached_player_stats(player_id)
        except ValueError:
            raise HTTPException(
                status_code=500, 
                detail=f"Stats unavailable for '{player_slug}'")

        player_stats.append(stats_data)
        names.append(" ".join(word.capitalize() for word in player_slug.split("-")))

    # Filter down to valid fields
    stat_fields = list(player_stats[0].keys())
    stat_fields.remove("team")         # Don't aggregate team names
    stat_fields.remove("usage_rate")   # Placeholder field, not numeric

    if stats:
        requested = set(stats.split(","))
        stat_fields = [field for field in stat_fields if field in requested]

    # Perform aggregation
    def aggregate(field):
        values = [p[field] for p in player_stats]
        if metric == "avg":
            return round(sum(values) / len(values), 2) 
        else: round(sum(values), 2)

    return {
        "lineup": names,
        "metric": metric,
        **{f"{metric}_{field}": aggregate(field) for field in stat_fields}
    }

