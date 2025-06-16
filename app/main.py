from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from nba_api.stats.endpoints import playerprofilev2 # Changed from playercareerstats
from nba_api.stats.static import players
from functools import lru_cache
from typing import Union, List, Optional, Dict
from app.db import init_db, log_usage # Assuming db.py is compatible
from contextlib import asynccontextmanager
import pandas as pd

# --- Pydantic Models ---

class BasicStatsModel(BaseModel):
    gp: Optional[int] = Field(None, description="Games Played")
    gs: Optional[int] = Field(None, description="Games Started")
    min_per_game: Optional[float] = Field(None, description="Minutes Per Game")
    pts_per_game: Optional[float] = Field(None, description="Points Per Game")
    fgm_per_game: Optional[float] = Field(None, description="Field Goals Made Per Game")
    fga_per_game: Optional[float] = Field(None, description="Field Goals Attempted Per Game")
    fg_pct: Optional[float] = Field(None, description="Field Goal Percentage")
    fg3m_per_game: Optional[float] = Field(None, description="3-Point Field Goals Made Per Game")
    fg3a_per_game: Optional[float] = Field(None, description="3-Point Field Goals Attempted Per Game")
    fg3_pct: Optional[float] = Field(None, description="3-Point Field Goal Percentage")
    ftm_per_game: Optional[float] = Field(None, description="Free Throws Made Per Game")
    fta_per_game: Optional[float] = Field(None, description="Free Throws Attempted Per Game")
    ft_pct: Optional[float] = Field(None, description="Free Throw Percentage")
    oreb_per_game: Optional[float] = Field(None, description="Offensive Rebounds Per Game")
    dreb_per_game: Optional[float] = Field(None, description="Defensive Rebounds Per Game")
    reb_per_game: Optional[float] = Field(None, description="Total Rebounds Per Game")
    ast_per_game: Optional[float] = Field(None, description="Assists Per Game")
    tov_per_game: Optional[float] = Field(None, description="Turnovers Per Game")
    stl_per_game: Optional[float] = Field(None, description="Steals Per Game")
    blk_per_game: Optional[float] = Field(None, description="Blocks Per Game")
    pf_per_game: Optional[float] = Field(None, description="Personal Fouls Per Game")

class AdvancedStatsModel(BaseModel):
    off_rating: Optional[float] = Field(None, description="Offensive Rating")
    def_rating: Optional[float] = Field(None, description="Defensive Rating")
    net_rating: Optional[float] = Field(None, description="Net Rating")
    ast_pct: Optional[float] = Field(None, description="Assist Percentage")
    ast_to_val: Optional[float] = Field(None, description="Assist to Turnover Ratio (AST/TOV)") # Renamed from ast_tov
    ast_ratio: Optional[float] = Field(None, description="Assist Ratio")
    oreb_pct: Optional[float] = Field(None, description="Offensive Rebound Percentage")
    dreb_pct: Optional[float] = Field(None, description="Defensive Rebound Percentage")
    reb_pct: Optional[float] = Field(None, description="Rebound Percentage")
    tm_tov_pct: Optional[float] = Field(None, description="Team Turnover Percentage (Possession ending in TOV)")
    efg_pct: Optional[float] = Field(None, description="Effective Field Goal Percentage")
    ts_pct: Optional[float] = Field(None, description="True Shooting Percentage")
    usg_pct: Optional[float] = Field(None, description="Usage Percentage")
    pace: Optional[float] = Field(None, description="Pace")
    pie: Optional[float] = Field(None, description="Player Impact Estimate")
    ws: Optional[float] = Field(None, description="Win Shares")
    # Other advanced stats can be added if available from PlayerProfileV2's 'Advanced' PerMode
    # e_off_rating, e_def_rating, e_net_rating, e_pace, e_usg_pct might be available

class SeasonStats(BaseModel):
    season_id: str = Field(..., description="Season identifier (e.g., '2022-23')")
    team_abbreviation: str = Field(..., description="Team abbreviation during that season")
    player_age: Optional[int] = Field(None, description="Player's age during that season")
    basic_stats: Optional[BasicStatsModel] = None
    advanced_stats: Optional[AdvancedStatsModel] = None

