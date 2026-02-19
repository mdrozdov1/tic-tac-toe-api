# Tic-Tac-Toe API

A containerized, full-stack Tic-Tac-Toe game featuring a FastAPI server, SQLModel for persistence, and a terminal-based interactive client.

![Tic-Tac-Toe Demo](tictactoegif.gif)
---

## Features

* RESTful API: Create games, make moves, and view history via HTTP endpoints.
* Dynamic Board Size: Supports grids from 3x3 up to 10x10.
* Automated Opponent: Includes a random-move AI (Player O) that responds immediately to your moves.
* Data Persistence: Uses SQLite via SQLModel to store game states and move history.
* ASCII Visualization: A custom board formatter provides a clear visual state in your terminal.

---

## Tech Stack

* Language: Python 3.11
* Framework: FastAPI
* Database: SQLite and SQLModel
* Containerization: Docker
* Testing: Pytest and HTTPX

---

## Prerequisites

* Docker
* Python 3.11 or higher (to run the client script locally)

---

## Getting Started

### Build and Run with Docker
Build the image and start the server container on port 8000:
```bash
docker build -t tictactoe-app .
docker run -d -p 8000:8000 --name tictactoe-server tictactoe-app
```

### Run in a virtual env locally
Create a virtual environment and install requirements:
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Run main.py:
```bash
python main.py
```

### Play the Game
Once the server is running, launch the interactive client in a separate terminal:

```bash
python play.py
```

Note: Ensure you have the requests library installed.

### API Documentation
Once the server is running, you can access the interactive Swagger UI documentation at:
`http://localhost:8000/docs`

### API Reference
#### Games
- POST `/games?size=3`: Create a new game session.

- GET `/games`: List all active and completed games.

- GET `/games/{game_id}/moves`: View the full chronological history for a specific match.

#### Gameplay
- POST `/games/{game_id}/move`: Submit a move for Player X.
  - Input: JSON coordinates { "x": int, "y": int }.
 
### API Usage Examples

In addition to the interactive `play.py` script, you can interact with the API programmatically using standard Python libraries like `requests`.

#### List All Games
Fetch a list of all active and completed games to view their IDs and status.

```python
import requests

response = requests.get("http://localhost:8000/games")
games = response.json()

print(f"Found {len(games)} games:")
for game in games:
    print(f"ID: {game['game_id']} | Status: {game['status']} | Moves: {game['move_count']}")
```

#### Get Move History
Retrieve the full chronological history of moves for a specific game ID.

```python
import requests

game_id = 1  # Replace with your target game ID

response = requests.get(f"http://localhost:8000/games/{game_id}/moves")

if response.status_code == 200:
    moves = response.json()
    print(f"History for Game #{game_id}:")
    for move in moves:
        print(f"Move {move['move_number']}: {move['player']} placed at ({move['x']}, {move['y']})")
else:
    print("Game not found.")
```

#### Create a Custom 5x5 Game
Manually create a larger board using the size query parameter.
```python
import requests

response = requests.post("http://localhost:8000/games", params={"size": 5})
game = response.json()

print(f"Created 5x5 Game (ID: {game['game_id']})")
print(game['visual_board'])
```

### Testing
The project includes a suite of tests covering database initialization, game logic, and API edge cases.

To run the tests inside the container:

```bash
docker exec -it tictactoe-server pytest
```

To run the tests locally in a virtual env:

```bash
pytest
```
