from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from nba_api.stats.endpoints import playerprofilev2
from nba_api.stats.static import players
from nba_api.stats.static import players as nba_static_players # Added for recommendations
from functools import lru_cache
from typing import Union, List, Optional, Dict
from app.db import init_db, log_usage
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
    ast_to_val: Optional[float] = Field(None, description="Assist to Turnover Ratio (AST/TOV)")
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

class SeasonStats(BaseModel):
    season_id: str = Field(..., description="Season identifier (e.g., '2022-23')")
    team_abbreviation: str = Field(..., description="Team abbreviation during that season")
    player_age: Optional[int] = Field(None, description="Player's age during that season")
    basic_stats: Optional[BasicStatsModel] = None
    advanced_stats: Optional[AdvancedStatsModel] = None

class CareerStats(BaseModel):
    basic_stats: Optional[BasicStatsModel] = None
    advanced_stats: Optional[AdvancedStatsModel] = None

class PlayerStatsSummary(BaseModel):
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
    usage_rate: Optional[Union[str, float]] = None
    team: Optional[str] = None

class PlayerProfileResponse(BaseModel):
    player_id: int
    player_name: str
    latest_season_summary: Optional[PlayerStatsSummary] = Field(None, description="Summary stats for the player's most recent regular season.")
    career_regular_season: Optional[CareerStats] = None
    career_playoffs: Optional[CareerStats] = None
    historical_regular_seasons: Optional[List[SeasonStats]] = None
    historical_playoff_seasons: Optional[List[SeasonStats]] = None

class RecommendationRequest(BaseModel):
    target_categories: List[str] = Field(..., description="List of categories to score players on (e.g., ['PTS', 'REB']).")
    num_recommendations: int = Field(5, gt=0, le=20, description="Number of players to recommend.")
    excluded_player_ids: List[int] = Field([], description="List of player IDs to exclude from recommendations.")

class RecommendedPlayer(BaseModel):
    player_id: int
    full_name: str
    recommendation_score: float
    targeted_category_stats: Dict[str, Optional[float]] = Field(description="Stats for the categories the player was scored on.")
    latest_season_summary_brief: Dict[str, Union[str, float, None]] = Field(description="Brief summary of key stats from latest season.")

class RecommendationResponse(BaseModel):
    recommendations: List[RecommendedPlayer]

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
    return BasicStatsModel(
        gp=row.get('GP'), gs=row.get('GS'), min_per_game=safe_float(row.get('MIN'), 1),
        pts_per_game=safe_float(row.get('PTS'), 1), fgm_per_game=safe_float(row.get('FGM'), 1),
        fga_per_game=safe_float(row.get('FGA'), 1), fg_pct=safe_float(row.get('FG_PCT'), 3),
        fg3m_per_game=safe_float(row.get('FG3M'), 1), fg3a_per_game=safe_float(row.get('FG3A'), 1),
        fg3_pct=safe_float(row.get('FG3_PCT'), 3), ftm_per_game=safe_float(row.get('FTM'), 1),
        fta_per_game=safe_float(row.get('FTA'), 1), ft_pct=safe_float(row.get('FT_PCT'), 3),
        oreb_per_game=safe_float(row.get('OREB'), 1), dreb_per_game=safe_float(row.get('DREB'), 1),
        reb_per_game=safe_float(row.get('REB'), 1), ast_per_game=safe_float(row.get('AST'), 1),
        tov_per_game=safe_float(row.get('TOV'), 1), stl_per_game=safe_float(row.get('STL'), 1),
        blk_per_game=safe_float(row.get('BLK'), 1), pf_per_game=safe_float(row.get('PF'), 1)
    )

