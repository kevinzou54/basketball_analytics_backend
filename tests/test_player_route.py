# tests/test_player_route.py

from fastapi.testclient import TestClient
from app.main import app
from app.main import get_cached_player_stats, get_player_id


client = TestClient(app)


def test_get_player_stats_valid():
    response = client.get("/player/lebron-james")
    assert response.status_code == 200
    data = response.json()
    assert "points_per_game" in data
    assert data["team"] == "LAL"



def test_get_player_stats_invalid():
    response = client.get("/player/unknown-player")
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Player not found"



def test_get_cached_player_stats_for_known_player():
    lebron_id = get_player_id("lebron-james")
    stats = get_cached_player_stats(lebron_id)

    assert isinstance(stats, dict)
    assert "points_per_game" in stats
    assert "true_shooting_pct" in stats
    assert "usage_rate" in stats
    assert "team" in stats
    assert isinstance(stats["points_per_game"], float)
    assert isinstance(stats["true_shooting_pct"], float)
    assert stats["usage_rate"] in ["N/A", None] or isinstance(stats["usage_rate"], float)



def test_compare_players():
    response = client.get("/compare?player1=lebron-james&player2=stephen-curry")
    assert response.status_code == 200

    data = response.json()
    assert "player1" in data
    assert "player2" in data

    for stat in [
        "points_per_game", 
        "assists_per_game", 
        "fg_pct", 
        "minutes_per_game"
    ]:
        assert stat in data["player1"]
        assert stat in data["player2"]

        

def test_lineup_stats():
    response = client.post("/lineup", json={
        "players": ["lebron-james", "stephen-curry", "kevin-durant"]
    })
    assert response.status_code == 200
    data = response.json()

    assert "lineup" in data
    assert "avg_points_per_game" in data
    assert "avg_true_shooting_pct" in data
    assert "avg_rebounds_per_game" in data
    assert "total_minutes_per_game" in data
    assert isinstance(data["avg_points_per_game"], float)
    assert isinstance(data["total_minutes_per_game"], float)