class CareerStats(BaseModel):
    # For career, stats are usually totals or averages across the career
    # The PerMode from nba_api will dictate if these are per-game or totals that we need to average.
    # For simplicity, let's assume we will store PerGame basic and Advanced summary stats for career.
    basic_stats: Optional[BasicStatsModel] = None
    advanced_stats: Optional[AdvancedStatsModel] = None

class PlayerStatsSummary(BaseModel): # This was the old PlayerStats model
    points_per_game: Optional[float] = None
    true_shooting_pct: Optional[float] = None
    rebounds_per_game: Optional[float] = None
    assists_per_game: Optional[float] = None
    steals_per_game: Optional[float] = None
    blocks_per_game: Optional[float] = None
    turnovers_per_game: Optional[float] = None
    fg_pct: Optional[float] = None
    fg3_pct: Optional[float] = None
    ft_pct: Optional[float] = None
    minutes_per_game: Optional[float] = None
    usage_rate: Optional[Union[str, float]] = None # Align with usg_pct from AdvancedStatsModel
    team: Optional[str] = None

class PlayerProfileResponse(BaseModel):
    player_id: int
    player_name: str
    latest_season_summary: Optional[PlayerStatsSummary] = Field(None, description="Summary stats for the player's most recent regular season.")
    career_regular_season: Optional[CareerStats] = None
    career_playoffs: Optional[CareerStats] = None
    historical_regular_seasons: Optional[List[SeasonStats]] = None
    historical_playoff_seasons: Optional[List[SeasonStats]] = None

# --- FastAPI Lifespan & App Initialization ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(lifespan=lifespan)

# --- Helper Functions ---

def safe_float(value, precision=None):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    try:
        val = float(value)
        return round(val, precision) if precision is not None else val
    except (ValueError, TypeError):
        return None

def _parse_api_row_to_basic_stats(row: pd.Series) -> BasicStatsModel:
    # Assumes row comes from a 'PerGame' API call
    return BasicStatsModel(
        gp=row.get('GP'),
        gs=row.get('GS'),
        min_per_game=safe_float(row.get('MIN'), 1),
        pts_per_game=safe_float(row.get('PTS'), 1),
        fgm_per_game=safe_float(row.get('FGM'), 1),
        fga_per_game=safe_float(row.get('FGA'), 1),
        fg_pct=safe_float(row.get('FG_PCT'), 3),
        fg3m_per_game=safe_float(row.get('FG3M'), 1),
        fg3a_per_game=safe_float(row.get('FG3A'), 1),
        fg3_pct=safe_float(row.get('FG3_PCT'), 3),
        ftm_per_game=safe_float(row.get('FTM'), 1),
        fta_per_game=safe_float(row.get('FTA'), 1),
        ft_pct=safe_float(row.get('FT_PCT'), 3),
        oreb_per_game=safe_float(row.get('OREB'), 1),
        dreb_per_game=safe_float(row.get('DREB'), 1),
        reb_per_game=safe_float(row.get('REB'), 1),
        ast_per_game=safe_float(row.get('AST'), 1),
        tov_per_game=safe_float(row.get('TOV'), 1), # API uses TOV, not TO
        stl_per_game=safe_float(row.get('STL'), 1),
        blk_per_game=safe_float(row.get('BLK'), 1),
        pf_per_game=safe_float(row.get('PF'), 1)
    )