def _parse_api_row_to_advanced_stats(row: pd.Series) -> AdvancedStatsModel:
    return AdvancedStatsModel(
        off_rating=safe_float(row.get('OFF_RATING'), 1), def_rating=safe_float(row.get('DEF_RATING'), 1),
        net_rating=safe_float(row.get('NET_RATING'), 1), ast_pct=safe_float(row.get('AST_PCT'), 3),
        ast_to_val=safe_float(row.get('AST_TO'), 1), ast_ratio=safe_float(row.get('AST_RATIO'), 1),
        oreb_pct=safe_float(row.get('OREB_PCT'), 3), dreb_pct=safe_float(row.get('DREB_PCT'), 3),
        reb_pct=safe_float(row.get('REB_PCT'), 3), tm_tov_pct=safe_float(row.get('TM_TOV_PCT'), 3),
        efg_pct=safe_float(row.get('EFG_PCT'), 3), ts_pct=safe_float(row.get('TS_PCT'), 3),
        usg_pct=safe_float(row.get('USG_PCT'), 3), pace=safe_float(row.get('PACE'), 1),
        pie=safe_float(row.get('PIE'), 3), ws=safe_float(row.get('WS'), 1)
    )

@lru_cache(maxsize=32)
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

@lru_cache(maxsize=64)
def get_player_data_from_nba_api(player_id: int, fetch_regular_season: bool, fetch_playoffs: bool, fetch_basic: bool, fetch_advanced: bool):
    api_data_cache = {}
    def fetch_profile_data(per_mode, season_type):
        cache_key = (player_id, per_mode, season_type)
        if cache_key in api_data_cache: return api_data_cache[cache_key]
        try:
            profile = playerprofilev2.PlayerProfileV2(player_id=player_id, per_mode36=per_mode, season_type_all_star=season_type)
            api_data_cache[cache_key] = profile
            return profile
        except Exception as e:
            print(f"Error fetching PlayerProfileV2 for {player_id}, {per_mode}, {season_type}: {e}")
            api_data_cache[cache_key] = None
            return None

    historical_regular_seasons_list, career_regular_season_stats = [], CareerStats()
    if fetch_regular_season:
        temp_season_data_basic, temp_season_data_adv = {}, {}
        if fetch_basic:
            profile_reg_pg = fetch_profile_data("PerGame", "Regular Season")
            if profile_reg_pg:
                df_reg_pg_seasons = profile_reg_pg.season_totals_regular_season.get_data_frame()
                df_reg_pg_career = profile_reg_pg.career_totals_regular_season.get_data_frame()
                if not df_reg_pg_career.empty: career_regular_season_stats.basic_stats = _parse_api_row_to_basic_stats(df_reg_pg_career.iloc[0])
                temp_season_data_basic = {row['SEASON_ID']: {"basic": _parse_api_row_to_basic_stats(row), "meta": row} for _, row in df_reg_pg_seasons.iterrows()}
        if fetch_advanced:
            profile_reg_adv = fetch_profile_data("Advanced", "Regular Season")
            if profile_reg_adv:
                df_reg_adv_seasons = profile_reg_adv.season_totals_regular_season.get_data_frame()
                df_reg_adv_career = profile_reg_adv.career_totals_regular_season.get_data_frame()
                if not df_reg_adv_career.empty: career_regular_season_stats.advanced_stats = _parse_api_row_to_advanced_stats(df_reg_adv_career.iloc[0])
                temp_season_data_adv = {row['SEASON_ID']: {"advanced": _parse_api_row_to_advanced_stats(row), "meta": row} for _, row in df_reg_adv_seasons.iterrows()}

        all_season_ids = set(temp_season_data_basic.keys()) | set(temp_season_data_adv.keys())
        for season_id in sorted(list(all_season_ids)):
            basic_s, adv_s, meta_s = None, None, None
            if season_id in temp_season_data_basic: basic_s, meta_s = temp_season_data_basic[season_id]["basic"], temp_season_data_basic[season_id]["meta"]
            if season_id in temp_season_data_adv: adv_s, meta_s_adv = temp_season_data_adv[season_id]["advanced"], temp_season_data_adv[season_id]["meta"]
            if not meta_s and meta_s_adv: meta_s = meta_s_adv
            if meta_s is not None: historical_regular_seasons_list.append(SeasonStats(season_id=season_id, team_abbreviation=meta_s.get('TEAM_ABBREVIATION', 'N/A'), player_age=meta_s.get('PLAYER_AGE'), basic_stats=basic_s, advanced_stats=adv_s))

    historical_playoff_seasons_list, career_playoff_stats = [], CareerStats()
    if fetch_playoffs:
        temp_season_data_basic_pst, temp_season_data_adv_pst = {}, {}
        if fetch_basic:
            profile_pst_pg = fetch_profile_data("PerGame", "Playoffs")
            if profile_pst_pg:
                df_pst_pg_seasons = profile_pst_pg.season_totals_post_season.get_data_frame()
                df_pst_pg_career = profile_pst_pg.career_totals_post_season.get_data_frame()
                if not df_pst_pg_career.empty: career_playoff_stats.basic_stats = _parse_api_row_to_basic_stats(df_pst_pg_career.iloc[0])
                temp_season_data_basic_pst = {row['SEASON_ID']: {"basic": _parse_api_row_to_basic_stats(row), "meta": row} for _, row in df_pst_pg_seasons.iterrows()}
        if fetch_advanced:
            profile_pst_adv = fetch_profile_data("Advanced", "Playoffs")
            if profile_pst_adv:
                df_pst_adv_seasons = profile_pst_adv.season_totals_post_season.get_data_frame()
                df_pst_adv_career = profile_pst_adv.career_totals_post_season.get_data_frame()
                if not df_pst_adv_career.empty: career_playoff_stats.advanced_stats = _parse_api_row_to_advanced_stats(df_pst_adv_career.iloc[0])
                temp_season_data_adv_pst = {row['SEASON_ID']: {"advanced": _parse_api_row_to_advanced_stats(row), "meta": row} for _, row in df_pst_adv_seasons.iterrows()}

        all_playoff_season_ids = set(temp_season_data_basic_pst.keys()) | set(temp_season_data_adv_pst.keys())
        for season_id in sorted(list(all_playoff_season_ids)):
            basic_s, adv_s, meta_s = None, None, None
            if season_id in temp_season_data_basic_pst: basic_s, meta_s = temp_season_data_basic_pst[season_id]["basic"], temp_season_data_basic_pst[season_id]["meta"]
            if season_id in temp_season_data_adv_pst: adv_s, meta_s_adv = temp_season_data_adv_pst[season_id]["advanced"], temp_season_data_adv_pst[season_id]["meta"]
            if not meta_s and meta_s_adv: meta_s = meta_s_adv
            if meta_s is not None: historical_playoff_seasons_list.append(SeasonStats(season_id=season_id, team_abbreviation=meta_s.get('TEAM_ABBREVIATION', 'N/A'), player_age=meta_s.get('PLAYER_AGE'), basic_stats=basic_s, advanced_stats=adv_s))

    return {
        "historical_regular_seasons": historical_regular_seasons_list or None,
        "career_regular_season": career_regular_season_stats if career_regular_season_stats.basic_stats or career_regular_season_stats.advanced_stats else None,
        "historical_playoff_seasons": historical_playoff_seasons_list or None,
        "career_playoffs": career_playoff_stats if career_playoff_stats.basic_stats or career_playoff_stats.advanced_stats else None,
    }

