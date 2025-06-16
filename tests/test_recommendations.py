import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, ANY
import pandas as pd

from app.main import app # Assuming FastAPI app instance
# Import models and functions to be tested if they are not part of the app's namespace directly
# from app.main import RecommendationRequest, RecommendedPlayer, RecommendationResponse
# from app.main import calculate_heuristic_score_for_player # If it were standalone
# For now, testing calculate_heuristic_score_for_player implicitly via endpoint, or need to extract it.
# For robust unit testing, calculate_heuristic_score_for_player should ideally be importable.
# Let's assume it's accessible or test its logic via the endpoint.

client = TestClient(app)

# --- Mock Data ---
MOCK_ACTIVE_PLAYERS_LIST = [
    {"id": 1, "full_name": "Player One", "is_active": True}, # High Scorer
    {"id": 2, "full_name": "Player Two", "is_active": True}, # Good Rebounder
    {"id": 3, "full_name": "Player Three", "is_active": True}, # Low TOV, Low Volume Pct
    {"id": 4, "full_name": "Player Four", "is_active": True}, # Filtered Out (Low GP)
    {"id": 5, "full_name": "Player Five", "is_active": True}, # Filtered Out (Low MPG)
    {"id": 6, "full_name": "Player Six", "is_active": True}, # High FG% High Volume
]

# Mock for app.main.get_player_data_from_nba_api
# This function returns a dictionary with keys like "historical_regular_seasons"
# where historical_regular_seasons is a list of SeasonStats objects.
# SeasonStats has basic_stats (BasicStatsModel) and advanced_stats (AdvancedStatsModel)

def create_mock_player_data_bundle(player_id, gp, min_pg, pts_pg, reb_pg, ast_pg, stl_pg, blk_pg, tov_pg, fg3m_pg, fg_pct, fga_pg, ft_pct, fta_pg, ts_pct=None, ws=None, pie=None, team="XYZ"):
    # Helper to create the nested structure expected by recommendation logic

    # Mock BasicStatsModel structure
    basic_stats_data = {
        "gp": gp, "gs": gp, "min_per_game": min_pg, "pts_per_game": pts_pg,
        "fgm_per_game": pts_pg / 2, "fga_per_game": fga_pg, "fg_pct": fg_pct,
        "fg3m_per_game": fg3m_pg, "fg3a_per_game": fg3m_pg * 2 if fg3m_pg else 0, "fg3_pct": 0.35 if fg3m_pg else 0,
        "ftm_per_game": 2.0, "fta_per_game": fta_pg, "ft_pct": ft_pct,
        "oreb_per_game": reb_pg / 3, "dreb_per_game": reb_pg * 2/3, "reb_per_game": reb_pg,
        "ast_per_game": ast_pg, "tov_per_game": tov_pg, "stl_per_game": stl_pg, "blk_per_game": blk_pg, "pf_per_game": 2.0
    }
    # Mock AdvancedStatsModel structure
    advanced_stats_data = {
        "off_rating": 110.0, "def_rating": 105.0, "net_rating": 5.0,
        "ast_pct": 0.15, "ast_to_val": 2.0, "ast_ratio": 15.0,
        "oreb_pct": 0.10, "dreb_pct": 0.20, "reb_pct": 0.15,
        "tm_tov_pct": 0.12, "efg_pct": (fg_pct + 0.5 * (fg3m_pg / fga_pg if fga_pg > 0 else 0)) if fg_pct and fg3m_pg is not None else 0.5,
        "ts_pct": ts_pct if ts_pct is not None else 0.55,
        "usg_pct": 0.20, "pace": 100.0,
        "pie": pie if pie is not None else 0.1,
        "ws": ws if ws is not None else 2.0
    }

    # Dynamically create Pydantic model instances from app.main
    from app.main import BasicStatsModel, AdvancedStatsModel, SeasonStats

    mock_basic_stats = BasicStatsModel(**basic_stats_data)
    mock_advanced_stats = AdvancedStatsModel(**advanced_stats_data)

    mock_season_stats = SeasonStats(
        season_id="2022-23", team_abbreviation=team, player_age=25,
        basic_stats=mock_basic_stats, advanced_stats=mock_advanced_stats
    )

    return {
        "player_id": player_id, # Not part of get_player_data_from_nba_api output, but useful for mock setup
        "historical_regular_seasons": [mock_season_stats],
        "career_regular_season": None, # Not used by current recommendation logic
        "historical_playoff_seasons": None,
        "career_playoffs": None,
    }

