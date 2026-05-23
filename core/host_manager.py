import json
from core.data_manager import DataManager
from core.sync_manager import SyncManager, MessageTypes

_dm = DataManager()
_dm.load_config("network.json")


class HostManager:
    STATE_LOBBY = "lobby"
    STATE_COUNTDOWN = "countdown"
    STATE_PLAYING = "playing"
    STATE_GAMEOVER = "game_over"

    def __init__(self, network_manager):
        self._nm = network_manager
        self._max_players = _dm.get_config("network.json", "room.max_players")
        self._min_players = _dm.get_config("network.json", "room.min_players")
        self._countdown_seconds = _dm.get_config("network.json", "room.countdown_seconds")
        self._state = self.STATE_LOBBY
        self._players = {}
        self._player_scores = {}
        self._player_ready = {}
        self._countdown_timer = 0

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value):
        self._state = value

    @property
    def players(self):
        return self._players

    @property
    def player_scores(self):
        return self._player_scores

    @property
    def player_count(self):
        return len(self._players) + 1

    def is_ready_to_start(self):
        return self.player_count >= self._min_players and all(self._player_ready.values())

    def add_player(self, player_id: str, player_name: str = ""):
        if player_id in self._players:
            return False
        if len(self._players) >= self._max_players - 1:
            return False
        self._players[player_id] = {"name": player_name or player_id, "ready": False,
                                      "health": 100, "x": 0, "y": 0, "facing": -1,
                                      "score": 0, "shooting": False}
        self._player_ready[player_id] = False
        self._player_scores[player_id] = 0
        return True

    def remove_player(self, player_id: str):
        if player_id in self._players:
            del self._players[player_id]
        if player_id in self._player_ready:
            del self._player_ready[player_id]
        if player_id in self._player_scores:
            del self._player_scores[player_id]

    def set_player_ready(self, player_id: str, ready: bool = True):
        if player_id in self._player_ready:
            self._player_ready[player_id] = ready

    def update_player_state(self, player_id: str, state: dict):
        if player_id in self._players:
            p = self._players[player_id]
            p["x"] = state.get("x", p["x"])
            p["y"] = state.get("y", p["y"])
            p["health"] = state.get("health", p["health"])
            p["facing"] = state.get("facing", p.get("facing", -1))
            p["score"] = state.get("score", p["score"])
            p["shooting"] = state.get("shooting", p["shooting"])
            self._player_scores[player_id] = state.get("score", self._player_scores.get(player_id, 0))

    def get_player_state(self, player_id: str):
        return self._players.get(player_id, None)

    def update_countdown(self):
        if self._state == self.STATE_COUNTDOWN:
            self._countdown_timer -= 1
            if self._countdown_timer <= 0:
                self._state = self.STATE_PLAYING
                return True
        return False

    def start_countdown(self):
        self._state = self.STATE_COUNTDOWN
        self._countdown_timer = self._countdown_seconds * 40

    def get_countdown(self):
        return max(0, self._countdown_timer // 40)

    def reset(self):
        self._state = self.STATE_LOBBY
        self._players = {}
        self._player_scores = {}
        self._player_ready = {}
        self._countdown_timer = 0

    def broadcast_lobby_state(self):
        data = {
            "state": self._state,
            "players": list(self._players.keys()),
            "ready": self._player_ready,
            "countdown": self.get_countdown() if self._state == self.STATE_COUNTDOWN else -1,
        }
        self._nm.broadcast_to_players(MessageTypes.LOBBY_STATE, data)

    def compute_spawn_positions(self, screen_width, spawn_y):
        player_ids = self.get_all_player_ids()
        n = len(player_ids)
        positions = {}
        for i, pid in enumerate(player_ids):
            x = int(screen_width * (i + 1) / (n + 1))
            positions[pid] = (x, spawn_y)
        return positions

    def broadcast_game_start(self):
        player_ids = self.get_all_player_ids()
        from core.constants import SCREENRECT
        spawn_positions = self.compute_spawn_positions(SCREENRECT.width, SCREENRECT.height)
        data = {
            "players": player_ids,
            "countdown": self._countdown_seconds,
            "spawn_positions": {pid: {"x": pos[0], "y": pos[1]} for pid, pos in spawn_positions.items()},
        }
        self._nm.broadcast_to_players(MessageTypes.GAME_START, data)

    def broadcast_game_over(self, final_scores: dict):
        data = {"scores": final_scores}
        self._nm.broadcast_to_players(MessageTypes.GAME_OVER, data)

    def get_sorted_scores(self):
        all_scores = {**self._player_scores}
        return sorted(all_scores.items(), key=lambda x: x[1], reverse=True)

    def get_all_player_ids(self):
        return ["host_1"] + list(self._players.keys())