# --- Recommendation Logic ---

CATEGORY_MAP = {
    "PTS": ("pts_per_game", "BasicStatsModel", True), "REB": ("reb_per_game", "BasicStatsModel", True),
    "AST": ("ast_per_game", "BasicStatsModel", True), "STL": ("stl_per_game", "BasicStatsModel", True),
    "BLK": ("blk_per_game", "BasicStatsModel", True), "FG3M": ("fg3m_per_game", "BasicStatsModel", True),
    "TOV": ("tov_per_game", "BasicStatsModel", False), "FG_PCT": ("fg_pct", "BasicStatsModel", True),
    "FT_PCT": ("ft_pct", "BasicStatsModel", True), "GP": ("gp", "BasicStatsModel", True),
    "MIN": ("min_per_game", "BasicStatsModel", True), "TS_PCT": ("ts_pct", "AdvancedStatsModel", True),
    "USG_PCT": ("usg_pct", "AdvancedStatsModel", True), "WS": ("ws", "AdvancedStatsModel", True),
    "PIE": ("pie", "AdvancedStatsModel", True), "OFF_RATING": ("off_rating", "AdvancedStatsModel", True),
    "DEF_RATING": ("def_rating", "AdvancedStatsModel", True), "NET_RATING": ("net_rating", "AdvancedStatsModel", True),
    "AST_PCT": ("ast_pct", "AdvancedStatsModel", True), "REB_PCT": ("reb_pct", "AdvancedStatsModel", True),
}
MIN_GAMES_PLAYED_THRESHOLD = 10
MIN_MINUTES_PER_GAME_THRESHOLD = 15.0

