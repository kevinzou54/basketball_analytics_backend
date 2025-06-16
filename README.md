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

### Get Player Stats

*   **Endpoint:** `GET /player/{name}`
*   **Description:** Retrieves career statistics for a specific player.
*   **Path Parameters:**
    *   `name` (string, required): The player's name (e.g., "lebron-james").
*   **Example Request:**
    ```
    GET /player/lebron-james
    ```
*   **Example Response (200 OK):**
    ```json
    {
        "points_per_game": 27.1,
        "true_shooting_pct": 0.588,
        "rebounds_per_game": 7.5,
        "assists_per_game": 7.4,
        "steals_per_game": 1.5,
        "blocks_per_game": 0.8,
        "turnovers_per_game": 3.5,
        "fg_pct": 0.505,
        "fg3_pct": 0.347,
        "ft_pct": 0.736,
        "minutes_per_game": 37.9,
        "usage_rate": "N/A",
        "team": "LAL"
    }
    ```
*   **Error Responses:**
    *   `404 Not Found`: If the player is not found.
    *   `500 Internal Server Error`: If player data is incomplete or there's a server-side issue.

### Compare Players

*   **Endpoint:** `GET /compare`
*   **Description:** Compares the statistics of two players.
*   **Query Parameters:**
    *   `player1` (string, required): The name of the first player (e.g., "michael-jordan").
    *   `player2` (string, required): The name of the second player (e.g., "kobe-bryant").
*   **Example Request:**
    ```
    GET /compare?player1=michael-jordan&player2=kobe-bryant
    ```
*   **Example Response (200 OK):**
    ```json
    {
        "player1": {
            "points_per_game": 30.1,
            "true_shooting_pct": 0.569,
            "rebounds_per_game": 6.2,
            "assists_per_game": 5.3,
            // ... other stats
            "name": "Michael Jordan"
        },
        "player2": {
            "points_per_game": 25.0,
            "true_shooting_pct": 0.550,
            "rebounds_per_game": 5.2,
            "assists_per_game": 4.7,
            // ... other stats
            "name": "Kobe Bryant"
        }
    }
    ```
*   **Error Responses:**
    *   `404 Not Found`: If one or both players are not found.
    *   `500 Internal Server Error`: If stats retrieval fails for one or both players.

### Get Lineup Stats

*   **Endpoint:** `POST /lineup`
*   **Description:** Calculates aggregated statistics for a lineup of players.
*   **Request Body (JSON):**
    ```json
    {
        "players": ["player-name-1", "player-name-2", "player-name-3"]
    }
    ```
*   **Query Parameters:**
    *   `metric` (string, optional, default: "avg"): The aggregation metric. Can be "avg" or "total".
    *   `stats` (string, optional): A comma-separated list of specific stats to include (e.g., "points_per_game,rebounds_per_game"). If not provided, all applicable stats are returned.
*   **Example Request:**
    ```
    POST /lineup?metric=avg&stats=points_per_game,assists_per_game
    Content-Type: application/json

    {
        "players": ["lebron-james", "stephen-curry", "kevin-durant"]
    }
    ```
*   **Example Response (200 OK):**
    ```json
    {
        "lineup": ["Lebron James", "Stephen Curry", "Kevin Durant"],
        "metric": "avg",
        "avg_points_per_game": 28.5,
        "avg_assists_per_game": 6.8
    }
    ```
*   **Error Responses:**
    *   `404 Not Found`: If any player in the lineup is not found.
    *   `422 Unprocessable Entity`: If the request body or query parameters are invalid.
    *   `500 Internal Server Error`: If stats retrieval fails for any player.

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