def _parse_api_row_to_advanced_stats(row: pd.Series) -> AdvancedStatsModel:
    # Assumes row comes from an 'Advanced' API call
    return AdvancedStatsModel(
        off_rating=safe_float(row.get('OFF_RATING'), 1),
        def_rating=safe_float(row.get('DEF_RATING'), 1),
        net_rating=safe_float(row.get('NET_RATING'), 1),
        ast_pct=safe_float(row.get('AST_PCT'), 3),
        ast_to_val=safe_float(row.get('AST_TO'), 1), # AST_TO in nba_api
        ast_ratio=safe_float(row.get('AST_RATIO'), 1),
        oreb_pct=safe_float(row.get('OREB_PCT'), 3),
        dreb_pct=safe_float(row.get('DREB_PCT'), 3),
        reb_pct=safe_float(row.get('REB_PCT'), 3),
        tm_tov_pct=safe_float(row.get('TM_TOV_PCT'), 3), # Or FTM_TOV_PCT from API? Check nba_api docs for exact name. Assuming TM_TOV_PCT
        efg_pct=safe_float(row.get('EFG_PCT'), 3),
        ts_pct=safe_float(row.get('TS_PCT'), 3),
        usg_pct=safe_float(row.get('USG_PCT'), 3),
        pace=safe_float(row.get('PACE'), 1),
        pie=safe_float(row.get('PIE'), 3),
        ws=safe_float(row.get('WS'), 1)
    )

@lru_cache(maxsize=32) # Cache player ID to name mapping
def get_player_name_from_id(player_id: int) -> str:
    player_list = players.get_players()
    for player in player_list:
        if player["id"] == player_id:
            return player["full_name"]
    return "Unknown Player"

@lru_cache(maxsize=128)
def get_player_id(name: str) -> Optional[int]:
    player_list = players.get_players()
    name_lower = name.lower().replace("-", " ")
    for player in player_list:
        if player["full_name"].lower() == name_lower:
            return player["id"]
    return None