def calculate_heuristic_score_for_player(player_data_bundle: Dict, target_categories: List[str], player_full_name: str) -> Optional[RecommendedPlayer]:
    recommendation_score_total = 0.0
    targeted_category_stats_dict = {}
    if not player_data_bundle or not player_data_bundle.get("historical_regular_seasons") or not player_data_bundle["historical_regular_seasons"][-1].basic_stats:
        return None
    latest_season_data = player_data_bundle["historical_regular_seasons"][-1]
    basic_stats, advanced_stats = latest_season_data.basic_stats, latest_season_data.advanced_stats
    if not basic_stats: return None

    latest_season_summary_brief = {"GP": basic_stats.gp, "MIN": basic_stats.min_per_game, "PTS": basic_stats.pts_per_game, "REB": basic_stats.reb_per_game, "AST": basic_stats.ast_per_game, "Team": latest_season_data.team_abbreviation}

    for cat_name_req in target_categories:
        cat_name = cat_name_req.upper().replace("_PER_GAME", "").replace("3", "3")
        if cat_name == "FG3_PCT": cat_name = "FG3_PCT"
        elif "FG_PCT" in cat_name: cat_name = "FG_PCT"
        elif "FT_PCT" in cat_name: cat_name = "FT_PCT"
        if cat_name not in CATEGORY_MAP:
            print(f"Warning: Category '{cat_name_req}' (normalized to '{cat_name}') not recognized. Skipping.")
            targeted_category_stats_dict[cat_name_req] = None; continue
        model_field_name, model_type, higher_is_better = CATEGORY_MAP[cat_name]
        stat_value, source_model_instance = None, None
        if model_type == "BasicStatsModel" and basic_stats: source_model_instance = basic_stats
        elif model_type == "AdvancedStatsModel" and advanced_stats: source_model_instance = advanced_stats
        if source_model_instance and hasattr(source_model_instance, model_field_name): stat_value = getattr(source_model_instance, model_field_name)
        if stat_value is None: targeted_category_stats_dict[cat_name_req] = None; continue
        targeted_category_stats_dict[cat_name_req] = stat_value
        category_score_contribution = 0.0
        if cat_name == "FG_PCT" and basic_stats.fga_per_game and basic_stats.fga_per_game > 0: category_score_contribution = (stat_value * basic_stats.fga_per_game) * 0.1
        elif cat_name == "FT_PCT" and basic_stats.fta_per_game and basic_stats.fta_per_game > 0: category_score_contribution = (stat_value * basic_stats.fta_per_game) * 0.1
        elif cat_name == "TOV": category_score_contribution = -stat_value
        else: category_score_contribution = stat_value
        if not higher_is_better and cat_name != "TOV": category_score_contribution = -category_score_contribution
        recommendation_score_total += category_score_contribution

    player_id_placeholder = basic_stats.gp if basic_stats.gp is not None else 0 # Will be replaced by actual ID
    return RecommendedPlayer(player_id=player_id_placeholder, full_name=player_full_name, recommendation_score=round(recommendation_score_total, 2), targeted_category_stats=targeted_category_stats_dict, latest_season_summary_brief=latest_season_summary_brief)

# --- API Endpoints ---

