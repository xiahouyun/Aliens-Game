import time
import pygame
from interfaces.i_scene import IScene
from interfaces.i_event_listener import IEventListener
import core.constants as const
from core.constants import SCREENRECT, FPS, MAX_SHOTS, ALIEN_ODDS, BOMB_ODDS, ALIEN_RELOAD
from core.resource_manager import resource_manager
from core.collision_system import CollisionSystem
from core.ai_system import AISystem
from core.data_manager import DataManager
from core.event_bus import event_bus, EventTypes
from core.game_stats import game_stats
from core.network_manager import NetworkManager
from core.host_manager import HostManager
from core.sync_manager import SyncManager, MessageTypes

from entity.player import Player
from entity.enemy import Alien
from entity.bullet import Shot
from entity.bomb import Bomb
from entity.explosion import Explosion
from entity.remote_player import RemotePlayer
from ui.text import UIText
from ui.button import UIButton
from ui.progress_bar import UIProgressBar


class GameScene(IScene, IEventListener):
    MODE_SINGLE = "single"
    MODE_MULTI_HOST = "multi_host"
    MODE_MULTI_CLIENT = "multi_client"

    def __init__(self, scene_manager):
        self.scene_manager = scene_manager
        self.running = True
        self.game_over = False

        self.all_sprites = None
        self.aliens = None
        self.shots = None
        self.bombs = None
        self.lastalien = None

        self.player = None
        self.score_text = None
        self.pause_btn = None
        self.gameover_text = None
        self.player_health_bar = None

        self.alienreload = ALIEN_RELOAD

        self.background = None
        self.shoot_sound = None
        self.boom_sound = None

        self._dm = DataManager()

        self._mode = self.MODE_SINGLE
        self._nm = NetworkManager()
        self._host_mgr = None

        self.remote_players = {}
        self._remote_player_sprites = {}
        self._sync_timer = 0
        self._sync_interval = 2

        self._remote_state = {}
        self._local_input_state = {"direction": 0, "shooting": False}
        self._music_playing = False

        self.subscribe_to_events(event_bus)

    def on_event(self, event_type: str, data=None):
        if event_type == EventTypes.SCORE_CHANGED:
            self._on_score_changed(data)

    def _on_score_changed(self, data):
        if self.score_text and "score" in data:
            self.score_text.set_text(f"Score: {data['score']}")

    def init(self):
        self.all_sprites = pygame.sprite.Group()
        self.aliens = pygame.sprite.Group()
        self.shots = pygame.sprite.Group()
        self.bombs = pygame.sprite.Group()
        self.lastalien = pygame.sprite.GroupSingle()

        Player.containers = self.all_sprites
        Alien.containers = self.aliens, self.all_sprites, self.lastalien
        Shot.containers = self.shots, self.all_sprites
        Bomb.containers = self.bombs, self.all_sprites
        Explosion.containers = self.all_sprites

        self._setup_mode()

        RemotePlayer.containers = self.all_sprites
        img = resource_manager.load_image("player1.gif")
        RemotePlayer.images = [img, pygame.transform.flip(img, True, False)]
        Player.images = [img, pygame.transform.flip(img, True, False)]

        exp_img = resource_manager.load_image("explosion1.gif")
        exp_img = pygame.transform.scale(exp_img, (64, 64))
        Explosion.images = [exp_img, pygame.transform.flip(exp_img, True, True)]
        Alien.images = [resource_manager.load_image(i) for i in ("alien1.gif", "alien2.gif", "alien3.gif")]
        Bomb.images = [resource_manager.load_image("bomb.gif")]
        Shot.images = [resource_manager.load_image("shot.gif")]

        bgdtile = resource_manager.load_image("background.gif")
        self.background = pygame.Surface(SCREENRECT.size)
        for y in range(0, SCREENRECT.height, bgdtile.get_height()):
            for x in range(0, SCREENRECT.width, bgdtile.get_width()):
                self.background.blit(bgdtile, (x, y))

        self.boom_sound = resource_manager.load_sound("boom.wav")
        self.shoot_sound = resource_manager.load_sound("car_door.wav")
        if pygame.mixer:
            pygame.mixer.music.load("assets/sounds/house_lo.wav")
            pygame.mixer.music.play(-1)
        self._music_playing = True

        self.player = self._create_local_player()

        self.score_text = UIText("score")
        self.score_text.set_position((50, 20))

        self.player_health_bar = UIProgressBar(
            x=self.player.rect.centerx - 30,
            y=self.player.rect.top - 15,
            width=60,
            height=8
        )
        self.player_health_bar.set_value(self.player.health)

        game_stats.reset()
        self.score_text.set_text(f"Score: {game_stats.score}")

        self.pause_btn = UIButton("pause", callback=self._pause_game)

        self.gameover_text = None
        self.alienreload = ALIEN_RELOAD
        self.game_over = False

        self.remote_players = {}
        self._remote_player_sprites = {}
        self._sync_timer = 0
        self._local_input_state = {"direction": 0, "shooting": False}
        self._player_speed = self._dm.get_config("game.json", "entity.player.speed")

    def _setup_mode(self):
        if self._nm.is_host:
            self._mode = self.MODE_MULTI_HOST
            self._host_mgr = HostManager(self._nm)
            self._host_mgr.state = HostManager.STATE_PLAYING
        elif self._nm.is_client:
            self._mode = self.MODE_MULTI_CLIENT
            self._host_mgr = None
        else:
            self._mode = self.MODE_SINGLE
            self._host_mgr = None

    def _pause_game(self):
        if self._mode != self.MODE_SINGLE:
            self._end_game()
        else:
            if pygame.mixer:
                pygame.mixer.music.stop()
            self._music_playing = False
            self.scene_manager.switch_scene("pause")

    def _end_game(self):
        self.game_over = True
        self.player.kill()
        if pygame.mixer:
            pygame.mixer.music.stop()
        self._music_playing = False

        self._dm.load_save()
        self._dm.update_high_score(game_stats.score)

        if self._mode == self.MODE_MULTI_HOST and self._host_mgr:
            scores = {"host_1": game_stats.score}
            for pid, sprite in self._remote_player_sprites.items():
                scores[pid] = sprite.score
            self._host_mgr.broadcast_game_over(scores)
            self._nm.stop()
            self._mode = self.MODE_SINGLE

        if self._mode == self.MODE_MULTI_CLIENT:
            self._nm.send_to_host(MessageTypes.GAME_OVER, {"score": game_stats.score})
            self._nm.stop()
            self._mode = self.MODE_SINGLE

        self.scene_manager.reset_scene("over")
        self.scene_manager.switch_scene("over")

    def handle_event(self, event):
        if not self.game_over and self.pause_btn:
            self.pause_btn.handle_event(event)

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if not self.game_over:
                if self._mode == self.MODE_SINGLE:
                    self._pause_game()
                else:
                    self._end_game()

    def update(self):
        if not self._music_playing and not self.game_over:
            if pygame.mixer and not pygame.mixer.music.get_busy():
                pygame.mixer.music.load("assets/sounds/house_lo.wav")
                pygame.mixer.music.play(-1)
            self._music_playing = True

        self._process_network_messages()

        if self.game_over:
            self.all_sprites.update()
            return

        if self._mode == self.MODE_MULTI_CLIENT:
            self._update_client()
            return

        self._update_host_or_single()

        if self._mode == self.MODE_MULTI_HOST:
            self._sync_timer += 1
            if self._sync_timer >= self._sync_interval:
                self._sync_timer = 0
                self._sync_game_state_to_clients()
            self._nm.process_send_queue()
            now = time.time()
            if not hasattr(self, '_last_heartbeat'):
                self._last_heartbeat = now
            if now - self._last_heartbeat >= 3.0:
                self._last_heartbeat = now
                self._nm.send_heartbeat_to_all()
                timed_out = self._nm.check_heartbeat_timeouts()
                for pid in timed_out:
                    self._remove_remote_player_sprite(pid)
                    if self._host_mgr:
                        self._host_mgr.remove_player(pid)

        if self._mode == self.MODE_MULTI_CLIENT:
            self._nm.flush_send_queue()

    def _update_host_or_single(self):
        self.all_sprites.update()

        keys = pygame.key.get_pressed()
        dir = keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]
        self.player.move(dir)
        self._local_input_state["direction"] = dir

        fire = keys[pygame.K_SPACE]
        if not self.player.reloading and fire and len(self.shots) < MAX_SHOTS:
            Shot(self.player.gunpos())
            if self.shoot_sound:
                self.shoot_sound.play()
        self.player.reloading = fire
        self._local_input_state["shooting"] = bool(fire)

        if self.alienreload > 0:
            self.alienreload -= 1
        else:
            if AISystem.need_spawn_alien(self.alienreload):
                Alien()
                self.alienreload = AISystem.reset_alien_timer()

        if self.lastalien.sprite and AISystem.need_drop_bomb():
            Bomb(self.lastalien.sprite)

        self._handle_collisions()

    def _update_client(self):
        keys = pygame.key.get_pressed()
        dir = keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]
        shooting = keys[pygame.K_SPACE]

        # 本地预测：立即响应玩家操作
        self.player.move(dir)
        if not self.player.reloading and shooting and len(self.shots) < MAX_SHOTS:
            Shot(self.player.gunpos())
        self.player.reloading = bool(shooting)

        if dir != self._local_input_state["direction"] or shooting != self._local_input_state.get("shooting", False):
            self._local_input_state["direction"] = dir
            self._local_input_state["shooting"] = shooting
            input_data = SyncManager.build_player_input(self._nm.player_id, self._local_input_state)
            self._nm.send_to_host(MessageTypes.PLAYER_INPUT, input_data)

        self.all_sprites.update()

    def _handle_collisions(self):
        for a in CollisionSystem.check_player_alien_collision(self.player, self.aliens):
            if self.boom_sound:
                self.boom_sound.play()
            Explosion(a)
            a.kill()
            self.player.take_damage(self.player.health)
            self.player_health_bar.set_value(self.player.health)
            if self.player.health <= 0:
                Explosion(self.player)
                self._end_game()
                return

        collisions = CollisionSystem.check_shot_alien_collision(self.aliens, self.shots)
        for alien, shots in collisions.items():
            for shot in shots:
                alien.take_damage(50)
                shot.kill()
                if alien.health <= 0:
                    if self.boom_sound:
                        self.boom_sound.play()
                    Explosion(alien)
                    alien.kill()
                    game_stats.add_score(1)
                    self.score_text.set_text(f"Score: {game_stats.score}")

        for b in CollisionSystem.check_player_bomb_collision(self.player, self.bombs):
            if self.boom_sound:
                self.boom_sound.play()
            self.player.take_damage(20)
            self.player_health_bar.set_value(self.player.health)
            Explosion(b)
            b.kill()
            if self.player.health <= 0:
                Explosion(self.player)
                self._end_game()
                return

    def _process_network_messages(self):
        if self._mode == self.MODE_SINGLE:
            return

        while not self._nm.recv_queue.empty():
            try:
                msg = self._nm.recv_queue.get_nowait()
                msg_type = msg["type"]
                data = msg.get("data", {})

                if self._mode == self.MODE_MULTI_HOST:
                    if msg_type == MessageTypes.HEARTBEAT:
                        player_id = msg.get("client_id", "")
                        self._nm.update_heartbeat(player_id)
                    elif msg_type == MessageTypes.PLAYER_INPUT:
                        player_id = msg.get("client_id", data.get("player_id", ""))
                        if self._host_mgr:
                            self._host_mgr.update_player_state(player_id, data)
                            if player_id not in self._remote_player_sprites:
                                self._create_remote_player_sprite(player_id)
                            sprite = self._remote_player_sprites.get(player_id)
                            if sprite:
                                direction = data.get("direction", 0)
                                sprite.move(direction, self._player_speed)
                                if data.get("shooting", False) and not sprite.reloading and len(self.shots) < MAX_SHOTS:
                                    Shot((sprite.rect.centerx, sprite.rect.top))
                                sprite.reloading = data.get("shooting", False)
                    elif msg_type == MessageTypes.PLAYER_DISCONNECT:
                        client_id = msg.get("client_id", "")
                        if self._host_mgr:
                            self._host_mgr.remove_player(client_id)
                        self._remove_remote_player_sprite(client_id)
                    elif msg_type == MessageTypes.GAME_OVER:
                        client_id = msg.get("client_id", "")
                        if self._host_mgr:
                            self._host_mgr.remove_player(client_id)
                        self._remove_remote_player_sprite(client_id)

                elif self._mode == self.MODE_MULTI_CLIENT:
                    if msg_type == MessageTypes.HEARTBEAT:
                        self._nm.send_to_host(MessageTypes.HEARTBEAT, {"ts": data.get("ts", 0)})
                    elif msg_type == MessageTypes.GAME_STATE_SYNC:
                        self._remote_state = data
                        self._apply_remote_game_state(data)
                    elif msg_type == MessageTypes.GAME_OVER:
                        self._end_game()

            except Exception:
                pass

    def _create_local_player(self):
        spawn_pos = None
        if self._mode in (self.MODE_MULTI_HOST, self.MODE_MULTI_CLIENT):
            pid = self._nm.player_id
            spawn_pos = self._nm.spawn_positions.get(pid)
        return Player(spawn_pos)

    def _create_remote_player_sprite(self, player_id: str):
        if player_id not in self._remote_player_sprites:
            spawn_pos = self._nm.spawn_positions.get(player_id, (SCREENRECT.width // 2, SCREENRECT.height))
            sprite = RemotePlayer(player_id, x=spawn_pos[0], y=spawn_pos[1])
            self._remote_player_sprites[player_id] = sprite
            self.remote_players[player_id] = {"x": spawn_pos[0], "y": spawn_pos[1], "health": 100}

    def _remove_remote_player_sprite(self, player_id: str):
        sprite = self._remote_player_sprites.pop(player_id, None)
        if sprite:
            sprite.kill()
        self.remote_players.pop(player_id, None)

    def _apply_remote_game_state(self, data: dict):
        host_data = data.get("host", {})
        if host_data:
            if "host_1" not in self._remote_player_sprites:
                spawn_pos = self._nm.spawn_positions.get("host_1", (SCREENRECT.width // 2, SCREENRECT.height))
                sprite = RemotePlayer("host_1", x=spawn_pos[0], y=spawn_pos[1])
                self._remote_player_sprites["host_1"] = sprite
                self.remote_players["host_1"] = {"x": spawn_pos[0], "y": spawn_pos[1], "health": 100}
            self._remote_player_sprites["host_1"].update_from_state(host_data)

        remotes = data.get("remotes", {})
        my_pid = self._nm.player_id
        known_remote_ids = set(self._remote_player_sprites.keys())
        synced_ids = set()
        for pid, state in remotes.items():
            if pid == my_pid:
                if self.player:
                    self.player.rect.x = state.get("x", self.player.rect.x)
                    self.player.rect.y = state.get("y", self.player.rect.y)
                    self.player.health = state.get("health", self.player.health)
                    self.player.facing = state.get("facing", self.player.facing)
                    game_stats.score = state.get("score", game_stats.score)
                    self.score_text.set_text(f"Score: {game_stats.score}")
                    self.player_health_bar.set_value(self.player.health)
                    if self.player.images:
                        self.player.image = self.player.images[0] if self.player.facing < 0 else self.player.images[1]
                continue
            synced_ids.add(pid)
            if pid not in self._remote_player_sprites:
                self._create_remote_player_sprite(pid)
            sprite = self._remote_player_sprites.get(pid)
            if sprite:
                sprite.update_from_state(state)
        for pid in known_remote_ids - synced_ids:
            if pid != "host_1":
                self._remove_remote_player_sprite(pid)

        enemies = data.get("enemies", [])
        self._sync_remote_enemies(enemies)

        shots = data.get("shots", [])
        self._sync_remote_shots(shots)

        bombs = data.get("bombs", [])
        self._sync_remote_bombs(bombs)

        explosions = data.get("explosions", [])
        self._sync_remote_explosions(explosions)

    def _sync_remote_enemies(self, enemies_data):
        for a in list(self.aliens):
            a.kill()
        for ed in enemies_data:
            alien = Alien()
            alien.rect.x = ed.get("x", 0)
            alien.rect.y = ed.get("y", 0)
            alien.health = ed.get("health", alien.max_health)

    def _sync_remote_shots(self, shots_data):
        existing = list(self.shots)
        n = min(len(existing), len(shots_data))
        for i in range(n):
            existing[i].rect.x = shots_data[i].get("x", existing[i].rect.x)
            existing[i].rect.y = shots_data[i].get("y", existing[i].rect.y)
        if len(shots_data) < len(existing):
            for s in existing[len(shots_data):]:
                s.kill()
        elif len(shots_data) > len(existing):
            for sd in shots_data[len(existing):]:
                Shot((sd.get("x", 0), sd.get("y", 0)))

    def _sync_remote_bombs(self, bombs_data):
        existing = list(self.bombs)
        n = min(len(existing), len(bombs_data))
        for i in range(n):
            existing[i].rect.x = bombs_data[i].get("x", existing[i].rect.x)
            existing[i].rect.y = bombs_data[i].get("y", existing[i].rect.y)
        if len(bombs_data) < len(existing):
            for b in existing[len(bombs_data):]:
                b.kill()
        elif len(bombs_data) > len(existing):
            for bd in bombs_data[len(existing):]:
                Bomb.from_pos(bd.get("x", 0), bd.get("y", 0))

    def _sync_remote_explosions(self, explosions_data):
        for ed in explosions_data:
            try:
                Explosion.from_pos(ed.get("x", 0), ed.get("y", 0))
            except Exception:
                pass

    def _sync_game_state_to_clients(self):
        enemies = [{"x": a.rect.x, "y": a.rect.y, "health": a.health}
                    for a in self.aliens if a.alive()]
        shots = [{"x": s.rect.x, "y": s.rect.y} for s in self.shots if s.alive()]
        bombs = [{"x": b.rect.x, "y": b.rect.y} for b in self.bombs if b.alive()]
        explosions = [{"x": e.rect.x, "y": e.rect.y, "life": getattr(e, "life", 0)}
                       for e in self.all_sprites if isinstance(e, Explosion)]

        host_stats = {
            "x": self.player.rect.x,
            "y": self.player.rect.y,
            "health": self.player.health,
            "facing": self.player.facing,
            "score": game_stats.score,
            "shooting": self.player.reloading,
            "enemies": enemies,
            "shots": shots,
            "bombs": bombs,
            "explosions": explosions,
        }

        remote_states = {}
        for pid, sprite in self._remote_player_sprites.items():
            remote_states[pid] = {
                "x": sprite.rect.x,
                "y": sprite.rect.y,
                "health": sprite.health,
                "facing": sprite.facing,
                "score": sprite.score,
                "shooting": sprite.shooting,
            }

        state_msg = SyncManager.build_game_state(host_stats, remote_states)
        self._nm.broadcast_to_players(MessageTypes.GAME_STATE_SYNC, state_msg)

    def draw(self, screen):
        screen.blit(self.background, (0, 0))
        self.all_sprites.draw(screen)

        for alien in self.aliens:
            bar_width = alien.rect.width
            bar_height = 4
            bar_x = alien.rect.left
            bar_y = alien.rect.top - 10
            pygame.draw.rect(screen, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height))
            fill_width = bar_width * alien.health / alien.max_health
            pygame.draw.rect(screen, (255, 0, 0), (bar_x, bar_y, fill_width, bar_height))
            pygame.draw.rect(screen, (255, 255, 255), (bar_x, bar_y, bar_width, bar_height), 1)

        if self.score_text:
            self.score_text.draw(screen)
        if self.player_health_bar and self.player:
            self.player_health_bar.rect.x = self.player.rect.centerx - 30
            self.player_health_bar.rect.y = self.player.rect.top - 15
            self.player_health_bar.draw(screen)
        if self.pause_btn and not self.game_over:
            self.pause_btn.draw(screen)
        if self.gameover_text:
            self.gameover_text.draw(screen)

        for pid, sprite in self._remote_player_sprites.items():
            if sprite.alive():
                bar_width = 32
                bar_height = 4
                bar_x = sprite.rect.left
                bar_y = sprite.rect.top - 10
                pygame.draw.rect(screen, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height))
                fill_width = bar_width * sprite.health / sprite.max_health
                pygame.draw.rect(screen, (0, 255, 0), (bar_x, bar_y, fill_width, bar_height))
                pygame.draw.rect(screen, (255, 255, 255), (bar_x, bar_y, bar_width, bar_height), 1)

        pygame.display.flip()

    def is_running(self):
        return self.running