# Main data fetching logic
@lru_cache(maxsize=64) # Cache based on player_id and requested data types
def get_player_data_from_nba_api(player_id: int, fetch_regular_season: bool, fetch_playoffs: bool, fetch_basic: bool, fetch_advanced: bool):

    api_data_cache = {} # Store DataFrames from API calls to avoid redundant calls for the same player_id

    def fetch_profile_data(per_mode, season_type):
        cache_key = (player_id, per_mode, season_type)
        if cache_key in api_data_cache:
            return api_data_cache[cache_key]

        try:
            profile = playerprofilev2.PlayerProfileV2(player_id=player_id, per_mode36=per_mode, season_type_all_star=season_type)
            api_data_cache[cache_key] = profile
            return profile
        except Exception as e:
            # Log error or handle as needed
            print(f"Error fetching PlayerProfileV2 for {player_id}, {per_mode}, {season_type}: {e}")
            api_data_cache[cache_key] = None # Cache failure to avoid retries for this specific call combination
            return None

    historical_regular_seasons_list = []
    career_regular_season_stats = CareerStats()
    if fetch_regular_season:
        # Basic Regular Season Stats (Seasons & Career)
        if fetch_basic:
            profile_reg_pg = fetch_profile_data("PerGame", "Regular Season")
            if profile_reg_pg:
                df_reg_pg_seasons = profile_reg_pg.season_totals_regular_season.get_data_frame()
                df_reg_pg_career = profile_reg_pg.career_totals_regular_season.get_data_frame()

                # Populate basic career stats
                if not df_reg_pg_career.empty:
                    career_regular_season_stats.basic_stats = _parse_api_row_to_basic_stats(df_reg_pg_career.iloc[0])

                # Temp dict to hold season data before merging advanced
                temp_season_data_basic = {row['SEASON_ID']: {"basic": _parse_api_row_to_basic_stats(row), "meta": row} for _, row in df_reg_pg_seasons.iterrows()}

        # Advanced Regular Season Stats (Seasons & Career)
        if fetch_advanced:
            profile_reg_adv = fetch_profile_data("Advanced", "Regular Season")
            if profile_reg_adv:
                df_reg_adv_seasons = profile_reg_adv.season_totals_regular_season.get_data_frame()
                df_reg_adv_career = profile_reg_adv.career_totals_regular_season.get_data_frame()

                if not df_reg_adv_career.empty:
                    career_regular_season_stats.advanced_stats = _parse_api_row_to_advanced_stats(df_reg_adv_career.iloc[0])

                # Temp dict to hold season data before merging basic
                temp_season_data_adv = {row['SEASON_ID']: {"advanced": _parse_api_row_to_advanced_stats(row), "meta": row} for _, row in df_reg_adv_seasons.iterrows()}

        # Combine basic and advanced for historical regular seasons
        # Use all season IDs from both basic and advanced fetching attempts
        all_season_ids = set()
        if fetch_basic and 'temp_season_data_basic' in locals(): all_season_ids.update(temp_season_data_basic.keys())
        if fetch_advanced and 'temp_season_data_adv' in locals(): all_season_ids.update(temp_season_data_adv.keys())

        for season_id in sorted(list(all_season_ids)): # Process in chronological order
            basic_s, adv_s, meta_s = None, None, None
            if fetch_basic and 'temp_season_data_basic' in locals() and season_id in temp_season_data_basic:
                basic_s = temp_season_data_basic[season_id]["basic"]
                meta_s = temp_season_data_basic[season_id]["meta"]
            if fetch_advanced and 'temp_season_data_adv' in locals() and season_id in temp_season_data_adv:
                adv_s = temp_season_data_adv[season_id]["advanced"]
                if not meta_s: meta_s = temp_season_data_adv[season_id]["meta"] # Fallback if only advanced was fetched

            if meta_s is not None: # Ensure we have at least some data for the season
                 historical_regular_seasons_list.append(SeasonStats(
                    season_id=season_id,
                    team_abbreviation=meta_s.get('TEAM_ABBREVIATION', 'N/A'),
                    player_age=meta_s.get('PLAYER_AGE'),
                    basic_stats=basic_s,
                    advanced_stats=adv_s
                ))

    historical_playoff_seasons_list = []
    career_playoff_stats = CareerStats()
    if fetch_playoffs:
        # Basic Playoff Stats
        if fetch_basic:
            profile_pst_pg = fetch_profile_data("PerGame", "Playoffs")
            if profile_pst_pg:
                df_pst_pg_seasons = profile_pst_pg.season_totals_post_season.get_data_frame()
                df_pst_pg_career = profile_pst_pg.career_totals_post_season.get_data_frame()
                if not df_pst_pg_career.empty:
                    career_playoff_stats.basic_stats = _parse_api_row_to_basic_stats(df_pst_pg_career.iloc[0])
                temp_season_data_basic_pst = {row['SEASON_ID']: {"basic": _parse_api_row_to_basic_stats(row), "meta": row} for _, row in df_pst_pg_seasons.iterrows()}

        # Advanced Playoff Stats
        if fetch_advanced:
            profile_pst_adv = fetch_profile_data("Advanced", "Playoffs")
            if profile_pst_adv:
                df_pst_adv_seasons = profile_pst_adv.season_totals_post_season.get_data_frame()
                df_pst_adv_career = profile_pst_adv.career_totals_post_season.get_data_frame()
                if not df_pst_adv_career.empty:
                    career_playoff_stats.advanced_stats = _parse_api_row_to_advanced_stats(df_pst_adv_career.iloc[0])
                temp_season_data_adv_pst = {row['SEASON_ID']: {"advanced": _parse_api_row_to_advanced_stats(row), "meta": row} for _, row in df_pst_adv_seasons.iterrows()}

        all_playoff_season_ids = set()
        if fetch_basic and 'temp_season_data_basic_pst' in locals(): all_playoff_season_ids.update(temp_season_data_basic_pst.keys())
        if fetch_advanced and 'temp_season_data_adv_pst' in locals(): all_playoff_season_ids.update(temp_season_data_adv_pst.keys())

        for season_id in sorted(list(all_playoff_season_ids)):
            basic_s, adv_s, meta_s = None, None, None
            if fetch_basic and 'temp_season_data_basic_pst' in locals() and season_id in temp_season_data_basic_pst:
                basic_s = temp_season_data_basic_pst[season_id]["basic"]
                meta_s = temp_season_data_basic_pst[season_id]["meta"]
            if fetch_advanced and 'temp_season_data_adv_pst' in locals() and season_id in temp_season_data_adv_pst:
                adv_s = temp_season_data_adv_pst[season_id]["advanced"]
                if not meta_s: meta_s = temp_season_data_adv_pst[season_id]["meta"]

            if meta_s is not None:
                historical_playoff_seasons_list.append(SeasonStats(
                    season_id=season_id,
                    team_abbreviation=meta_s.get('TEAM_ABBREVIATION', 'N/A'),
                    player_age=meta_s.get('PLAYER_AGE'),
                    basic_stats=basic_s,
                    advanced_stats=adv_s
                ))

    return {
        "historical_regular_seasons": historical_regular_seasons_list if historical_regular_seasons_list else None,
        "career_regular_season": career_regular_season_stats if career_regular_season_stats.basic_stats or career_regular_season_stats.advanced_stats else None,
        "historical_playoff_seasons": historical_playoff_seasons_list if historical_playoff_seasons_list else None,
        "career_playoffs": career_playoff_stats if career_playoff_stats.basic_stats or career_playoff_stats.advanced_stats else None,
    }