@app.get("/player/{name}", response_model=PlayerProfileResponse)
def get_player_profile(name: str, season_type: str = Query("all", description="Type of season data: 'regular', 'playoffs', 'all'"), stats_mode: str = Query("all", description="Type of stats: 'basic', 'advanced', 'all'")):
    log_usage(endpoint="/player", payload=f"{name}?season_type={season_type}&stats_mode={stats_mode}")
    player_id = get_player_id(name)
    if not player_id: raise HTTPException(status_code=404, detail="Player not found")
    player_name_str = get_player_name_from_id(player_id)
    fetch_regular = "regular" in season_type.lower() or "all" in season_type.lower()
    fetch_playoffs = "playoffs" in season_type.lower() or "all" in season_type.lower()
    fetch_basic_stats = "basic" in stats_mode.lower() or "all" in stats_mode.lower()
    fetch_advanced_stats = "advanced" in stats_mode.lower() or "all" in stats_mode.lower()
    if not (fetch_regular or fetch_playoffs): raise HTTPException(status_code=400, detail="Invalid season_type. Must be 'regular', 'playoffs', or 'all'.")
    if not (fetch_basic_stats or fetch_advanced_stats): raise HTTPException(status_code=400, detail="Invalid stats_mode. Must be 'basic', 'advanced', or 'all'.")
    try:
        data = get_player_data_from_nba_api(player_id, fetch_regular, fetch_playoffs, fetch_basic_stats, fetch_advanced_stats)
    except ValueError as e: raise HTTPException(status_code=500, detail=f"Player data issue: {e}")
    except Exception as e: print(f"Unhandled exception in get_player_data_from_nba_api: {e}"); raise HTTPException(status_code=500, detail="Error retrieving or processing player data.")
    latest_season_summary_obj = None
    if data["historical_regular_seasons"] and data["historical_regular_seasons"][-1].basic_stats:
        latest_reg_season = data["historical_regular_seasons"][-1]
        ts_pct_summary, usg_pct_summary = (latest_reg_season.advanced_stats.ts_pct, latest_reg_season.advanced_stats.usg_pct) if latest_reg_season.advanced_stats else (None, None)
        latest_season_summary_obj = PlayerStatsSummary(points_per_game=latest_reg_season.basic_stats.pts_per_game, true_shooting_pct=ts_pct_summary, rebounds_per_game=latest_reg_season.basic_stats.reb_per_game, assists_per_game=latest_reg_season.basic_stats.ast_per_game, steals_per_game=latest_reg_season.basic_stats.stl_per_game, blocks_per_game=latest_reg_season.basic_stats.blk_per_game, turnovers_per_game=latest_reg_season.basic_stats.tov_per_game, fg_pct=latest_reg_season.basic_stats.fg_pct, fg3_pct=latest_reg_season.basic_stats.fg3_pct, ft_pct=latest_reg_season.basic_stats.ft_pct, minutes_per_game=latest_reg_season.basic_stats.min_per_game, usage_rate=usg_pct_summary, team=latest_reg_season.team_abbreviation)
    return PlayerProfileResponse(player_id=player_id, player_name=player_name_str, latest_season_summary=latest_season_summary_obj, career_regular_season=data["career_regular_season"], career_playoffs=data["career_playoffs"], historical_regular_seasons=data["historical_regular_seasons"], historical_playoff_seasons=data["historical_playoff_seasons"])