MOCK_PLAYER_DATA_BUNDLES = {
    1: create_mock_player_data_bundle(player_id=1, gp=70, min_pg=30.0, pts_pg=25.0, reb_pg=5.0, ast_pg=5.0, stl_pg=1.0, blk_pg=0.5, tov_pg=2.0, fg3m_pg=2.0, fg_pct=0.450, fga_pg=18.0, ft_pct=0.800, fta_pg=5.0, ts_pct=0.580, ws=8.0, pie=0.15),
    2: create_mock_player_data_bundle(player_id=2, gp=65, min_pg=32.0, pts_pg=15.0, reb_pg=10.0, ast_pg=2.0, stl_pg=0.5, blk_pg=1.5, tov_pg=1.5, fg3m_pg=0.5, fg_pct=0.500, fga_pg=10.0, ft_pct=0.750, fta_pg=4.0, ts_pct=0.590, ws=7.0, pie=0.13),
    3: create_mock_player_data_bundle(player_id=3, gp=75, min_pg=20.0, pts_pg=8.0, reb_pg=3.0, ast_pg=1.0, stl_pg=0.8, blk_pg=0.2, tov_pg=0.5, fg3m_pg=1.0, fg_pct=0.380, fga_pg=5.0, ft_pct=0.900, fta_pg=1.0, ts_pct=0.520, ws=3.0, pie=0.08), # Low volume for FG/FT PCT
    4: create_mock_player_data_bundle(player_id=4, gp=5, min_pg=25.0, pts_pg=20.0, reb_pg=5.0, ast_pg=5.0, stl_pg=1.0, blk_pg=0.5, tov_pg=2.0, fg3m_pg=2.0, fg_pct=0.450, fga_pg=18.0, ft_pct=0.800, fta_pg=5.0), # Filtered: Low GP
    5: create_mock_player_data_bundle(player_id=5, gp=70, min_pg=10.0, pts_pg=10.0, reb_pg=2.0, ast_pg=1.0, stl_pg=0.3, blk_pg=0.1, tov_pg=1.0, fg3m_pg=0.2, fg_pct=0.400, fga_pg=8.0, ft_pct=0.700, fta_pg=2.0),  # Filtered: Low MPG
    6: create_mock_player_data_bundle(player_id=6, gp=70, min_pg=30.0, pts_pg=18.0, reb_pg=4.0, ast_pg=3.0, stl_pg=0.9, blk_pg=0.4, tov_pg=2.5, fg3m_pg=1.0, fg_pct=0.550, fga_pg=15.0, ft_pct=0.850, fta_pg=3.0, ts_pct=0.620, ws=9.0, pie=0.16), # High FG% high volume
}

# Mock for nba_api.stats.static.players.get_active_players()
@patch('app.main.nba_static_players.get_active_players', return_value=MOCK_ACTIVE_PLAYERS_LIST)
# Mock for app.main.get_player_data_from_nba_api
# This mock needs to return the correct bundle based on player_id
def mock_get_player_data_bundle(player_id, fetch_regular_season, fetch_playoffs, fetch_basic, fetch_advanced):
    # Simplified: always return the pre-defined bundle if ID matches
    return MOCK_PLAYER_DATA_BUNDLES.get(player_id)


