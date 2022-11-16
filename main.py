from dotenv import dotenv_values
import requests
import webbrowser
import websocket
import json
import time
import math
import numpy as np

FRONTEND_BASE = "noflight.monad.fi"
BACKEND_BASE = "noflight.monad.fi/backend"

game_id = None


def normalize_heading(heading):
    return round(heading + 360) % 360

def on_message(ws: websocket.WebSocketApp, message):
    [action, payload] = json.loads(message)

    if action != "game-instance":
        print([action, payload])
        return

     # New game tick arrived!
    game_state = json.loads(payload["gameState"])
    commands = generate_commands(game_state)

    time.sleep(0.1)
    ws.send(json.dumps(["run-command", {"gameId": game_id, "payload": commands}]))


def on_error(ws: websocket.WebSocketApp, error):
    print(error)


def on_open(ws: websocket.WebSocketApp):
    print("OPENED")
    ws.send(json.dumps(["sub-game", {"id": game_id}]))


def on_close(ws, close_status_code, close_msg):
    print("CLOSED")


def calculate_direction(x1,x2,y1,y2):
    new_dir = np.rad2deg(math.atan2(y2-y1, x2-x1))
    return normalize_heading(new_dir)


def calculate_distance(x1,x2,y1,y2):
    dist = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    return dist


# Change this to your own implementation
def generate_commands(game_state):
    commands = []

    for aircraft in game_state["aircrafts"]:
        x = aircraft["position"]["x"]
        y = aircraft["position"]["y"]

        airport = game_state["airports"][0]
        airport_x = airport["position"]["x"]
        airport_y = airport["position"]["y"]
        airport_dir = airport["direction"]

        y_offset_opposite = 20
        y_offset_directional = 23

        # if the plane is inside airport, match directions
        if calculate_distance(x, airport_x, y, airport_y) < 25:
            target_dir = airport_dir
        else:

            # if approaching from opposite side, always offset y-axis negatively
            if abs(aircraft["direction"] - airport_dir == 180):
                airport_y -= y_offset_opposite
            else:
                # offset to same direction airport is pointing to
                airport_y += int(y_offset_directional * math.sin(np.deg2rad(abs(airport_dir + 180))))
                airport_x += int(y_offset_directional * math.cos(np.deg2rad(abs(airport_dir + 180))))

            target_dir = calculate_direction(x, airport_x, y, airport_y)

        old_dir = aircraft["direction"]

        # Adjust bearing accordingly. (There is probably a better way for this
        # but it works)
        if old_dir - target_dir < 180:
            if abs(old_dir - target_dir) < 20:
                new_dir = target_dir
            else:
                if old_dir > target_dir:
                    new_dir = old_dir - 20
                else:
                    new_dir = old_dir + 20
        else:
            if abs(old_dir - target_dir) < 20:
                new_dir = target_dir
            else:
                if old_dir > target_dir:
                    new_dir = old_dir + 20
                else:
                    new_dir = old_dir - 20

        commands.append(f"HEAD {aircraft['id']} {normalize_heading(new_dir)}")

    return commands


def main():
    config = dotenv_values()
    res = requests.post(
        f"https://{BACKEND_BASE}/api/levels/{config['LEVEL_ID']}",
        headers={
            "Authorization": config["TOKEN"]
        })

    if not res.ok:
        print(f"Couldn't create game: {res.status_code} - {res.text}")
        return

    game_instance = res.json()

    global game_id
    game_id = game_instance["entityId"]

    url = f"https://{FRONTEND_BASE}/?id={game_id}"
    print(f"Game at {url}")
    webbrowser.open(url, new=2)
    time.sleep(2)

    ws = websocket.WebSocketApp(
        f"wss://{BACKEND_BASE}/{config['TOKEN']}/", on_message=on_message, on_open=on_open, on_close=on_close, on_error=on_error)
    ws.run_forever()


if __name__ == "__main__":
    main()