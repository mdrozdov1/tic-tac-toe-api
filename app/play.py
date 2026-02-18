import sys

import requests

BASE_URL = "http://127.0.0.1:8000"


def play():
    print("🎮 CONNECTING TO TIC-TAC-TOE SERVER...")

    try:
        board_size = int(input(f"Choose your board size: "))

        response = requests.post(f"{BASE_URL}/games", params={"size": board_size})
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to localhost:8000. Is the server running?")
        return

    game = response.json()
    game_id = game["game_id"]

    print(f"\n✅ Game #{game_id} Created!")
    print(f"📝 Instructions: Enter coordinates as 'x y' (e.g., '1 1' for center).")
    print(game["visual_board"])

    while game["status"] == "IN_PROGRESS":
        try:
            user_input = input(f"Your Move (Game #{game_id}) > ")
            if user_input.lower() in ["q", "quit", "exit"]:
                print("Quitting...")
                break

            parts = user_input.split()
            if len(parts) != 2:
                print("⚠️  Invalid input. Please enter 'x y' (e.g. 0 0)")
                continue

            x, y = int(parts[0]), int(parts[1])

            move_resp = requests.post(
                f"{BASE_URL}/games/{game_id}/move", json={"x": x, "y": y}
            )

            if move_resp.status_code == 409:
                print("⛔ That square is already taken!")
                continue
            if move_resp.status_code == 400:
                print("⛔ Out of bounds! x and y must be 0, 1, or 2.")
                continue

            move_resp.raise_for_status()
            game = move_resp.json()

            print("\n" + "-" * 30)
            print(game["visual_board"])
            print("-" * 30)

        except ValueError:
            print("⚠️  Please enter numbers only.")
        except Exception as e:
            print(f"❌ Error: {e}")
            break

    print(f"\n🏁 GAME OVER! Result: {game['status']}")


if __name__ == "__main__":
    play()