@patch('app.main.get_player_data_from_nba_api', side_effect=mock_get_player_data_bundle)
class TestRecommendationEndpoint:

    def test_recommend_points_and_steals(self, mock_get_player_data, mock_get_active_players_static):
        request_data = {
            "target_categories": ["PTS", "STL"],
            "num_recommendations": 2
        }
        response = client.post("/recommendations/categories", json=request_data)
        assert response.status_code == 200
        data = response.json()

        assert "recommendations" in data
        recommendations = data["recommendations"]
        assert len(recommendations) == 2

        # Expected scoring:
        # P1: PTS=25, STL=1.0. Score = 25 + 1.0 = 26.0
        # P2: PTS=15, STL=0.5. Score = 15 + 0.5 = 15.5
        # P3: PTS=8, STL=0.8. Score = 8 + 0.8 = 8.8
        # P6: PTS=18, STL=0.9. Score = 18 + 0.9 = 18.9
        # Expected order: P1, P6

        assert recommendations[0]["player_id"] == 1 # Player One
        assert recommendations[0]["full_name"] == "Player One"
        assert recommendations[0]["recommendation_score"] > recommendations[1]["recommendation_score"]
        assert recommendations[0]["targeted_category_stats"]["PTS"] == 25.0
        assert recommendations[0]["targeted_category_stats"]["STL"] == 1.0

        assert recommendations[1]["player_id"] == 6 # Player Six

    def test_recommend_tov_lower_is_better(self, mock_get_player_data, mock_get_active_players_static):
        request_data = {
            "target_categories": ["TOV"], # Lower TOV is better
            "num_recommendations": 1
        }
        response = client.post("/recommendations/categories", json=request_data)
        assert response.status_code == 200
        data = response.json()
        recommendations = data["recommendations"]
        assert len(recommendations) == 1

        # P1 TOV=2.0 (Score -2.0)
        # P2 TOV=1.5 (Score -1.5)
        # P3 TOV=0.5 (Score -0.5) -> Best (highest score)
        # P6 TOV=2.5 (Score -2.5)
        assert recommendations[0]["player_id"] == 3 # Player Three (lowest TOV)
        assert recommendations[0]["targeted_category_stats"]["TOV"] == 0.5

    def test_recommend_fg_pct_volume_weighted(self, mock_get_player_data, mock_get_active_players_static):
        request_data = {
            "target_categories": ["FG_PCT"],
            "num_recommendations": 2
        }
        response = client.post("/recommendations/categories", json=request_data)
        assert response.status_code == 200
        data = response.json()
        recommendations = data["recommendations"]
        # P1: 0.45 * 18.0 * 0.1 = 0.81
        # P2: 0.50 * 10.0 * 0.1 = 0.50
        # P3: 0.38 * 5.0 * 0.1 = 0.19
        # P6: 0.55 * 15.0 * 0.1 = 0.825 -> Best
        assert recommendations[0]["player_id"] == 6 # Player Six (high pct, high volume)
        assert recommendations[1]["player_id"] == 1 # Player One
        assert recommendations[0]["targeted_category_stats"]["FG_PCT"] == 0.550

    def test_recommend_excluded_player(self, mock_get_player_data, mock_get_active_players_static):
        request_data = {
            "target_categories": ["PTS"],
            "excluded_player_ids": [1], # Exclude Player One (highest PTS)
            "num_recommendations": 1
        }
        response = client.post("/recommendations/categories", json=request_data)
        assert response.status_code == 200
        data = response.json()
        recommendations = data["recommendations"]
        assert len(recommendations) == 1
        # P1 (25 PTS) is excluded. Next best is P6 (18 PTS)
        assert recommendations[0]["player_id"] == 6

    def test_recommend_num_recommendations(self, mock_get_player_data, mock_get_active_players_static):
        request_data = {"target_categories": ["PTS"], "num_recommendations": 3}
        response = client.post("/recommendations/categories", json=request_data)
        assert response.status_code == 200
        data = response.json()
        # P1 (25), P6 (18), P2 (15) are the top 3 eligible for PTS
        assert len(data["recommendations"]) == 3
        assert data["recommendations"][0]["player_id"] == 1
        assert data["recommendations"][1]["player_id"] == 6
        assert data["recommendations"][2]["player_id"] == 2

    def test_recommend_filtered_players_not_included(self, mock_get_player_data, mock_get_active_players_static):
        # Players 4 (low GP) and 5 (low MPG) should be filtered out by default thresholds
        request_data = {"target_categories": ["PTS"], "num_recommendations": 4} # Ask for all possible
        response = client.post("/recommendations/categories", json=request_data)
        assert response.status_code == 200
        data = response.json()
        recommendations = data["recommendations"]
        # Expected eligible players: 1, 2, 3, 6. (4 total)
        assert len(recommendations) == 4
        player_ids_recommended = {p["player_id"] for p in recommendations}
        assert 4 not in player_ids_recommended
        assert 5 not in player_ids_recommended

    def test_recommend_unknown_category(self, mock_get_player_data, mock_get_active_players_static):
        request_data = {"target_categories": ["UNKNOWN_CAT", "PTS"], "num_recommendations": 1}
        response = client.post("/recommendations/categories", json=request_data)
        assert response.status_code == 200 # Should still succeed, just ignore unknown category
        data = response.json()
        recommendations = data["recommendations"]
        assert len(recommendations) == 1
        assert recommendations[0]["player_id"] == 1 # Based on PTS
        assert recommendations[0]["targeted_category_stats"]["PTS"] == 25.0
        assert "UNKNOWN_CAT" in recommendations[0]["targeted_category_stats"]
        assert recommendations[0]["targeted_category_stats"]["UNKNOWN_CAT"] is None # Shows it was targeted but not scored

    def test_no_players_meet_criteria_or_available(self, mock_get_player_data, mock_no_active_players_fixture): # Renamed fixture
        # Mock get_active_players to return empty list
        # This test now uses the fixture correctly
        request_data = {"target_categories": ["PTS"], "num_recommendations": 5}
        response = client.post("/recommendations/categories", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert len(data["recommendations"]) == 0

# It would also be good to have direct unit tests for `calculate_heuristic_score_for_player`
# if it were refactored to be easily importable and testable in isolation.
# For now, its logic is tested via the endpoint tests.

# Pytest fixture for mocking get_active_players to return empty list
@pytest.fixture
def mock_no_active_players_fixture(monkeypatch): # Renamed fixture
    monkeypatch.setattr("app.main.nba_static_players.get_active_players", lambda: [])
