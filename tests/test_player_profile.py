import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import pandas as pd

# Assuming your FastAPI app instance is in app.main
# If app is created by a function, you might need to adjust import
from app.main import app  # , get_player_id # Import other necessary things

# --- Test Client ---
client = TestClient(app)

# --- Mock Data Samples ---

# Mock for players.get_players() used by get_player_id and get_player_name_from_id
MOCK_NBA_PLAYERS_LIST = [
    {"id": 2544, "full_name": "LeBron James", "is_active": True},
    {"id": 201939, "full_name": "Stephen Curry", "is_active": True},
    {
        "id": 12345,
        "full_name": "Non Existent Player",
        "is_active": False,
    },  # Test case for player not found by name
    {"id": 999999, "full_name": "Test Player With No Data", "is_active": True},
]

# Mock DataFrame for PlayerProfileV2().season_totals_regular_season.get_data_frame() - PerGame
MOCK_DF_REG_SEASON_PG = pd.DataFrame(
    {
        "PLAYER_ID": [2544, 2544],
        "SEASON_ID": ["2022-23", "2021-22"],
        "TEAM_ID": [1610612747, 1610612747],
        "TEAM_ABBREVIATION": ["LAL", "LAL"],
        "PLAYER_AGE": [38.0, 37.0],
        "GP": [55, 56],
        "GS": [54, 56],
        "MIN": [35.5, 37.2],
        "FGM": [11.1, 11.3],
        "FGA": [22.2, 21.8],
        "FG_PCT": [0.500, 0.520],
        "FG3M": [2.2, 2.9],
        "FG3A": [6.9, 8.0],
        "FG3_PCT": [0.321, 0.359],
        "FTM": [4.6, 4.8],
        "FTA": [6.0, 6.5],
        "FT_PCT": [0.768, 0.756],
        "OREB": [1.1, 1.1],
        "DREB": [7.2, 6.5],
        "REB": [8.3, 7.6],  # Corrected REB calculation example
        "AST": [6.8, 6.2],
        "STL": [0.9, 1.3],
        "BLK": [0.6, 1.1],
        "TOV": [3.2, 3.5],
        "PF": [1.9, 2.2],
        "PTS": [28.9, 30.3],
    }
)

# Mock DataFrame for PlayerProfileV2().career_totals_regular_season.get_data_frame() - PerGame
MOCK_DF_REG_CAREER_PG = pd.DataFrame(
    {
        "PLAYER_ID": [2544],
        "LEAGUE_ID": ["00"],
        "GP": [1421],
        "GS": [1420],
        "MIN": [38.1],
        "FGM": [10.0],
        "FGA": [19.8],
        "FG_PCT": [0.505],
        "FG3M": [1.6],
        "FG3A": [4.5],
        "FG3_PCT": [0.345],
        "FTM": [5.5],
        "FTA": [7.5],
        "FT_PCT": [0.735],
        "OREB": [1.2],
        "DREB": [6.3],
        "REB": [7.5],
        "AST": [7.3],
        "STL": [1.5],
        "BLK": [0.8],
        "TOV": [3.5],
        "PF": [1.9],
        "PTS": [27.2],
    }
)

# Mock DataFrame for PlayerProfileV2().season_totals_regular_season.get_data_frame() - Advanced
MOCK_DF_REG_SEASON_ADV = pd.DataFrame(
    {
        "PLAYER_ID": [2544, 2544],
        "SEASON_ID": ["2022-23", "2021-22"],
        "TEAM_ID": [1610612747, 1610612747],
        "TEAM_ABBREVIATION": ["LAL", "LAL"],
        "PLAYER_AGE": [38.0, 37.0],
        "GP": [55, 56],
        "GS": [54, 56],
        "MIN": [35.5, 37.2],
        "E_OFF_RATING": [113.0, 112.0],
        "OFF_RATING": [115.7, 114.7],
        "E_DEF_RATING": [110.1, 109.1],
        "DEF_RATING": [112.8, 111.8],
        "E_NET_RATING": [2.9, 2.8],
        "NET_RATING": [2.9, 2.8],
        "AST_PCT": [0.320, 0.300],
        "AST_TO": [2.13, 1.77],
        "AST_RATIO": [19.4, 18.0],
        "OREB_PCT": [0.035, 0.036],
        "DREB_PCT": [0.220, 0.210],
        "REB_PCT": [0.128, 0.123],
        "TM_TOV_PCT": [12.0, 13.0],
        "EFG_PCT": [0.550, 0.580],
        "TS_PCT": [0.583, 0.619],
        "USG_PCT": [0.320, 0.315],
        "E_USG_PCT": [0.325, 0.320],
        "E_PACE": [100.0, 99.5],
        "PACE": [102.31, 101.5],
        "PACE_PER40": [85.26, 84.58],
        "POSS": [4000, 4200],
        "PIE": [0.180, 0.190],
        "FGM_PG": [11.1, 11.3],
        "FGA_PG": [
            22.2,
            21.8,
        ],  # These are not usually in advanced stats but for testing parsing
        "WS": [5.6, 6.0],  # Win Shares
    }
)