@app.get("/compare", response_model=Dict[str, PlayerProfileResponse])
def compare_players(player1_name: str = Query(..., alias="player1"), player2_name: str = Query(..., alias="player2"), season_type: str = Query("regular", description="Type of season data: 'regular', 'playoffs', 'all'"), stats_mode: str = Query("all", description="Type of stats: 'basic', 'advanced', 'all'")):
    log_usage(endpoint="/compare", payload=f"{player1_name} vs {player2_name} (season: {season_type}, mode: {stats_mode})")
    p1_id, p2_id = get_player_id(player1_name), get_player_id(player2_name)
    if not p1_id: raise HTTPException(status_code=404, detail=f"Player '{player1_name}' not found")
    if not p2_id: raise HTTPException(status_code=404, detail=f"Player '{player2_name}' not found")
    fetch_regular, fetch_playoffs = ("regular" in season_type.lower() or "all" in season_type.lower()), ("playoffs" in season_type.lower() or "all" in season_type.lower())
    fetch_basic, fetch_advanced = ("basic" in stats_mode.lower() or "all" in stats_mode.lower()), ("advanced" in stats_mode.lower() or "all" in stats_mode.lower())
    if not (fetch_regular or fetch_playoffs): raise HTTPException(status_code=400, detail="Invalid season_type for comparison.")
    if not (fetch_basic or fetch_advanced): raise HTTPException(status_code=400, detail="Invalid stats_mode for comparison.")
    try:
        p1_data, p2_data = get_player_data_from_nba_api(p1_id, fetch_regular, fetch_playoffs, fetch_basic, fetch_advanced), get_player_data_from_nba_api(p2_id, fetch_regular, fetch_playoffs, fetch_basic, fetch_advanced)
    except Exception as e: print(f"Exception during data fetching for compare: {e}"); raise HTTPException(status_code=500, detail=f"Error retrieving data for comparison: {e}")
    p1_name_str, p2_name_str = get_player_name_from_id(p1_id), get_player_name_from_id(p2_id)
    p1_summary, p2_summary = None, None
    if p1_data["historical_regular_seasons"] and p1_data["historical_regular_seasons"][-1].basic_stats:
        latest_p1 = p1_data["historical_regular_seasons"][-1]
        p1_ts, p1_usg = (latest_p1.advanced_stats.ts_pct, latest_p1.advanced_stats.usg_pct) if latest_p1.advanced_stats else (None,None)
        p1_summary = PlayerStatsSummary(points_per_game=latest_p1.basic_stats.pts_per_game, true_shooting_pct=p1_ts, rebounds_per_game=latest_p1.basic_stats.reb_per_game, assists_per_game=latest_p1.basic_stats.ast_per_game, steals_per_game=latest_p1.basic_stats.stl_per_game, blocks_per_game=latest_p1.basic_stats.blk_per_game, turnovers_per_game=latest_p1.basic_stats.tov_per_game, fg_pct=latest_p1.basic_stats.fg_pct, fg3_pct=latest_p1.basic_stats.fg3_pct, ft_pct=latest_p1.basic_stats.ft_pct, minutes_per_game=latest_p1.basic_stats.min_per_game, usage_rate=p1_usg, team=latest_p1.team_abbreviation)
    p1_response = PlayerProfileResponse(player_id=p1_id, player_name=p1_name_str, latest_season_summary=p1_summary, career_regular_season=p1_data["career_regular_season"], career_playoffs=p1_data["career_playoffs"], historical_regular_seasons=p1_data["historical_regular_seasons"], historical_playoff_seasons=p1_data["historical_playoff_seasons"])
    if p2_data["historical_regular_seasons"] and p2_data["historical_regular_seasons"][-1].basic_stats:
        latest_p2 = p2_data["historical_regular_seasons"][-1]
        p2_ts, p2_usg = (latest_p2.advanced_stats.ts_pct, latest_p2.advanced_stats.usg_pct) if latest_p2.advanced_stats else (None,None)
        p2_summary = PlayerStatsSummary(points_per_game=latest_p2.basic_stats.pts_per_game, true_shooting_pct=p2_ts, rebounds_per_game=latest_p2.basic_stats.reb_per_game, assists_per_game=latest_p2.basic_stats.ast_per_game, steals_per_game=latest_p2.basic_stats.stl_per_game, blocks_per_game=latest_p2.basic_stats.blk_per_game, turnovers_per_game=latest_p2.basic_stats.tov_per_game, fg_pct=latest_p2.basic_stats.fg_pct, fg3_pct=latest_p2.basic_stats.fg3_pct, ft_pct=latest_p2.basic_stats.ft_pct, minutes_per_game=latest_p2.basic_stats.min_per_game, usage_rate=p2_usg, team=latest_p2.team_abbreviation)
    p2_response = PlayerProfileResponse(player_id=p2_id, player_name=p2_name_str, latest_season_summary=p2_summary, career_regular_season=p2_data["career_regular_season"], career_playoffs=p2_data["career_playoffs"], historical_regular_seasons=p2_data["historical_regular_seasons"], historical_playoff_seasons=p2_data["historical_playoff_seasons"])
    return {player1_name: p1_response, player2_name: p2_response}

class LineupRequest(BaseModel):
    players: List[str]

