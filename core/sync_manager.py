import struct
import json
from core.data_manager import DataManager

_dm = DataManager()
_dm.load_config("network.json")


class MessageTypes:
    JOIN_REQUEST = _dm.get_config("network.json", "message_types.JOIN_REQUEST")
    JOIN_ACCEPT = _dm.get_config("network.json", "message_types.JOIN_ACCEPT")
    JOIN_REJECT = _dm.get_config("network.json", "message_types.JOIN_REJECT")
    PLAYER_READY = _dm.get_config("network.json", "message_types.PLAYER_READY")
    GAME_START = _dm.get_config("network.json", "message_types.GAME_START")
    PLAYER_INPUT = _dm.get_config("network.json", "message_types.PLAYER_INPUT")
    GAME_STATE_SYNC = _dm.get_config("network.json", "message_types.GAME_STATE_SYNC")
    GAME_OVER = _dm.get_config("network.json", "message_types.GAME_OVER")
    PLAYER_DISCONNECT = _dm.get_config("network.json", "message_types.PLAYER_DISCONNECT")
    HEARTBEAT = _dm.get_config("network.json", "message_types.HEARTBEAT")
    LOBBY_STATE = _dm.get_config("network.json", "message_types.LOBBY_STATE")


del _dm


class SyncManager:
    MAGIC = 0xDEADBEEF
    HEADER_FMT = "!IHI"
    HEADER_SIZE = struct.calcsize(HEADER_FMT)

    @classmethod
    def pack_message(cls, msg_type: int, data: dict):
        payload = json.dumps(data).encode("utf-8")
        header = struct.pack(cls.HEADER_FMT, cls.MAGIC, msg_type, len(payload))
        return header + payload

    @classmethod
    def unpack_message(cls, data: bytes):
        if len(data) < cls.HEADER_SIZE:
            return None
        magic, msg_type, payload_len = struct.unpack(cls.HEADER_FMT, data[:cls.HEADER_SIZE])
        if magic != cls.MAGIC:
            return None
        payload_data = data[cls.HEADER_SIZE:cls.HEADER_SIZE + payload_len]
        try:
            payload = json.loads(payload_data.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None
        return msg_type, payload

    @classmethod
    def build_game_state(cls, host_stats, remote_states: dict):
        return {
            "host": {
                "x": host_stats.get("x", 0),
                "y": host_stats.get("y", 0),
                "health": host_stats.get("health", 100),
                "facing": host_stats.get("facing", -1),
                "score": host_stats.get("score", 0),
                "shooting": host_stats.get("shooting", False),
            },
            "remotes": {
                pid: {
                    "x": s.get("x", 0),
                    "y": s.get("y", 0),
                    "health": s.get("health", 100),
                    "facing": s.get("facing", -1),
                    "score": s.get("score", 0),
                    "shooting": s.get("shooting", False),
                }
                for pid, s in remote_states.items()
            },
            "enemies": host_stats.get("enemies", []),
            "shots": host_stats.get("shots", []),
            "bombs": host_stats.get("bombs", []),
            "explosions": host_stats.get("explosions", []),
        }

    @classmethod
    def build_player_input(cls, player_id: str, input_data: dict):
        return {
            "player_id": player_id,
            "direction": input_data.get("direction", 0),
            "shooting": input_data.get("shooting", False),
        }