# Mock DataFrame for PlayerProfileV2().career_totals_regular_season.get_data_frame() - Advanced
MOCK_DF_REG_CAREER_ADV = pd.DataFrame(
    {
        "PLAYER_ID": [2544],
        "LEAGUE_ID": ["00"],
        "TEAM_ID": [0],
        "GP": [1421],
        "MIN": [38.1],
        "OFF_RATING": [116.0],
        "DEF_RATING": [106.1],
        "NET_RATING": [9.9],
        "AST_PCT": [0.358],
        "AST_TO": [1.98],
        "AST_RATIO": [20.1],
        "OREB_PCT": [0.037],
        "DREB_PCT": [0.197],
        "REB_PCT": [0.117],
        "TM_TOV_PCT": [13.3],
        "EFG_PCT": [0.545],
        "TS_PCT": [0.588],
        "USG_PCT": [0.315],
        "PACE": [96.0],
        "PIE": [0.182],
        "WS": [250.0],
    }
)

# Empty DataFrame for cases like no playoff data
MOCK_DF_EMPTY = pd.DataFrame()


# --- Mock PlayerProfileV2 Endpoint ---
class MockPlayerProfileV2:
    def __init__(self, player_id, per_mode36, season_type_all_star):
        self.player_id = player_id
        self.per_mode36 = per_mode36
        self.season_type = season_type_all_star

        # Simulate the structure of nba_api endpoint results
        self.season_totals_regular_season = MagicMock()
        self.career_totals_regular_season = MagicMock()
        self.season_totals_post_season = MagicMock()
        self.career_totals_post_season = MagicMock()

        if player_id == 999999:  # Test Player With No Data
            self.season_totals_regular_season.get_data_frame = MagicMock(
                return_value=MOCK_DF_EMPTY
            )
            self.career_totals_regular_season.get_data_frame = MagicMock(
                return_value=MOCK_DF_EMPTY
            )
            self.season_totals_post_season.get_data_frame = MagicMock(
                return_value=MOCK_DF_EMPTY
            )
            self.career_totals_post_season.get_data_frame = MagicMock(
                return_value=MOCK_DF_EMPTY
            )
            return

        # Regular Season Data
        if self.season_type == "Regular Season":
            if self.per_mode36 == "PerGame":
                self.season_totals_regular_season.get_data_frame = MagicMock(
                    return_value=MOCK_DF_REG_SEASON_PG.copy()
                )
                self.career_totals_regular_season.get_data_frame = MagicMock(
                    return_value=MOCK_DF_REG_CAREER_PG.copy()
                )
            elif self.per_mode36 == "Advanced":
                self.season_totals_regular_season.get_data_frame = MagicMock(
                    return_value=MOCK_DF_REG_SEASON_ADV.copy()
                )
                self.career_totals_regular_season.get_data_frame = MagicMock(
                    return_value=MOCK_DF_REG_CAREER_ADV.copy()
                )
            else:  # Totals, etc. - return empty for simplicity if not explicitly mocked
                self.season_totals_regular_season.get_data_frame = MagicMock(
                    return_value=MOCK_DF_EMPTY
                )
                self.career_totals_regular_season.get_data_frame = MagicMock(
                    return_value=MOCK_DF_EMPTY
                )
            # No playoff data for this mock if type is Regular Season
            self.season_totals_post_season.get_data_frame = MagicMock(
                return_value=MOCK_DF_EMPTY
            )
            self.career_totals_post_season.get_data_frame = MagicMock(
                return_value=MOCK_DF_EMPTY
            )

        # Playoff Data (simplified - returning empty for now, can be expanded)
        elif self.season_type == "Playoffs":
            self.season_totals_regular_season.get_data_frame = MagicMock(
                return_value=MOCK_DF_EMPTY
            )
            self.career_totals_regular_season.get_data_frame = MagicMock(
                return_value=MOCK_DF_EMPTY
            )
            if (
                self.per_mode36 == "PerGame"
            ):  # Example: Mock playoff per game data if needed
                # Use regular season mock data for playoffs for simplicity in this example
                self.season_totals_post_season.get_data_frame = MagicMock(
                    return_value=MOCK_DF_REG_SEASON_PG.copy()
                )
                self.career_totals_post_season.get_data_frame = MagicMock(
                    return_value=MOCK_DF_REG_CAREER_PG.copy()
                )
            elif self.per_mode36 == "Advanced":
                self.season_totals_post_season.get_data_frame = MagicMock(
                    return_value=MOCK_DF_REG_SEASON_ADV.copy()
                )
                self.career_totals_post_season.get_data_frame = MagicMock(
                    return_value=MOCK_DF_REG_CAREER_ADV.copy()
                )
            else:
                self.season_totals_post_season.get_data_frame = MagicMock(
                    return_value=MOCK_DF_EMPTY
                )
                self.career_totals_post_season.get_data_frame = MagicMock(
                    return_value=MOCK_DF_EMPTY
                )
        else:  # All-Star or other types
            self.season_totals_regular_season.get_data_frame = MagicMock(
                return_value=MOCK_DF_EMPTY
            )
            self.career_totals_regular_season.get_data_frame = MagicMock(
                return_value=MOCK_DF_EMPTY
            )
            self.season_totals_post_season.get_data_frame = MagicMock(
                return_value=MOCK_DF_EMPTY
            )
            self.career_totals_post_season.get_data_frame = MagicMock(
                return_value=MOCK_DF_EMPTY
            )


