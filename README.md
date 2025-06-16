# NBA Player Stats API

This project is a FastAPI application that provides NBA player statistics. It allows you to retrieve career statistics for individual players, compare players, and get aggregated statistics for a lineup of players.

## Features

*   **Get Player Stats:** Retrieve detailed career statistics for any NBA player.
*   **Compare Players:** Compare the statistics of two NBA players side-by-side.
*   **Lineup Analysis:** Calculate aggregated statistics (average or total) for a custom lineup of players.
*   **Caching:** Player data is cached to provide faster responses for frequently requested players.
*   **Usage Tracking:** API usage is logged in a local database.

## Installation and Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```
2.  **Create and activate a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Run the application:**
    ```bash
    uvicorn app.main:app --reload
    ```
    The API will be accessible at `http://127.0.0.1:8000`.

## API Endpoints

### Get Player Stats (Enhanced)

*   **Endpoint:** `GET /player/{name}`
*   **Description:** Retrieves comprehensive career, historical season, playoff, and advanced statistics for a specific player.
*   **Path Parameters:**
    *   `name` (string, required): The player's name (e.g., "lebron-james").
*   **Query Parameters:**
    *   `season_type` (string, optional, default: "all"): Type of season data.
        *   `"regular"`: Only regular season data.
        *   `"playoffs"`: Only playoff data.
        *   `"all"`: Both regular season and playoff data.
    *   `stats_mode` (string, optional, default: "all"): Type of statistics.
        *   `"basic"`: Only basic stats (points, rebounds, assists, percentages, etc.).
        *   `"advanced"`: Only advanced stats (ratings, percentages like USG%, TS%, PIE, WS, etc.).
        *   `"all"`: Both basic and advanced stats.
*   **Example Request (Fetching all regular season data, basic + advanced for LeBron James):**
    ```
    GET /player/lebron-james?season_type=regular&stats_mode=all
    ```
*   **Example Response Structure (200 OK - Snippet):**
    The response is a `PlayerProfileResponse` object.
    ```json
    {
        "player_id": 2544,
        "player_name": "LeBron James",
        "latest_season_summary": { // Summary of most recent regular season
            "points_per_game": 28.9,
            "true_shooting_pct": 0.583,
            "rebounds_per_game": 8.3,
            // ... other summary fields from PlayerStatsSummary
            "team": "LAL"
        },
        "career_regular_season": {
            "basic_stats": { /* ... BasicStatsModel fields ... */ },
            "advanced_stats": { /* ... AdvancedStatsModel fields ... */ }
        },
        "career_playoffs": { /* ... similar to career_regular_season ... */ },
        "historical_regular_seasons": [
            {
                "season_id": "2022-23",
                "team_abbreviation": "LAL",
                "player_age": 38,
                "basic_stats": {
                    "gp": 55,
                    "pts_per_game": 28.9,
                    // ... other BasicStatsModel fields ...
                },
                "advanced_stats": {
                    "usg_pct": 0.320,
                    "ts_pct": 0.583,
                    "ws": 5.6,
                    // ... other AdvancedStatsModel fields ...
                }
            },
            // ... other seasons ...
        ],
        "historical_playoff_seasons": [ /* ... similar structure for playoff seasons ... */ ]
    }
    ```
    *   **Note:** `BasicStatsModel` includes fields like `gp`, `min_per_game`, `pts_per_game`, `fg_pct`, `ast_per_game`, etc.
    *   **Note:** `AdvancedStatsModel` includes fields like `off_rating`, `def_rating`, `net_rating`, `usg_pct`, `ts_pct`, `pie`, `ws`, etc.
*   **Error Responses:**
    *   `400 Bad Request`: If `season_type` or `stats_mode` are invalid.
    *   `404 Not Found`: If the player is not found.
    *   `500 Internal Server Error`: If player data is incomplete or there's a server-side issue.

### Compare Players (Enhanced)

*   **Endpoint:** `GET /compare`
*   **Description:** Compares the detailed statistics of two players.
*   **Query Parameters:**
    *   `player1` (string, required): Name of the first player.
    *   `player2` (string, required): Name of the second player.
    *   `season_type` (string, optional, default: "regular"): Common season type for both players ('regular', 'playoffs', 'all').
    *   `stats_mode` (string, optional, default: "all"): Common stats mode for both players ('basic', 'advanced', 'all').
*   **Example Request:**
    ```
    GET /compare?player1=lebron-james&player2=stephen-curry&season_type=regular&stats_mode=all
    ```
*   **Example Response (200 OK - Snippet):**
    The response is a dictionary where keys are player names, and values are their full `PlayerProfileResponse` objects (see structure above).
    ```json
    {
        "LeBron James": { /* PlayerProfileResponse for LeBron James */ },
        "Stephen Curry": { /* PlayerProfileResponse for Stephen Curry */ }
    }
    ```
*   **Error Responses:**
    *   `404 Not Found`: If one or both players are not found.
    *   `500 Internal Server Error`: If stats retrieval fails.

### Get Lineup Stats (Updated)

*   **Endpoint:** `POST /lineup`
*   **Description:** Calculates aggregated statistics for a lineup of players based on their latest regular season summary stats.
*   **Request Body (JSON):**
    ```json
    {
        "players": ["player-name-1", "player-name-2", "player-name-3"]
    }
    ```
*   **Query Parameters:**
    *   `metric` (string, optional, default: "avg"): The aggregation metric ("avg" or "total").
*   **Example Response (200 OK - Snippet):**
    ```json
    {
        "lineup_players": ["LeBron James", "Stephen Curry"],
        "aggregation_metric": "avg",
        "aggregated_stats_from_latest_season_summary": {
            "avg_points_per_game": 28.5,
            "avg_true_shooting_pct": 0.600,
            // ... other aggregated PlayerStatsSummary fields ...
        },
        "note": "Lineup stats are aggregated from each player's latest regular season summary."
    }
    ```
*   **Error Responses:**
    *   `404 Not Found`: If any player in the lineup is not found.
    *   `422 Unprocessable Entity`: If the request body is invalid.
    *   `500 Internal Server Error`: If stats retrieval fails.

## Running Tests

This project uses `pytest` for testing. To run the tests:

1.  Make sure you have installed the development dependencies (including `pytest` and `httpx` if not already installed with `requirements.txt`). You might need a `requirements-dev.txt` or similar if `pytest` is not in the main `requirements.txt`. For this project, `pytest` and `httpx` are in `requirements.txt`.
2.  Navigate to the root directory of the project.
3.  Run the following command:

    ```bash
    pytest
    ```

## Contributing

Contributions are welcome! If you'd like to contribute to this project, please follow these steps:

1.  Fork the repository.
2.  Create a new branch for your feature or bug fix (`git checkout -b feature/your-feature-name` or `bugfix/issue-number`).
3.  Make your changes and commit them with clear and concise messages.
4.  Ensure your code adheres to the project's coding standards (e.g., by running a linter if provided).
5.  Write tests for your changes and ensure all tests pass.
6.  Push your changes to your forked repository.
7.  Create a pull request to the main repository's `main` branch (or the appropriate development branch).

Please provide a clear description of your changes in the pull request.

## License

This project is licensed under the MIT License. See the `LICENSE` file for more details (if a `LICENSE` file is present in the repository).

---

*This README was generated with assistance from an AI coding agent.*
