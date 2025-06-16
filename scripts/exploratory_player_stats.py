import pandas
from nba_api.stats.static import players
from nba_api.stats.endpoints import playerprofilev2

# Ensure player_id is correctly fetched
player_name = "LeBron James"
player_info_list = players.find_players_by_full_name(player_name)
if not player_info_list:
    print(f"Player {player_name} not found.")
    exit()
player_id = player_info_list[0]["id"]
print(f"Player ID for {player_name}: {player_id}\n")

# Fetch Regular Season - PerGame stats from PlayerProfileV2
print("--- PlayerProfileV2: Regular Season (PerGame) ---")
try:
    profile_reg_pg = playerprofilev2.PlayerProfileV2(
        player_id=player_id, per_mode36="PerGame", season_type_all_star="Regular Season"
    )
    df_reg_pg_seasons = profile_reg_pg.season_totals_regular_season.get_data_frame()
    if not df_reg_pg_seasons.empty:
        print("Sample rows (Regular Season, PerGame):")
        print(
            df_reg_pg_seasons[
                [
                    "SEASON_ID",
                    "TEAM_ABBREVIATION",
                    "GP",
                    "MIN",
                    "PTS",
                    "REB",
                    "AST",
                    "STL",
                    "BLK",
                    "FG_PCT",
                    "FG3_PCT",
                    "FT_PCT",
                ]
            ].head(2)
        )
        print("\nColumns available (Regular Season, PerGame):")
        print(df_reg_pg_seasons.columns.tolist())
    else:
        print("No regular season per game data found.")
except Exception as e:
    print(f"Error fetching PlayerProfileV2 Regular Season PerGame: {e}")

# Fetch Playoff - PerGame stats from PlayerProfileV2
print("\n--- PlayerProfileV2: Playoffs (PerGame) ---")
try:
    profile_post_pg = playerprofilev2.PlayerProfileV2(
        player_id=player_id, per_mode36="PerGame", season_type_all_star="Playoffs"
    )
    df_post_pg_seasons = profile_post_pg.season_totals_post_season.get_data_frame()
    if not df_post_pg_seasons.empty:
        print("Sample rows (Playoffs, PerGame):")
        print(
            df_post_pg_seasons[
                [
                    "SEASON_ID",
                    "TEAM_ABBREVIATION",
                    "GP",
                    "MIN",
                    "PTS",
                    "REB",
                    "AST",
                    "STL",
                    "BLK",
                    "FG_PCT",
                    "FG3_PCT",
                    "FT_PCT",
                ]
            ].head(2)
        )
        print("\nColumns available (Playoffs, PerGame):")
        print(df_post_pg_seasons.columns.tolist())
    else:
        print("No playoff per game data found.")
except Exception as e:
    print(f"Error fetching PlayerProfileV2 Playoffs PerGame: {e}")

# Fetch Regular Season - Advanced stats from PlayerProfileV2
print("\n--- PlayerProfileV2: Regular Season (Advanced) ---")
try:
    profile_reg_adv = playerprofilev2.PlayerProfileV2(
        player_id=player_id,
        per_mode36="Advanced",
        season_type_all_star="Regular Season",
    )
    df_reg_adv_seasons = profile_reg_adv.season_totals_regular_season.get_data_frame()
    if not df_reg_adv_seasons.empty:
        print("Sample rows (Regular Season, Advanced):")
        # Selecting a subset of potentially available advanced stats
        adv_cols_to_show = [
            "SEASON_ID",
            "TEAM_ABBREVIATION",
            "GP",
            "MIN",
            "OFF_RATING",
            "DEF_RATING",
            "NET_RATING",
            "AST_PCT",
            "AST_TOV",
            "AST_RATIO",
            "OREB_PCT",
            "DREB_PCT",
            "REB_PCT",
            "TM_TOV_PCT",
            "EFG_PCT",
            "TS_PCT",
            "USG_PCT",
            "PACE",
            "PIE",
            "WS",
        ]
        # Filter to columns that actually exist in the dataframe
        existing_adv_cols = [
            col for col in adv_cols_to_show if col in df_reg_adv_seasons.columns
        ]
        print(df_reg_adv_seasons[existing_adv_cols].head(2))
        print("\nColumns available (Regular Season, Advanced):")
        print(df_reg_adv_seasons.columns.tolist())
    else:
        print("No regular season advanced data found.")
except Exception as e:
    print(f"Error fetching PlayerProfileV2 Regular Season Advanced: {e}")

# Fetch Playoff - Advanced stats from PlayerProfileV2
print("\n--- PlayerProfileV2: Playoffs (Advanced) ---")
try:
    profile_post_adv = playerprofilev2.PlayerProfileV2(
        player_id=player_id, per_mode36="Advanced", season_type_all_star="Playoffs"
    )
    df_post_adv_seasons = profile_post_adv.season_totals_post_season.get_data_frame()
    if not df_post_adv_seasons.empty:
        print("Sample rows (Playoffs, Advanced):")
        adv_cols_to_show = [
            "SEASON_ID",
            "TEAM_ABBREVIATION",
            "GP",
            "MIN",
            "OFF_RATING",
            "DEF_RATING",
            "NET_RATING",
            "AST_PCT",
            "AST_TOV",
            "AST_RATIO",
            "OREB_PCT",
            "DREB_PCT",
            "REB_PCT",
            "TM_TOV_PCT",
            "EFG_PCT",
            "TS_PCT",
            "USG_PCT",
            "PACE",
            "PIE",
            "WS",
        ]
        existing_adv_cols = [
            col for col in adv_cols_to_show if col in df_post_adv_seasons.columns
        ]
        print(df_post_adv_seasons[existing_adv_cols].head(2))
        print("\nColumns available (Playoffs, Advanced):")
        print(df_post_adv_seasons.columns.tolist())
    else:
        print("No playoff advanced data found.")
