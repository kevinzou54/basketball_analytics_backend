# tests/test_player_route.py

from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)

def test_get_player_stats_valid():
    response = client.get("/player/lebron-james")
    assert response.status_code == 200
    data = response.json()
    assert "points_per_game" in data
    assert data["team"] == "Lakers"

def test_get_player_stats_invalid():
    response = client.get("/player/unknown-player")
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Player not found"