@app.get("/player/{name}", response_model=PlayerProfileResponse) # Changed response_model
def get_player_profile(
    name: str,
    season_type: str = Query("all", description="Type of season data: 'regular', 'playoffs', 'all'"),
    # season: str = Query("all", description="Specific season (e.g., '2022-23') or 'all', 'career' - Not fully implemented yet, defaults to all seasons/career"),
    stats_mode: str = Query("all", description="Type of stats: 'basic', 'advanced', 'all'")
):
    log_usage(endpoint="/player", payload=f"{name}?season_type={season_type}&stats_mode={stats_mode}") # Add params to log

    player_id = get_player_id(name)
    if not player_id:
        raise HTTPException(status_code=404, detail="Player not found")

    player_name_str = get_player_name_from_id(player_id)

    fetch_regular = "regular" in season_type.lower() or "all" in season_type.lower()
    fetch_playoffs = "playoffs" in season_type.lower() or "all" in season_type.lower()
    fetch_basic_stats = "basic" in stats_mode.lower() or "all" in stats_mode.lower()
    fetch_advanced_stats = "advanced" in stats_mode.lower() or "all" in stats_mode.lower()

    if not (fetch_regular or fetch_playoffs):
        raise HTTPException(status_code=400, detail="Invalid season_type. Must be 'regular', 'playoffs', or 'all'.")
    if not (fetch_basic_stats or fetch_advanced_stats):
        raise HTTPException(status_code=400, detail="Invalid stats_mode. Must be 'basic', 'advanced', or 'all'.")

    try:
        data = get_player_data_from_nba_api(player_id, fetch_regular, fetch_playoffs, fetch_basic_stats, fetch_advanced_stats)
    except ValueError as e: # More specific error handling from fetching/parsing if needed
        # This generic ValueError might come from nba_api itself if data is bad
        raise HTTPException(status_code=500, detail=f"Player data issue: {e}")
    except Exception as e:
        # Log this exception for debugging
        print(f"Unhandled exception in get_player_data_from_nba_api: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving or processing player data.")


    # Create the summary for latest_season_summary
    latest_season_summary_obj = None
    if data["historical_regular_seasons"] and data["historical_regular_seasons"][-1].basic_stats:
        latest_reg_season = data["historical_regular_seasons"][-1] # Assumes sorted

        # Try to get advanced stats for summary if available
        ts_pct_summary = None
        usg_pct_summary = None
        if latest_reg_season.advanced_stats:
            ts_pct_summary = latest_reg_season.advanced_stats.ts_pct
            usg_pct_summary = latest_reg_season.advanced_stats.usg_pct

        latest_season_summary_obj = PlayerStatsSummary(
            points_per_game=latest_reg_season.basic_stats.pts_per_game,
            true_shooting_pct=ts_pct_summary,
            rebounds_per_game=latest_reg_season.basic_stats.reb_per_game,
            assists_per_game=latest_reg_season.basic_stats.ast_per_game,
            steals_per_game=latest_reg_season.basic_stats.stl_per_game,
            blocks_per_game=latest_reg_season.basic_stats.blk_per_game,
            turnovers_per_game=latest_reg_season.basic_stats.tov_per_game,
            fg_pct=latest_reg_season.basic_stats.fg_pct,
            fg3_pct=latest_reg_season.basic_stats.fg3_pct,
            ft_pct=latest_reg_season.basic_stats.ft_pct,
            minutes_per_game=latest_reg_season.basic_stats.min_per_game,
            usage_rate=usg_pct_summary, # From advanced if available
            team=latest_reg_season.team_abbreviation
        )

    return PlayerProfileResponse(
        player_id=player_id,
        player_name=player_name_str,
        latest_season_summary=latest_season_summary_obj,
        career_regular_season=data["career_regular_season"],
        career_playoffs=data["career_playoffs"],
        historical_regular_seasons=data["historical_regular_seasons"],
        historical_playoff_seasons=data["historical_playoff_seasons"]
    )

