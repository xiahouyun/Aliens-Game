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

from entity.player import Player
from entity.enemy import Alien
from entity.bullet import Shot
from entity.bomb import Bomb
from entity.explosion import Explosion
from ui.text import UIText
from ui.button import UIButton
from ui.progress_bar import UIProgressBar


class GameScene(IScene, IEventListener):
    """游戏主场景：玩家控制飞船躲避外星人并射击得分"""

    def __init__(self, scene_manager):
        self.scene_manager = scene_manager
        self.running = True
        self.game_over = False

        # 精灵组管理
        self.all_sprites = None      # 所有精灵的容器
        self.aliens = None          # 外星人组
        self.shots = None            # 子弹组
        self.bombs = None            # 炸弹组
        self.lastalien = None        # 最后一个外星人（用于投弹）

        # 游戏对象
        self.player = None           # 玩家飞船
        self.score_text = None       # 分数显示
        self.pause_btn = None        # 暂停按钮
        self.gameover_text = None    # 游戏结束文字
        self.player_health_bar = None  # 玩家血条

        # 计时器：控制外星人生成频率
        self.alienreload = ALIEN_RELOAD

        # 资源
        self.background = None
        self.shoot_sound = None
        self.boom_sound = None

        # 数据管理器
        self._dm = DataManager()

        # 通过接口订阅事件
        self.subscribe_to_events(event_bus)

    def on_event(self, event_type: str, data=None):
        """处理事件总线事件（实现 IEventListener 接口）

        Args:
            event_type: 事件类型
            data: 事件数据
        """
        if event_type == EventTypes.SCORE_CHANGED:
            self._on_score_changed(data)

    def _on_score_changed(self, data):
        """分数变化回调：通过事件总线自动更新UI

        Args:
            data: 事件数据，包含 {"score": int}
        """
        if self.score_text and "score" in data:
            self.score_text.set_text(f"Score: {data['score']}")

    def init(self):
        """初始化游戏：重置分数、创建精灵组、加载资源、生成玩家"""
        # 创建精灵组
        self.all_sprites = pygame.sprite.Group()
        self.aliens = pygame.sprite.Group()
        self.shots = pygame.sprite.Group()
        self.bombs = pygame.sprite.Group()
        self.lastalien = pygame.sprite.GroupSingle()

        # 绑定容器：实体创建时自动加入对应精灵组
        Player.containers = self.all_sprites
        Alien.containers = self.aliens, self.all_sprites, self.lastalien
        Shot.containers = self.shots, self.all_sprites
        Bomb.containers = self.bombs, self.all_sprites
        Explosion.containers = self.all_sprites

        # 加载图片资源
        img = resource_manager.load_image("player1.gif")
        Player.images = [img, pygame.transform.flip(img, True, False)]
        exp_img = resource_manager.load_image("explosion1.gif")
        # 放大爆炸图片，使其更明显
        exp_img = pygame.transform.scale(exp_img, (64, 64))
        Explosion.images = [exp_img, pygame.transform.flip(exp_img, True, True)]
        Alien.images = [resource_manager.load_image(i) for i in ("alien1.gif", "alien2.gif", "alien3.gif")]
        Bomb.images = [resource_manager.load_image("bomb.gif")]
        Shot.images = [resource_manager.load_image("shot.gif")]

        # 平铺背景（横向和纵向都平铺）
        bgdtile = resource_manager.load_image("background.gif")
        self.background = pygame.Surface(SCREENRECT.size)
        for y in range(0, SCREENRECT.height, bgdtile.get_height()):
            for x in range(0, SCREENRECT.width, bgdtile.get_width()):
                self.background.blit(bgdtile, (x, y))

        # 加载音效
        self.boom_sound = resource_manager.load_sound("boom.wav")
        self.shoot_sound = resource_manager.load_sound("car_door.wav")
        if pygame.mixer:
            pygame.mixer.music.load("assets/sounds/house_lo.wav")
            pygame.mixer.music.play(-1)

        # 创建玩家飞船
        self.player = Player()

        # 创建UI
        self.score_text = UIText("score")
        self.score_text.set_position((50, 20))  # 左上角
        
        # 创建玩家血条（显示在玩家上方）
        self.player_health_bar = UIProgressBar(
            x=self.player.rect.centerx - 30, 
            y=self.player.rect.top - 15, 
            width=60, 
            height=8
        )
        self.player_health_bar.set_value(self.player.health)
        
        # 重置游戏状态（必须在设置分数文本之前调用）
        game_stats.reset()
        
        # 设置分数文本（使用重置后的分数）
        self.score_text.set_text(f"Score: {game_stats.score}")

        self.pause_btn = UIButton("pause", callback=self._pause_game)

        self.gameover_text = None
        self.alienreload = ALIEN_RELOAD
        self.game_over = False

    def _pause_game(self):
        """暂停游戏，切换到暂停场景"""
        self.scene_manager.switch_scene("pause")

    def _end_game(self):
        """玩家死亡：停止游戏、保存分数、切换到结束场景"""
        self.game_over = True
        self.player.kill()
        if pygame.mixer:
            pygame.mixer.music.stop()

        # 保存最高分
        self._dm.load_save()
        self._dm.update_high_score(game_stats.score)

        self.scene_manager.reset_scene("over")
        self.scene_manager.switch_scene("over")

    def handle_event(self, event):
        """处理Pygame输入事件（实现 IScene 接口）"""
        # 暂停按钮始终可点击（游戏未结束时）
        if not self.game_over and self.pause_btn:
            self.pause_btn.handle_event(event)

        # 按下 ESC 键切换到暂停场景（游戏未结束时）
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if not self.game_over:
                self._pause_game()

    def update(self):
        """更新游戏逻辑：移动、射击、生成敌人、碰撞检测"""
        if self.game_over:
            # 游戏结束时只更新视觉效果（爆炸动画等）
            self.all_sprites.update()
            return

        self.all_sprites.update()

        # 玩家移动（左右方向键）
        keys = pygame.key.get_pressed()
        dir = keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]
        self.player.move(dir)

        # 射击（空格键）
        fire = keys[pygame.K_SPACE]
        if not self.player.reloading and fire and len(self.shots) < MAX_SHOTS:
            Shot(self.player.gunpos())
            if self.shoot_sound:
                self.shoot_sound.play()
        self.player.reloading = fire

        # 外星人生成（计时器控制）
        if self.alienreload > 0:
            self.alienreload -= 1
        else:
            if AISystem.need_spawn_alien(self.alienreload):
                Alien()
                self.alienreload = AISystem.reset_alien_timer()

        # 炸弹生成（最后一个外星人投放）
        if self.lastalien.sprite and AISystem.need_drop_bomb():
            Bomb(self.lastalien.sprite)

        # 碰撞检测
        self._handle_collisions()

    def _handle_collisions(self):
        """碰撞检测：玩家-外星人、子弹-外星人、玩家-炸弹"""
        # 玩家与外星人碰撞 → 玩家受到当前血量的全部伤害
        for a in CollisionSystem.check_player_alien_collision(self.player, self.aliens):
            if self.boom_sound:
                self.boom_sound.play()
            Explosion(a)
            a.kill()
            self.player.take_damage(self.player.health)  # 造成当前血量的全部伤害
            self.player_health_bar.set_value(self.player.health)  # 更新血条
            if self.player.health <= 0:
                Explosion(self.player)
                self._end_game()
                return

        # 子弹与外星人碰撞 → 减少血量
        collisions = CollisionSystem.check_shot_alien_collision(self.aliens, self.shots)
        for alien, shots in collisions.items():
            for shot in shots:
                alien.take_damage(50)  # 每次击中减少50点血
                shot.kill()  # 销毁子弹
                if alien.health <= 0:
                    if self.boom_sound:
                        self.boom_sound.play()
                    Explosion(alien)
                    alien.kill()
                    game_stats.add_score(1)  # 通过事件总线加分并更新UI
                    self.score_text.set_text(f"Score: {game_stats.score}")  # 手动更新UI

        # 玩家与炸弹碰撞 → 减少20点血
        for b in CollisionSystem.check_player_bomb_collision(self.player, self.bombs):
            if self.boom_sound:
                self.boom_sound.play()
            self.player.take_damage(20)  # 炸弹造成20点伤害
            self.player_health_bar.set_value(self.player.health)  # 更新血条
            Explosion(b)
            b.kill()
            if self.player.health <= 0:
                Explosion(self.player)
                self._end_game()
                return

    def draw(self, screen):
        """绘制游戏画面"""
        screen.blit(self.background, (0, 0))
        self.all_sprites.draw(screen)

        # 绘制外星人血条
        for alien in self.aliens:
            # 血条显示在外星人上方
            bar_width = alien.rect.width
            bar_height = 4
            bar_x = alien.rect.left
            bar_y = alien.rect.top - 10
            # 背景
            pygame.draw.rect(screen, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height))
            # 填充
            fill_width = bar_width * alien.health / alien.max_health
            pygame.draw.rect(screen, (255, 0, 0), (bar_x, bar_y, fill_width, bar_height))
            # 边框
            pygame.draw.rect(screen, (255, 255, 255), (bar_x, bar_y, bar_width, bar_height), 1)

        # UI层（分数、按钮）
        if self.score_text:
            self.score_text.draw(screen)
        # 绘制玩家血条（跟随玩家移动）
        if self.player_health_bar and self.player:
            self.player_health_bar.rect.x = self.player.rect.centerx - 30
            self.player_health_bar.rect.y = self.player.rect.top - 15
            self.player_health_bar.draw(screen)
        if self.pause_btn and not self.game_over:
            self.pause_btn.draw(screen)
        if self.gameover_text:
            self.gameover_text.draw(screen)

        pygame.display.flip()

    def is_running(self):
        """返回游戏是否继续运行"""
        return self.running