@patch("app.main.players.get_players", return_value=MOCK_NBA_PLAYERS_LIST)
@patch("app.main.playerprofilev2.PlayerProfileV2", MockPlayerProfileV2)
class TestPlayerProfileEndpoints:

    def test_get_player_profile_lebron_regular_basic_advanced(
        self, mock_get_players, mock_ppv2
    ):
        response = client.get("/player/lebron-james?season_type=regular&stats_mode=all")
        assert response.status_code == 200
        data = response.json()

        assert data["player_id"] == 2544
        assert data["player_name"] == "LeBron James"

        # Check historical regular seasons
        assert data["historical_regular_seasons"] is not None
        assert (
            len(data["historical_regular_seasons"]) == 2
        )  # Based on MOCK_DF_REG_SEASON_PG/ADV
        first_season = data["historical_regular_seasons"][0]
        assert first_season["season_id"] == "2021-22"  # Sorted chronologically
        assert first_season["basic_stats"]["pts_per_game"] == 30.3
        assert first_season["advanced_stats"]["ts_pct"] == 0.619

        # Check career regular season
        assert data["career_regular_season"] is not None
        assert data["career_regular_season"]["basic_stats"]["pts_per_game"] == 27.2
        assert data["career_regular_season"]["advanced_stats"]["ts_pct"] == 0.588

        # Check latest season summary
        assert data["latest_season_summary"] is not None
        assert data["latest_season_summary"]["points_per_game"] == 28.9  # From 2022-23
        assert (
            data["latest_season_summary"]["true_shooting_pct"] == 0.583
        )  # From 2022-23 advanced

        # Playoffs should be None as we requested regular
        assert data["historical_playoff_seasons"] is None
        assert data["career_playoffs"] is None
        mock_ppv2.assert_any_call(
            player_id=2544, per_mode36="PerGame", season_type_all_star="Regular Season"
        )
        mock_ppv2.assert_any_call(
            player_id=2544, per_mode36="Advanced", season_type_all_star="Regular Season"
        )

    def test_get_player_profile_lebron_playoffs_all(self, mock_get_players, mock_ppv2):
        response = client.get(
            "/player/lebron-james?season_type=playoffs&stats_mode=all"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["player_id"] == 2544
        # Regular season data should be None
        assert data["historical_regular_seasons"] is None
        assert data["career_regular_season"] is None
        # Playoff data should be populated (using regular season mocks for now)
        assert data["historical_playoff_seasons"] is not None
        assert len(data["historical_playoff_seasons"]) == 2
        assert data["career_playoffs"] is not None
        mock_ppv2.assert_any_call(
            player_id=2544, per_mode36="PerGame", season_type_all_star="Playoffs"
        )
        mock_ppv2.assert_any_call(
            player_id=2544, per_mode36="Advanced", season_type_all_star="Playoffs"
        )

    def test_get_player_profile_player_not_found(self, mock_get_players, mock_ppv2):
        response = client.get("/player/unknown-player")
        assert response.status_code == 404
        assert response.json()["detail"] == "Player not found"

    def test_get_player_profile_player_with_no_data(self, mock_get_players, mock_ppv2):
        # This player ID 999999 is set up in MockPlayerProfileV2 to return empty DataFrames
        response = client.get(
            "/player/test-player-with-no-data?season_type=all&stats_mode=all"
        )
        assert (
            response.status_code == 200
        )  # Should still succeed, but data fields will be None or empty lists
        data = response.json()
        assert data["player_id"] == 999999
        assert data["player_name"] == "Test Player With No Data"
        assert data["latest_season_summary"] is None
        assert data["career_regular_season"] is None
        assert data["career_playoffs"] is None
        assert data["historical_regular_seasons"] is None
        assert data["historical_playoff_seasons"] is None

    def test_compare_players_endpoint(self, mock_get_players, mock_ppv2):
        response = client.get(
            "/compare?player1=lebron-james&player2=stephen-curry&season_type=regular&stats_mode=all"
        )
        assert response.status_code == 200
        data = response.json()
        assert "lebron-james" in data  # Uses slugs as keys
        assert "stephen-curry" in data
        assert data["lebron-james"]["player_id"] == 2544
        assert data["stephen-curry"]["player_id"] == 201939
        assert (
            data["lebron-james"]["career_regular_season"]["basic_stats"]["pts_per_game"]
            is not None
        )

    def test_compare_players_one_not_found(self, mock_get_players, mock_ppv2):
        response = client.get("/compare?player1=lebron-james&player2=unknown-player")
        assert response.status_code == 404
        assert "Player 'unknown-player' not found" in response.json()["detail"]

    def test_lineup_endpoint_basic(self, mock_get_players, mock_ppv2):
        request_body = {"players": ["lebron-james", "stephen-curry"]}
        response = client.post("/lineup?metric=avg", json=request_body)
        assert response.status_code == 200
        data = response.json()
        assert "LeBron James" in data["lineup_players"]
        assert "Stephen Curry" in data["lineup_players"]
        assert data["aggregation_metric"] == "avg"
        # Check a sample aggregated stat (based on PlayerStatsSummary fields from mocks)
        # LeBron 2022-23 PTS: 28.9, Curry (using LeBron's mock for simplicity here) PTS: 28.9
        # Avg should be 28.9
        assert (
            "avg_points_per_game" in data["aggregated_stats_from_latest_season_summary"]
        )
        # Note: MockPlayerProfileV2 returns LeBron's stats for Curry for simplicity, so avg is just LeBron's stats
        assert (
            data["aggregated_stats_from_latest_season_summary"]["avg_points_per_game"]
            == 28.9
        )

    def test_lineup_one_player_not_found(self, mock_get_players, mock_ppv2):
        request_body = {"players": ["lebron-james", "unknown-slug"]}
        response = client.post("/lineup?metric=avg", json=request_body)
        assert response.status_code == 404
        assert "Player 'unknown-slug' not found in lineup" in response.json()["detail"]


# --- Tests for helper functions (can be outside the class if not using TestClient) ---
# These would require importing the specific functions from app.main
# from app.main import _parse_api_row_to_basic_stats, _parse_api_row_to_advanced_stats


def test_parse_basic_stats_helper():
    from app.main import (
        _parse_api_row_to_basic_stats,
    )  # Import here for standalone test

    mock_row = MOCK_DF_REG_SEASON_PG.iloc[0]
    basic_model = _parse_api_row_to_basic_stats(mock_row)
    assert basic_model.gp == 55
    assert basic_model.pts_per_game == 28.9
    assert basic_model.fg_pct == 0.500


def test_parse_advanced_stats_helper():
    from app.main import _parse_api_row_to_advanced_stats  # Import here

    mock_row = MOCK_DF_REG_SEASON_ADV.iloc[0]
    adv_model = _parse_api_row_to_advanced_stats(mock_row)
    assert adv_model.usg_pct == 0.320
    assert adv_model.ts_pct == 0.583
    assert adv_model.ws == 5.6