except Exception as e:
    print(f"Error fetching PlayerProfileV2 Playoffs Advanced: {e}")

# Fetch Career Totals (Regular Season, PerGame) from PlayerProfileV2
print("\n--- PlayerProfileV2: Career Totals Regular Season (PerGame) ---")
try:
    # Reuse profile_reg_pg instance created earlier for Regular Season PerGame
    career_reg_pg = profile_reg_pg.career_totals_regular_season.get_data_frame()
    if not career_reg_pg.empty:
        print(
            career_reg_pg[
                [
                    "PLAYER_ID",
                    "GP",
                    "MIN",
                    "PTS",
                    "REB",
                    "AST",
                    "STL",
                    "BLK",
                    "FG_PCT",
                    "FG3_PCT",
                    "FT_PCT",
                ]
            ].head()
        )
        print("\nColumns available (Career Totals Regular Season, PerGame):")
        print(career_reg_pg.columns.tolist())
    else:
        print("No career totals regular season per game data found.")
except Exception as e:
    print(f"Error fetching PlayerProfileV2 Career Regular Season PerGame: {e}")

# Fetch Career Totals (Playoffs, PerGame) from PlayerProfileV2
print("\n--- PlayerProfileV2: Career Totals Playoffs (PerGame) ---")
try:
    # Reuse profile_post_pg instance created earlier for Playoffs PerGame
    career_post_pg = profile_post_pg.career_totals_post_season.get_data_frame()
    if not career_post_pg.empty:
        print(
            career_post_pg[
                [
                    "PLAYER_ID",
                    "GP",
                    "MIN",
                    "PTS",
                    "REB",
                    "AST",
                    "STL",
                    "BLK",
                    "FG_PCT",
                    "FG3_PCT",
                    "FT_PCT",
                ]
            ].head()
        )
        print("\nColumns available (Career Totals Playoffs, PerGame):")
        print(career_post_pg.columns.tolist())
    else:
        print("No career totals playoff per game data found.")
except Exception as e:
    print(f"Error fetching PlayerProfileV2 Career Playoffs PerGame: {e}")

# Fetch Career Totals (Regular Season, Advanced) from PlayerProfileV2
print("\n--- PlayerProfileV2: Career Totals Regular Season (Advanced) ---")
try:
    # Reuse profile_reg_adv instance created earlier for Regular Season Advanced
    career_reg_adv = profile_reg_adv.career_totals_regular_season.get_data_frame()
    adv_cols_to_show = [
        "PLAYER_ID",
        "GP",
        "MIN",
        "OFF_RATING",
        "DEF_RATING",
        "NET_RATING",
        "AST_PCT",
        "AST_TOV",
        "AST_RATIO",
        "OREB_PCT",
        "DREB_PCT",
        "REB_PCT",
        "TM_TOV_PCT",
        "EFG_PCT",
        "TS_PCT",
        "USG_PCT",
        "PACE",
        "PIE",
        "WS",
    ]
    existing_adv_cols = [
        col for col in adv_cols_to_show if col in career_reg_adv.columns
    ]
    if not career_reg_adv.empty:
        print(career_reg_adv[existing_adv_cols].head())
        print("\nColumns available (Career Totals Regular Season, Advanced):")
        print(career_reg_adv.columns.tolist())
    else:
        print("No career totals regular season advanced data found.")
except Exception as e:
    print(f"Error fetching PlayerProfileV2 Career Regular Season Advanced: {e}")

# Fetch Career Totals (Playoffs, Advanced) from PlayerProfileV2
print("\n--- PlayerProfileV2: Career Totals Playoffs (Advanced) ---")
try:
    # Reuse profile_post_adv instance created earlier for Playoffs Advanced
    career_post_adv = profile_post_adv.career_totals_post_season.get_data_frame()
    if not career_post_adv.empty:
        adv_cols_to_show = [
            "PLAYER_ID",
            "GP",
            "MIN",
            "OFF_RATING",
            "DEF_RATING",
            "NET_RATING",
            "AST_PCT",
            "AST_TOV",
            "AST_RATIO",
            "OREB_PCT",
            "DREB_PCT",
            "REB_PCT",
            "TM_TOV_PCT",
            "EFG_PCT",
            "TS_PCT",
            "USG_PCT",
            "PACE",
            "PIE",
            "WS",
        ]
        existing_adv_cols = [
            col for col in adv_cols_to_show if col in career_post_adv.columns
        ]
        print(career_post_adv[existing_adv_cols].head())
        print("\nColumns available (Career Totals Playoffs, Advanced):")
        print(career_post_adv.columns.tolist())
    else:
        print("No career totals playoff advanced data found.")
except Exception as e:
    print(f"Error fetching PlayerProfileV2 Career Playoffs Advanced: {e}")

print("\nDone with exploration.")