# --- Other Endpoints (Compare, Lineup) ---
# These will need to be updated to use the new data structures and fetching logic.
# For now, they might be broken or return data in the old format.
# This subtask primarily focuses on the /player/{name} endpoint.

@app.get("/compare", response_model=Dict[str, PlayerProfileResponse]) # Return type changed
def compare_players(
    player1_name: str = Query(..., alias="player1"),
    player2_name: str = Query(..., alias="player2"),
    season_type: str = Query("regular", description="Type of season data: 'regular', 'playoffs', 'all'"),
    stats_mode: str = Query("all", description="Type of stats: 'basic', 'advanced', 'all'")
):
    log_usage(endpoint="/compare", payload=f"{player1_name} vs {player2_name} (season: {season_type}, mode: {stats_mode})")

    p1_id = get_player_id(player1_name)
    p2_id = get_player_id(player2_name)

    if not p1_id:
        raise HTTPException(status_code=404, detail=f"Player '{player1_name}' not found")
    if not p2_id:
        raise HTTPException(status_code=404, detail=f"Player '{player2_name}' not found")

    fetch_regular = "regular" in season_type.lower() or "all" in season_type.lower()
    fetch_playoffs = "playoffs" in season_type.lower() or "all" in season_type.lower()
    fetch_basic = "basic" in stats_mode.lower() or "all" in stats_mode.lower()
    fetch_advanced = "advanced" in stats_mode.lower() or "all" in stats_mode.lower()

    if not (fetch_regular or fetch_playoffs):
        raise HTTPException(status_code=400, detail="Invalid season_type for comparison. Must be 'regular', 'playoffs', or 'all'.")
    if not (fetch_basic or fetch_advanced):
        raise HTTPException(status_code=400, detail="Invalid stats_mode for comparison. Must be 'basic', 'advanced', or 'all'.")

    try:
        p1_data_fetched = get_player_data_from_nba_api(p1_id, fetch_regular, fetch_playoffs, fetch_basic, fetch_advanced)
        p2_data_fetched = get_player_data_from_nba_api(p2_id, fetch_regular, fetch_playoffs, fetch_basic, fetch_advanced)
    except Exception as e:
        # Log this exception
        print(f"Exception during data fetching for compare: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving data for comparison: {e}")

    p1_profile_name = get_player_name_from_id(p1_id)
    p2_profile_name = get_player_name_from_id(p2_id)

    # Construct PlayerProfileResponse for player 1
    p1_latest_summary = None
    if p1_data_fetched["historical_regular_seasons"] and p1_data_fetched["historical_regular_seasons"][-1].basic_stats:
        latest_p1_reg = p1_data_fetched["historical_regular_seasons"][-1]
        p1_ts, p1_usg = (latest_p1_reg.advanced_stats.ts_pct, latest_p1_reg.advanced_stats.usg_pct) if latest_p1_reg.advanced_stats else (None, None)
        p1_latest_summary = PlayerStatsSummary(
            points_per_game=latest_p1_reg.basic_stats.pts_per_game, true_shooting_pct=p1_ts,
            rebounds_per_game=latest_p1_reg.basic_stats.reb_per_game, assists_per_game=latest_p1_reg.basic_stats.ast_per_game,
            steals_per_game=latest_p1_reg.basic_stats.stl_per_game, blocks_per_game=latest_p1_reg.basic_stats.blk_per_game,
            turnovers_per_game=latest_p1_reg.basic_stats.tov_per_game, fg_pct=latest_p1_reg.basic_stats.fg_pct,
            fg3_pct=latest_p1_reg.basic_stats.fg3_pct, ft_pct=latest_p1_reg.basic_stats.ft_pct,
            minutes_per_game=latest_p1_reg.basic_stats.min_per_game, usage_rate=p1_usg, team=latest_p1_reg.team_abbreviation
        )
    p1_response = PlayerProfileResponse(
        player_id=p1_id, player_name=p1_profile_name, latest_season_summary=p1_latest_summary,
        career_regular_season=p1_data_fetched["career_regular_season"], career_playoffs=p1_data_fetched["career_playoffs"],
        historical_regular_seasons=p1_data_fetched["historical_regular_seasons"], historical_playoff_seasons=p1_data_fetched["historical_playoff_seasons"]
    )

    # Construct PlayerProfileResponse for player 2
    p2_latest_summary = None
    if p2_data_fetched["historical_regular_seasons"] and p2_data_fetched["historical_regular_seasons"][-1].basic_stats:
        latest_p2_reg = p2_data_fetched["historical_regular_seasons"][-1]
        p2_ts, p2_usg = (latest_p2_reg.advanced_stats.ts_pct, latest_p2_reg.advanced_stats.usg_pct) if latest_p2_reg.advanced_stats else (None, None)
        p2_latest_summary = PlayerStatsSummary(
            points_per_game=latest_p2_reg.basic_stats.pts_per_game, true_shooting_pct=p2_ts,
            rebounds_per_game=latest_p2_reg.basic_stats.reb_per_game, assists_per_game=latest_p2_reg.basic_stats.ast_per_game,
            steals_per_game=latest_p2_reg.basic_stats.stl_per_game, blocks_per_game=latest_p2_reg.basic_stats.blk_per_game,
            turnovers_per_game=latest_p2_reg.basic_stats.tov_per_game, fg_pct=latest_p2_reg.basic_stats.fg_pct,
            fg3_pct=latest_p2_reg.basic_stats.fg3_pct, ft_pct=latest_p2_reg.basic_stats.ft_pct,
            minutes_per_game=latest_p2_reg.basic_stats.min_per_game, usage_rate=p2_usg, team=latest_p2_reg.team_abbreviation
        )
    p2_response = PlayerProfileResponse(
        player_id=p2_id, player_name=p2_profile_name, latest_season_summary=p2_latest_summary,
        career_regular_season=p2_data_fetched["career_regular_season"], career_playoffs=p2_data_fetched["career_playoffs"],
        historical_regular_seasons=p2_data_fetched["historical_regular_seasons"], historical_playoff_seasons=p2_data_fetched["historical_playoff_seasons"]
    )

    return {player1_name: p1_response, player2_name: p2_response}


