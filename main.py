import pygame
from core.constants import SCREENRECT, FPS, WINDOW_CAPTION
from core.data_manager import DataManager
from core.scene_manager import SceneManager
from scene.start_scene import StartScene
from scene.game_scene import GameScene
from scene.pause_scene import PauseScene
from scene.over_scene import OverScene
from scene.lobby_scene import LobbyScene


def main():
    pygame.mixer.pre_init(44100, 32, 2, 1024)
    pygame.init()

    # 加载配置（constants已经加载game.json）
    dm = DataManager()
    dm.load_config("game.json")
    dm.load_config("ui.json")
    dm.load_save()

    # 从配置读取全屏状态
    fullscreen = dm.get_config("game.json", "window.fullscreen")
    flags = pygame.FULLSCREEN if fullscreen else 0

    screen = pygame.display.set_mode(SCREENRECT.size, flags)
    pygame.display.set_caption(WINDOW_CAPTION)
    pygame.mouse.set_visible(True)

    # 场景管理器
    sm = SceneManager()
    sm.register_scene("start", StartScene(sm))
    sm.register_scene("game", GameScene(sm))
    sm.register_scene("pause", PauseScene(sm))
    sm.register_scene("over", OverScene(sm))
    sm.register_scene("lobby", LobbyScene(sm))
    sm.switch_scene("start")

    clock = pygame.time.Clock()
    running = True
    while running:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            # 全局F键切换全屏
            if e.type == pygame.KEYDOWN and e.key == pygame.K_f:
                fullscreen = not fullscreen
                flags = pygame.FULLSCREEN if fullscreen else 0
                screen = pygame.display.set_mode(SCREENRECT.size, flags)
                # 更新配置
                dm.configs["game.json"]["window"]["fullscreen"] = fullscreen

            sm.handle_event(e)

        sm.update()
        sm.draw(screen)
        clock.tick(FPS)

        # 检查场景管理器的退出标志
        if sm.should_quit:
            running = False

    if pygame.mixer:
        pygame.mixer.music.fadeout(1000)
    pygame.time.wait(1000)
    pygame.quit()


if __name__ == "__main__":
    main()