import socket
import struct
import threading
import queue
import time
from core.data_manager import DataManager
from core.sync_manager import SyncManager, MessageTypes

_dm = DataManager()
_dm.load_config("network.json")


class NetworkManager:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._tcp_port = _dm.get_config("network.json", "tcp.port")
        self._buffer_size = _dm.get_config("network.json", "tcp.buffer_size")
        self._connect_timeout = _dm.get_config("network.json", "tcp.connect_timeout")
        self._udp_port = _dm.get_config("network.json", "udp_discovery.port")
        self._multicast_group = _dm.get_config("network.json", "udp_discovery.multicast_group")
        self._broadcast_interval = _dm.get_config("network.json", "udp_discovery.broadcast_interval")
        self._discover_token = _dm.get_config("network.json", "udp_discovery.discover_token")
        self._response_token = _dm.get_config("network.json", "udp_discovery.response_token")

        self._recv_queue = queue.Queue()
        self._send_queue = queue.Queue()

        self._tcp_server_socket = None
        self._tcp_client_socket = None
        self._client_connections = {}
        self._client_addrs = {}
        self._client_recv_buffers = {}

        self._udp_socket = None
        self._is_host = False
        self._is_client = False
        self._running = False
        self._server_thread = None
        self._client_thread = None
        self._udp_thread = None
        self._player_id = ""
        self._room_name = "Room"
        self._discovered_rooms = {}
        self._next_client_id = 2
        self._spawn_positions = {}
        self._client_heartbeats = {}
        self._heartbeat_interval = 3.0

    @property
    def recv_queue(self):
        return self._recv_queue

    @property
    def send_queue(self):
        return self._send_queue

    @property
    def is_host(self):
        return self._is_host

    @property
    def is_client(self):
        return self._is_client

    @property
    def player_id(self):
        return self._player_id

    def set_player_id(self, pid: str):
        self._player_id = pid

    @property
    def connected(self):
        return self._is_host or self._is_client

    @property
    def discovered_rooms(self):
        return self._discovered_rooms

    @property
    def spawn_positions(self):
        return self._spawn_positions

    @spawn_positions.setter
    def spawn_positions(self, value):
        self._spawn_positions = value

    def set_room_name(self, name: str):
        self._room_name = name

    def get_room_name(self):
        return self._room_name

    def start_host(self):
        if self._running:
            return False
        self._is_host = True
        self._player_id = "host_1"
        self._running = True
        self._next_client_id = 2

        self._tcp_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._tcp_server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._tcp_server_socket.settimeout(1.0)
        self._tcp_server_socket.bind(("0.0.0.0", self._tcp_port))
        self._tcp_server_socket.listen(5)

        self._server_thread = threading.Thread(target=self._host_accept_loop, daemon=True)
        self._server_thread.start()

        self._start_udp_broadcast()
        return True

    def start_client(self, host_ip: str):
        if self._running:
            return False
        self._is_client = True
        self._running = True
        self._player_id = "client_temp"

        self._tcp_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._tcp_client_socket.settimeout(self._connect_timeout)
        try:
            self._tcp_client_socket.connect((host_ip, self._tcp_port))
            self._tcp_client_socket.settimeout(0.1)
        except (socket.timeout, ConnectionRefusedError, OSError) as e:
            self._is_client = False
            self._running = False
            self._tcp_client_socket = None
            return False

        self._client_thread = threading.Thread(target=self._client_recv_loop, daemon=True)
        self._client_thread.start()

        return True

    def stop(self):
        self._running = False
        self._is_host = False
        self._is_client = False

        for conn in self._client_connections.values():
            try:
                conn.close()
            except Exception:
                pass
        self._client_connections.clear()
        self._client_addrs.clear()
        self._client_recv_buffers.clear()

        if self._tcp_server_socket:
            try:
                self._tcp_server_socket.close()
            except Exception:
                pass
            self._tcp_server_socket = None

        if self._tcp_client_socket:
            try:
                self._tcp_client_socket.close()
            except Exception:
                pass
            self._tcp_client_socket = None

        if self._udp_socket:
            try:
                self._udp_socket.close()
            except Exception:
                pass
            self._udp_socket = None

        self._recv_queue = queue.Queue()
        self._send_queue = queue.Queue()
        self._discovered_rooms.clear()
        self._client_heartbeats.clear()
        self._player_id = ""
        self._next_client_id = 2

    def _host_accept_loop(self):
        while self._running and self._is_host:
            try:
                conn, addr = self._tcp_server_socket.accept()
                conn.settimeout(0.1)
                client_id = f"player_{self._next_client_id}"
                self._next_client_id += 1
                self._client_connections[client_id] = conn
                self._client_addrs[client_id] = addr
                self._client_recv_buffers[client_id] = b""
                t = threading.Thread(target=self._host_recv_loop, args=(client_id, conn), daemon=True)
                t.start()
            except socket.timeout:
                continue
            except Exception:
                if self._running:
                    time.sleep(0.5)
                continue

    def _host_recv_loop(self, client_id, conn):
        while self._running and client_id in self._client_connections:
            try:
                data = conn.recv(self._buffer_size)
                if not data:
                    break
                self._client_recv_buffers[client_id] += data
                self._parse_buffer(client_id)
            except socket.timeout:
                continue
            except Exception:
                break
        self._handle_client_disconnect(client_id)

    def _parse_buffer(self, client_id):
        buf = self._client_recv_buffers.get(client_id, b"")
        while len(buf) >= SyncManager.HEADER_SIZE:
            magic = struct.unpack("!I", buf[:4])[0]
            if magic != SyncManager.MAGIC:
                idx = buf[4:].find(struct.pack("!I", SyncManager.MAGIC))
                if idx == -1:
                    buf = buf[-3:]
                    break
                else:
                    buf = buf[idx + 4:]
                    continue
            if len(buf) < SyncManager.HEADER_SIZE:
                break
            _, msg_type, payload_len = struct.unpack(SyncManager.HEADER_FMT, buf[:SyncManager.HEADER_SIZE])
            total_len = SyncManager.HEADER_SIZE + payload_len
            if len(buf) < total_len:
                break
            payload_data = buf[SyncManager.HEADER_SIZE:total_len]
            try:
                payload = __import__("json").loads(payload_data.decode("utf-8"))
            except Exception:
                buf = buf[SyncManager.HEADER_SIZE:]
                continue
            self._recv_queue.put({"client_id": client_id, "type": msg_type, "data": payload})
            buf = buf[total_len:]
        self._client_recv_buffers[client_id] = buf

    def _handle_client_disconnect(self, client_id):
        if client_id in self._client_connections:
            try:
                self._client_connections[client_id].close()
            except Exception:
                pass
            del self._client_connections[client_id]
        if client_id in self._client_addrs:
            del self._client_addrs[client_id]
        if client_id in self._client_recv_buffers:
            del self._client_recv_buffers[client_id]
        self._recv_queue.put({"client_id": client_id, "type": MessageTypes.PLAYER_DISCONNECT, "data": {}})

    def _client_recv_loop(self):
        buf = b""
        while self._running and self._is_client:
            try:
                data = self._tcp_client_socket.recv(self._buffer_size)
                if not data:
                    break
                buf += data
                while len(buf) >= SyncManager.HEADER_SIZE:
                    magic = struct.unpack("!I", buf[:4])[0]
                    if magic != SyncManager.MAGIC:
                        idx = buf[4:].find(struct.pack("!I", SyncManager.MAGIC))
                        if idx == -1:
                            buf = buf[-3:]
                            break
                        else:
                            buf = buf[idx + 4:]
                            continue
                    _, msg_type, payload_len = struct.unpack(SyncManager.HEADER_FMT, buf[:SyncManager.HEADER_SIZE])
                    total_len = SyncManager.HEADER_SIZE + payload_len
                    if len(buf) < total_len:
                        break
                    payload_data = buf[SyncManager.HEADER_SIZE:total_len]
                    try:
                        payload = __import__("json").loads(payload_data.decode("utf-8"))
                    except Exception:
                        buf = buf[SyncManager.HEADER_SIZE:]
                        continue
                    self._recv_queue.put({"source": "host", "type": msg_type, "data": payload})
                    buf = buf[total_len:]
            except socket.timeout:
                self._flush_send_queue_client()
                continue
            except Exception:
                break
        self._running = False
        self._recv_queue.put({"source": "host", "type": MessageTypes.PLAYER_DISCONNECT, "data": {}})

    def _flush_send_queue_client(self):
        while not self._send_queue.empty():
            try:
                msg = self._send_queue.get_nowait()
                if msg.get("target") == "host":
                    data = SyncManager.pack_message(msg["type"], msg["data"])
                    self._tcp_client_socket.sendall(data)
            except queue.Empty:
                break
            except Exception:
                pass

    def flush_send_queue(self):
        if self._is_client:
            self._flush_send_queue_client()

    def send_to_player(self, player_id: str, msg_type: int, data: dict):
        if self._is_host and player_id in self._client_connections:
            packet = SyncManager.pack_message(msg_type, data)
            try:
                self._client_connections[player_id].sendall(packet)
            except Exception:
                pass

    def broadcast_to_players(self, msg_type: int, data: dict):
        if self._is_host:
            for pid in list(self._client_connections.keys()):
                self.send_to_player(pid, msg_type, data)

    def send_to_host(self, msg_type: int, data: dict):
        if self._is_client:
            self._send_queue.put({"target": "host", "type": msg_type, "data": data})

    def get_connected_player_ids(self):
        return list(self._client_connections.keys())

    def get_player_count(self):
        return len(self._client_connections)

    def _start_udp_broadcast(self):
        self._udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self._udp_socket.settimeout(0.5)
        self._udp_thread = threading.Thread(target=self._udp_broadcast_loop, daemon=True)
        self._udp_thread.start()

    def _udp_broadcast_loop(self):
        last_broadcast = 0
        while self._running and self._is_host:
            now = time.time()
            if now - last_broadcast >= self._broadcast_interval:
                try:
                    msg = f"{self._response_token}|{self._room_name}|{self.get_player_count()}"
                    self._udp_socket.sendto(msg.encode("utf-8"), ("<broadcast>", self._udp_port))
                    last_broadcast = now
                except Exception:
                    pass
            try:
                data, addr = self._udp_socket.recvfrom(1024)
                msg_text = data.decode("utf-8", errors="ignore")
                if msg_text == self._discover_token:
                    response = f"{self._response_token}|{self._room_name}|{self.get_player_count()}"
                    self._udp_socket.sendto(response.encode("utf-8"), addr)
            except socket.timeout:
                continue
            except Exception:
                continue
            time.sleep(0.1)

    def start_udp_discovery(self):
        if self._udp_socket:
            return
        self._discovered_rooms.clear()
        self._udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self._udp_socket.settimeout(0.5)
        self._udp_thread = threading.Thread(target=self._udp_discover_loop, daemon=True)
        self._udp_thread.start()

    def _udp_discover_loop(self):
        discovery_msg = self._discover_token.encode("utf-8")
        while self._running:
            try:
                self._udp_socket.sendto(discovery_msg, ("<broadcast>", self._udp_port))
            except Exception:
                pass
            try:
                data, addr = self._udp_socket.recvfrom(1024)
                msg = data.decode("utf-8", errors="ignore")
                if msg.startswith(self._response_token):
                    parts = msg.split("|")
                    if len(parts) >= 3:
                        room_name = parts[1]
                        player_count = parts[2]
                        self._discovered_rooms[addr[0]] = {
                            "ip": addr[0],
                            "name": room_name,
                            "players": player_count,
                            "last_seen": time.time(),
                        }
            except socket.timeout:
                pass
            except Exception:
                pass
            self._clean_stale_rooms()
            time.sleep(1.0)

    def _clean_stale_rooms(self):
        now = time.time()
        stale = [ip for ip, info in self._discovered_rooms.items() if now - info["last_seen"] > 10]
        for ip in stale:
            del self._discovered_rooms[ip]

    def stop_udp_discovery(self):
        if self._udp_socket and not self._is_host:
            try:
                self._udp_socket.close()
            except Exception:
                pass
            self._udp_socket = None
        self._discovered_rooms.clear()

    def process_send_queue(self):
        if not self._is_host:
            return
        while not self._send_queue.empty():
            try:
                msg = self._send_queue.get_nowait()
                target = msg.get("target")
                if target and target in self._client_connections:
                    data = SyncManager.pack_message(msg["type"], msg["data"])
                    try:
                        self._client_connections[target].sendall(data)
                    except Exception:
                        pass
            except queue.Empty:
                break
            except Exception:
                pass

    def send_raw_to_client(self, player_id, msg_type, data):
        if self._is_host and player_id in self._client_connections:
            packet = SyncManager.pack_message(msg_type, data)
            try:
                self._client_connections[player_id].sendall(packet)
            except Exception:
                pass

    def send_heartbeat_to_all(self):
        if not self._is_host:
            return
        now = time.time()
        for pid in list(self._client_connections.keys()):
            self.send_raw_to_client(pid, MessageTypes.HEARTBEAT, {"ts": now})
            if pid not in self._client_heartbeats:
                self._client_heartbeats[pid] = now

    def update_heartbeat(self, player_id):
        self._client_heartbeats[player_id] = time.time()

    def check_heartbeat_timeouts(self):
        if not self._is_host:
            return []
        now = time.time()
        timed_out = []
        for pid, last_ts in list(self._client_heartbeats.items()):
            if now - last_ts > self._heartbeat_interval * 2:
                timed_out.append(pid)
        return timed_out