class LineupRequest(BaseModel):
    players: List[str]
    # Potentially add season_type, season, stats_mode for lineup granularity

@app.post("/lineup")
def get_lineup_stats(
    request: LineupRequest, # LineupRequest model is simple: {"players": ["name1", "name2"]}
    metric: str = Query("avg", pattern="^(avg|total)$"),
    # stats_fields_query: Optional[str] = Query(None, alias="stats", description="Comma-separated specific PlayerStatsSummary fields to aggregate (e.g., points_per_game,rebounds_per_game). Default all numeric fields.")
    # For simplicity, this version will aggregate all numeric fields from PlayerStatsSummary.
    # Adding specific field selection can be a future enhancement.
):
    log_usage(endpoint="/lineup", payload=f"Players: {request.players}, Metric: {metric}")

    player_summaries_for_aggregation = []
    lineup_player_names = []

    for player_slug in request.players:
        player_id = get_player_id(player_slug)
        if not player_id:
            raise HTTPException(status_code=404, detail=f"Player '{player_slug}' not found in lineup.")

        player_name = get_player_name_from_id(player_id)
        lineup_player_names.append(player_name)

        try:
            # Fetch only latest regular season, basic + advanced for summary
            data = get_player_data_from_nba_api(player_id, fetch_regular_season=True, fetch_playoffs=False, fetch_basic=True, fetch_advanced=True)
        except Exception as e:
            # Log this exception
            print(f"Exception during data fetching for lineup player {player_slug}: {e}")
            raise HTTPException(status_code=500, detail=f"Error retrieving data for player {player_slug} in lineup.")

        current_player_summary = None
        if data["historical_regular_seasons"] and data["historical_regular_seasons"][-1].basic_stats:
            latest_reg_season = data["historical_regular_seasons"][-1]
            ts_pct, usg_rate = (None,None)
            if latest_reg_season.advanced_stats:
                ts_pct = latest_reg_season.advanced_stats.ts_pct
                usg_rate = latest_reg_season.advanced_stats.usg_pct

            current_player_summary = PlayerStatsSummary(
                points_per_game=latest_reg_season.basic_stats.pts_per_game,
                true_shooting_pct=ts_pct,
                rebounds_per_game=latest_reg_season.basic_stats.reb_per_game,
                assists_per_game=latest_reg_season.basic_stats.ast_per_game,
                steals_per_game=latest_reg_season.basic_stats.stl_per_game,
                blocks_per_game=latest_reg_season.basic_stats.blk_per_game,
                turnovers_per_game=latest_reg_season.basic_stats.tov_per_game,
                fg_pct=latest_reg_season.basic_stats.fg_pct,
                fg3_pct=latest_reg_season.basic_stats.fg3_pct,
                ft_pct=latest_reg_season.basic_stats.ft_pct,
                minutes_per_game=latest_reg_season.basic_stats.min_per_game,
                usage_rate=usg_rate, # From advanced if available
                team=latest_reg_season.team_abbreviation # Team here is from latest season, might not be relevant for "lineup"
            )
            player_summaries_for_aggregation.append(current_player_summary.model_dump(exclude_none=True))
        else:
            # If a player has no stats, we can skip them or raise error.
            # For now, skip them for aggregation but still list their name.
            # Or, add an empty dict to handle it in aggregation loop.
            player_summaries_for_aggregation.append({})


    if not player_summaries_for_aggregation: # Should not happen if names are valid and players are found
        raise HTTPException(status_code=500, detail="Could not retrieve any summary stats for the lineup players.")

    aggregated_stats = {}
    # Determine numeric fields from PlayerStatsSummary for aggregation
    # This is safer than using the first player's fields if some are None
    numeric_fields = [
        f.name for f in PlayerStatsSummary.model_fields.values()
        if f.annotation in [Optional[float], Optional[int], float, int] and f.name != "team" # Exclude non-numeric like team
    ]
    # Also, usage_rate can be Union[str, float], explicitly handle if it's float for aggregation
    # For now, relying on model_dump(exclude_none=True) and checking type later.

    for field in numeric_fields:
        values = []
        for p_summary_dict in player_summaries_for_aggregation:
            val = p_summary_dict.get(field)
            if isinstance(val, (int, float)): # Ensure it's numeric
                values.append(val)

        if not values: continue

        if metric == "avg":
            aggregated_stats[f"avg_{field}"] = round(sum(values) / len(values), 2)
        else: # total
            aggregated_stats[f"total_{field}"] = round(sum(values), 2)

    return {
        "lineup_players": lineup_player_names,
        "aggregation_metric": metric,
        "aggregated_stats_from_latest_season_summary": aggregated_stats,
        "note": "Lineup stats are aggregated from each player's latest regular season summary."
    }