@app.post("/lineup")
def get_lineup_stats(request: LineupRequest, metric: str = Query("avg", pattern="^(avg|total)$")):
    log_usage(endpoint="/lineup", payload=f"Players: {request.players}, Metric: {metric}")
    player_summaries_for_aggregation, lineup_player_names = [], []
    for player_slug in request.players:
        player_id = get_player_id(player_slug)
        if not player_id: raise HTTPException(status_code=404, detail=f"Player '{player_slug}' not found in lineup.")
        player_name = get_player_name_from_id(player_id)
        lineup_player_names.append(player_name)
        try:
            data = get_player_data_from_nba_api(player_id, True, False, True, True)
        except Exception as e: print(f"Exception during data fetching for lineup player {player_slug}: {e}"); raise HTTPException(status_code=500, detail=f"Error retrieving data for player {player_slug} in lineup.")
        current_player_summary = None
        if data["historical_regular_seasons"] and data["historical_regular_seasons"][-1].basic_stats:
            latest_reg_season = data["historical_regular_seasons"][-1]
            ts_pct, usg_rate = (latest_reg_season.advanced_stats.ts_pct, latest_reg_season.advanced_stats.usg_pct) if latest_reg_season.advanced_stats else (None,None)
            current_player_summary = PlayerStatsSummary(points_per_game=latest_reg_season.basic_stats.pts_per_game, true_shooting_pct=ts_pct, rebounds_per_game=latest_reg_season.basic_stats.reb_per_game, assists_per_game=latest_reg_season.basic_stats.ast_per_game, steals_per_game=latest_reg_season.basic_stats.stl_per_game, blocks_per_game=latest_reg_season.basic_stats.blk_per_game, turnovers_per_game=latest_reg_season.basic_stats.tov_per_game, fg_pct=latest_reg_season.basic_stats.fg_pct, fg3_pct=latest_reg_season.basic_stats.fg3_pct, ft_pct=latest_reg_season.basic_stats.ft_pct, minutes_per_game=latest_reg_season.basic_stats.min_per_game, usage_rate=usg_rate, team=latest_reg_season.team_abbreviation)
            player_summaries_for_aggregation.append(current_player_summary.model_dump(exclude_none=True))
        else: player_summaries_for_aggregation.append({})
    if not player_summaries_for_aggregation: raise HTTPException(status_code=500, detail="Could not retrieve any summary stats for the lineup players.")
    aggregated_stats = {}
    numeric_fields = [f.name for f in PlayerStatsSummary.model_fields.values() if f.annotation in [Optional[float], Optional[int], float, int] and f.name != "team"]
    for field in numeric_fields:
        values = [p_summary_dict.get(field) for p_summary_dict in player_summaries_for_aggregation if isinstance(p_summary_dict.get(field), (int, float))]
        if not values: continue
        if metric == "avg": aggregated_stats[f"avg_{field}"] = round(sum(values) / len(values), 2)
        else: aggregated_stats[f"total_{field}"] = round(sum(values), 2)
    return {"lineup_players": lineup_player_names, "aggregation_metric": metric, "aggregated_stats_from_latest_season_summary": aggregated_stats, "note": "Lineup stats are aggregated from each player's latest regular season summary."}

@app.post("/recommendations/categories", response_model=RecommendationResponse, tags=["Recommendations"])
async def get_category_recommendations(request_body: RecommendationRequest):
    log_usage(endpoint="/recommendations/categories", payload=request_body.model_dump_json())
    active_players_raw = nba_static_players.get_active_players()
    candidate_players = []
    for p_dict in active_players_raw:
        player_id = p_dict['id']
        if player_id in request_body.excluded_player_ids: continue
        try:
            player_data_bundle = get_player_data_from_nba_api(player_id, True, False, True, True)
            if not player_data_bundle or not player_data_bundle.get("historical_regular_seasons") or not player_data_bundle["historical_regular_seasons"][-1].basic_stats: continue
            latest_season = player_data_bundle["historical_regular_seasons"][-1]
            if not latest_season.basic_stats: continue
            gp, mpg = latest_season.basic_stats.gp, latest_season.basic_stats.min_per_game
            if not (gp and mpg and gp >= MIN_GAMES_PLAYED_THRESHOLD and mpg >= MIN_MINUTES_PER_GAME_THRESHOLD): continue
            recommended_player_obj = calculate_heuristic_score_for_player(player_data_bundle, request_body.target_categories, p_dict["full_name"])
            if recommended_player_obj:
                recommended_player_obj.player_id = player_id
                candidate_players.append(recommended_player_obj)
        except Exception as e: print(f"Error processing player {player_id} for recommendation: {e}"); continue
    candidate_players.sort(key=lambda p: p.recommendation_score, reverse=True)
    final_recommendations = candidate_players[:request_body.num_recommendations]
    return RecommendationResponse(recommendations=final_recommendations)
