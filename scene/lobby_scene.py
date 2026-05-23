import pygame
from interfaces.i_scene import IScene
from core.network_manager import NetworkManager
from core.host_manager import HostManager
from core.sync_manager import SyncManager, MessageTypes
from ui.text import UIText
from ui.button import UIButton
from ui.panel import UIPanel
from ui.player_list import UIPlayerList


class LobbyScene(IScene):
    def __init__(self, scene_manager):
        self.scene_manager = scene_manager
        self.ui_elements = []
        self._nm = NetworkManager()
        self._host_mgr = None
        self._mode = None
        self._title_text = None
        self._status_text = None
        self._player_list = None
        self._room_list_text = None
        self._selected_room_ip = None
        self._ready_btn = None
        self._start_btn = None
        self._back_btn = None
        self._create_btn = None
        self._join_btn = None
        self._refresh_btn = None
        self._my_ready = False
        self._lobby_state = {}
        self._discovery_timer = 0
        self._discovering = False
        self._refresh_timer = 0
        self._room_lines = []
        self._small_font = None

    def init(self):
        self._nm = NetworkManager()
        self._host_mgr = None
        self._my_ready = False
        self._lobby_state = {}
        self._discovery_timer = 0
        self._discovering = False
        self._refresh_timer = 0
        self._room_lines = []
        self._selected_room_ip = None

        from core.data_manager import DataManager
        dm = DataManager()
        dm.load_config("game.json")
        font_path = dm.get_config("game.json", "ui.font_path")
        font_size = dm.get_config("game.json", "ui.font_size")
        self._small_font = pygame.font.Font(font_path, 18)

        self._title_text = UIText("score")
        self._title_text.set_text("联机大厅")
        self._title_text.rect.center = (640, 40)

        self._status_text = UIText("score")
        self._status_text.set_text("请选择模式")
        self._status_text.set_position((640, 100))

        self._create_btn = UIButton("start", callback=self._do_create_room)
        self._create_btn.text_surf = self._create_btn.font.render("创建房间", True, (255, 255, 255))
        self._create_btn.rect.center = (520, 200)

        self._join_btn = UIButton("multiplayer", callback=self._do_show_rooms)
        self._join_btn.text_surf = self._join_btn.font.render("加入房间", True, (255, 255, 255))
        self._join_btn.rect.center = (760, 200)

        self._back_btn = UIButton("back", callback=self._do_back)
        self._back_btn.rect.center = (640, 430)

        self._ready_btn = None
        self._start_btn = None
        self._refresh_btn = None
        self._player_list = None
        self._room_list_text = None

        self._refresh_mode_selection()

    def _refresh_mode_selection(self):
        self._mode = None
        self._title_text.set_text("联机大厅")
        self._status_text.set_text("请选择模式")
        self._status_text.set_position((640, 100))
        self._create_btn.rect.center = (520, 200)
        self._join_btn.rect.center = (760, 200)
        self._ready_btn = None
        self._start_btn = None
        self._refresh_btn = None
        self._player_list = None
        self._room_list_text = None
        self._back_btn = UIButton("back", callback=self._do_back)
        self._back_btn.rect.center = (640, 430)
        self.ui_elements = [self._title_text, self._status_text,
                           self._create_btn, self._join_btn, self._back_btn]

    def _do_create_room(self):
        self._mode = "host"
        success = self._nm.start_host()
        if not success:
            self._status_text.set_text("创建房间失败")
            return
        self._host_mgr = HostManager(self._nm)
        self._title_text.set_text("等待玩家加入")
        self._status_text.set_text("房间已创建，等待玩家...")
        self._status_text.set_position((640, 90))
        self._player_list = UIPlayerList(490, 130)
        self._refresh_host_ui()

    def _refresh_host_ui(self):
        self._ready_btn = UIButton("resume", callback=self._do_toggle_ready)
        self._ready_btn.text_surf = self._ready_btn.font.render("准备", True, (255, 255, 255))
        self._ready_btn.rect.center = (760, 330)

        self._start_btn = UIButton("start", callback=self._do_start_game)
        self._start_btn.text_surf = self._start_btn.font.render("开始游戏", True, (255, 255, 255))
        self._start_btn.rect.center = (520, 330)

        self._back_btn = UIButton("back_to_lobby", callback=self._do_leave_room)

        self.ui_elements = [self._title_text, self._status_text, self._player_list,
                           self._ready_btn, self._start_btn, self._back_btn]

    def _do_toggle_ready(self):
        self._my_ready = not self._my_ready
        if self._mode == "host":
            self._host_mgr.set_player_ready("host_1", self._my_ready)
            self._host_mgr.broadcast_lobby_state()
            self._ready_btn.text_surf = self._ready_btn.font.render(
                "取消准备" if self._my_ready else "准备", True, (255, 255, 255))
        elif self._mode == "client":
            self._nm.send_to_host(MessageTypes.PLAYER_READY, {"ready": self._my_ready})
            self._ready_btn.text_surf = self._ready_btn.font.render(
                "取消准备" if self._my_ready else "准备", True, (255, 255, 255))

    def _do_start_game(self):
        if not self._host_mgr:
            return
        if not self._host_mgr.is_ready_to_start():
            self._status_text.set_text("等待所有玩家准备...")
            return
        self._host_mgr.state = HostManager.STATE_COUNTDOWN
        self._host_mgr.start_countdown()
        self._host_mgr.broadcast_game_start()

    def _do_show_rooms(self):
        self._mode = "discovering"
        self._discovering = True
        self._room_lines = []
        self._nm.start_udp_discovery()
        self._room_list_text = UIText("score")
        self._room_list_text.set_text("搜索房间中...")
        self._room_list_text.set_position((640, 200))
        self._refresh_btn = UIButton("resume", callback=self._do_refresh_rooms)
        self._refresh_btn.text_surf = self._refresh_btn.font.render("刷新", True, (255, 255, 255))
        self._refresh_btn.rect.center = (640, 350)
        self._back_btn = UIButton("back_to_lobby", callback=self._do_leave_room)
        self.ui_elements = [self._title_text, self._status_text, self._room_list_text,
                           self._refresh_btn, self._back_btn]

    def _do_refresh_rooms(self):
        self._discovering = True
        self._nm.start_udp_discovery()
        self._room_list_text.set_text("搜索房间中...")

    def _do_join_room(self, ip: str):
        self._selected_room_ip = ip
        self._mode = "client"
        self._nm.stop_udp_discovery()
        self._discovering = False
        success = self._nm.start_client(ip)
        if not success:
            self._status_text.set_text("连接房间失败")
            self._mode = None
            return
        self._nm.send_to_host(MessageTypes.JOIN_REQUEST, {"player_name": self._nm.player_id})
        self._nm.flush_send_queue()
        self._title_text.set_text("已加入房间")
        self._status_text.set_text("连接成功，等待开始...")
        self._status_text.set_position((640, 90))
        self._player_list = UIPlayerList(490, 130)
        self._ready_btn = UIButton("resume", callback=self._do_toggle_ready)
        self._ready_btn.text_surf = self._ready_btn.font.render("准备", True, (255, 255, 255))
        self._ready_btn.rect.center = (640, 330)
        self._room_list_text = None
        self._refresh_btn = None
        self._back_btn = UIButton("back_to_lobby", callback=self._do_leave_room)
        self.ui_elements = [self._title_text, self._status_text, self._player_list,
                           self._ready_btn, self._back_btn]

    def _do_back(self):
        self._nm.stop()
        self._nm.stop_udp_discovery()
        self._host_mgr = None
        self._discovering = False
        self._my_ready = False
        self.scene_manager.reset_scene("start")
        self.scene_manager.switch_scene("start")

    def _do_leave_room(self):
        self._nm.stop()
        self._host_mgr = None
        self._discovering = False
        self._my_ready = False
        self._refresh_mode_selection()

    def handle_event(self, event: pygame.event.Event):
        if self._mode == "discovering" and hasattr(self, '_room_list_text') and self._room_list_text:
            if event.type == pygame.KEYDOWN:
                rooms = list(self._nm.discovered_rooms.values())
                if rooms:
                    if event.key == pygame.K_1 and len(rooms) >= 1:
                        self._do_join_room(rooms[0]["ip"])
                        return
                    elif event.key == pygame.K_2 and len(rooms) >= 2:
                        self._do_join_room(rooms[1]["ip"])
                        return
                    elif event.key == pygame.K_3 and len(rooms) >= 3:
                        self._do_join_room(rooms[2]["ip"])
                        return

        for elem in self.ui_elements:
            if hasattr(elem, "handle_event"):
                elem.handle_event(event)

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if self._mode in ("host", "client"):
                self._do_leave_room()
            else:
                self._do_back()

    def _process_network_messages(self):
        while not self._nm.recv_queue.empty():
            try:
                msg = self._nm.recv_queue.get_nowait()
                msg_type = msg["type"]
                data = msg.get("data", {})

                if msg_type == MessageTypes.JOIN_REQUEST:
                    client_id = msg.get("client_id", "")
                    if self._host_mgr:
                        if self._host_mgr.add_player(client_id):
                            self._nm.send_raw_to_client(client_id, MessageTypes.JOIN_ACCEPT,
                                                         {"player_id": client_id})
                            self._host_mgr.broadcast_lobby_state()
                            self._update_player_list_display()
                        else:
                            self._nm.send_raw_to_client(client_id, MessageTypes.JOIN_REJECT,
                                                         {"reason": "房间已满"})

                elif msg_type == MessageTypes.HEARTBEAT:
                    if self._mode == "host":
                        self._nm.update_heartbeat(client_id)
                    elif self._mode == "client":
                        self._nm.send_to_host(MessageTypes.HEARTBEAT, {"ts": data.get("ts", 0)})

                elif msg_type == MessageTypes.PLAYER_READY:
                    client_id = msg.get("client_id", "")
                    if self._host_mgr:
                        ready = data.get("ready", False)
                        self._host_mgr.set_player_ready(client_id, ready)
                        self._host_mgr.broadcast_lobby_state()
                        self._update_player_list_display()

                elif msg_type == MessageTypes.LOBBY_STATE:
                    self._lobby_state = data
                    self._update_player_list_display()
                    if data.get("state") == HostManager.STATE_PLAYING:
                        self._start_multiplayer_game(data.get("players", []))

                elif msg_type == MessageTypes.JOIN_ACCEPT:
                    self._nm.set_player_id(data.get("player_id", "client_temp"))
                    self._status_text.set_text(f"已加入: {self._nm.player_id}")

                elif msg_type == MessageTypes.JOIN_REJECT:
                    self._status_text.set_text(data.get("reason", "加入被拒绝"))
                    self._mode = None

                elif msg_type == MessageTypes.GAME_START:
                    player_ids = data.get("players", [])
                    spawn_data = data.get("spawn_positions", {})
                    self._nm.spawn_positions = {pid: (info["x"], info["y"]) for pid, info in spawn_data.items()}
                    self._start_multiplayer_game(player_ids)

                elif msg_type == MessageTypes.GAME_OVER:
                    scores = data.get("scores", {})
                    self._handle_game_over(scores)

                elif msg_type == MessageTypes.PLAYER_DISCONNECT:
                    client_id = msg.get("client_id", "")
                    if self._host_mgr:
                        self._host_mgr.remove_player(client_id)
                        self._host_mgr.broadcast_lobby_state()
                    self._update_player_list_display()

            except Exception:
                pass

    def _update_player_list_display(self):
        if not self._player_list:
            return
        if self._mode == "host" and self._host_mgr:
            players = {"host_1 (你)": self._my_ready}
            for pid in self._host_mgr.players:
                players[pid] = self._host_mgr._player_ready.get(pid, False)
            self._player_list.set_players(players)
            count = self._host_mgr.player_count
            self._status_text.set_text(f"玩家: {count}/3")
        elif self._mode == "client" and self._lobby_state:
            players = {}
            for pid in self._lobby_state.get("players", []):
                ready = self._lobby_state.get("ready", {}).get(pid, False)
                if pid == self._nm.player_id:
                    players[pid] = self._my_ready
                else:
                    players[pid] = ready
            self._player_list.set_players(players)

    def _start_multiplayer_game(self, player_ids: list):
        self.scene_manager.reset_scene("game")
        self.scene_manager.switch_scene("game")

    def _handle_game_over(self, scores: dict):
        self.scene_manager.reset_scene("over")
        self.scene_manager.switch_scene("over")

    def update(self):
        for elem in self.ui_elements:
            elem.update()

        self._process_network_messages()

        if self._host_mgr:
            self._host_mgr.update_countdown()
            if self._host_mgr._state == HostManager.STATE_PLAYING:
                from core.constants import SCREENRECT
                spawn_positions = self._host_mgr.compute_spawn_positions(SCREENRECT.width, SCREENRECT.height)
                self._nm.spawn_positions = spawn_positions
                self._start_multiplayer_game([])

        if self._mode == "discovering" and self._discovering and self._room_list_text:
            self._refresh_timer += 1
            if self._refresh_timer > 60:
                self._refresh_timer = 0
                rooms = list(self._nm.discovered_rooms.values())
                if rooms:
                    self._room_lines = ["找到以下房间 (按数字键加入):"]
                    for i, r in enumerate(rooms[:3]):
                        self._room_lines.append(f"[{i + 1}] {r['name']} ({r['players']}人)")
                    self._room_list_text.set_text(self._room_lines[0])
                else:
                    self._room_list_text.set_text("未发现房间，请重试")
                    self._room_lines = []

    def draw(self, screen: pygame.Surface):
        screen.fill((0, 0, 0))
        for elem in self.ui_elements:
            elem.draw(screen)

        if self._mode == "discovering" and hasattr(self, '_room_lines') and self._room_lines:
            y = 220
            for line in self._room_lines[1:]:
                surf = self._small_font.render(line, True, (200, 200, 200))
                screen.blit(surf, (440, y))
                y += 24

        if self._mode == "discovering":
            hint = self._small_font.render("按 1/2/3 选择房间加入，ESC 返回", True, (150, 150, 150))
            screen.blit(hint, (470, 280))

        pygame.display.flip()
