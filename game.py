import math
import os
import sys
import random

import pygame

from scripts.entities import Player, Enemy, Bird
from scripts.utils import load_image, load_images, get_font, Animation
from scripts.tilemap import Tilemap
from scripts.particles import Particles
from scripts.spark import Spark
from scripts.button import Button

icon = pygame.image.load("data/icon.png")


class Game:
    def __init__(self):
        pygame.init()

        pygame.display.set_caption('Game')
        pygame.display.set_icon(icon)
        self.screen = pygame.display.set_mode((1920, 1080))
        self.display = pygame.Surface((1920, 1080), pygame.SRCALPHA)
        self.display_2 = pygame.Surface((1920, 1080))

        self.clock = pygame.time.Clock()

        self.movement = [False, False]
        self.movement_bird = [False, False, False, False]

        self.assets = {
            'decor': load_images('tiles/decor'),
            'egypt_wood': load_images('tiles/egypt_wood'),
            'egypt_platform': load_images('tiles/egypt_wood'),
            'platform_dest': load_images('tiles/platform_dest'),
            'egypt_border': load_images('tiles/egypt_border'),
            'brick': load_images('tiles/brick'),
            'stone_border': load_images('tiles/stone_border'),
            'traps': load_images('tiles/traps'),
            'barrier': load_images('tiles/barrier'),
            'platform': load_images('tiles/platforms'),
            'button': load_images('tiles/buttons'),
            'lever': load_images('tiles/levers'),
            'chest': load_images('tiles/chest'),
            'door': load_images('tiles/doors'),
            'key': load_images('tiles/key'),
            'arrow_spawner': load_images('tiles/arrow_spawner'),
            'arrow': load_images('tiles/arrows'),
            'player': load_image('entities/player.png'),
            'torch': load_images('tiles/torch'),
            'text': load_images('tiles/text'),
            'enemy/idle': Animation(load_images('entities/enemy/idle'), img_dur=6),
            'enemy/run': Animation(load_images('entities/enemy/run'), img_dur=4),
            'player/idle': Animation(load_images('entities/player/idle'), img_dur=6),
            'player/run': Animation(load_images('entities/player/run'), img_dur=4),
            'player/jump': Animation(load_images('entities/player/jump')),
            'player/wall_slide': Animation(load_images('entities/player/wall_slide')),
            'player2/idle': Animation(load_images('entities/player2/idle'), img_dur=6),
            'particle/particle': Animation(load_images('particles/particle'), img_dur=6, loop=False),
            'background': load_images('background'),
            'menu': load_images('menus/bg'),
        }

        self.sfx = {
            'jump': pygame.mixer.Sound('data/sfx/jump.wav'),
            'dash': pygame.mixer.Sound('data/sfx/dash.wav'),
            'hit': pygame.mixer.Sound('data/sfx/hit.wav'),
            'shoot': pygame.mixer.Sound('data/sfx/shoot.wav'),
        }

        self.sfx['shoot'].set_volume(0.4)
        self.sfx['hit'].set_volume(0.8)
        self.sfx['dash'].set_volume(0.3)
        self.sfx['jump'].set_volume(0.3)

        self.player = Player(self, (200, 1000), (35, 35))

        self.bird = Bird(self, (1800, 950), (40, 35))

        self.tilemap = Tilemap(self, tile_size=64)

        self.layout = True

        self.level = 0
        self.load_level(0)

        self.screenshake = 0

    def load_level(self, map_id):
        self.tilemap.load('data/maps/' + str(map_id) + '.json')

        self.enemies = []
        for spawner in self.tilemap.extract([('spawners', 0), ('spawners', 1), (('spawners', 2))]):
            if spawner['variant'] == 0:
                self.player.pos = spawner['pos'].copy()
                self.player.air_time = 0
            elif spawner['variant'] == 1:
                self.bird.pos = spawner['pos'].copy()
            else:
                self.enemies.append(Enemy(self, spawner['pos'], (56, 18)))

        pygame.mixer.music.stop()
        pygame.mixer.music.load(
            'data/music/levels/' + str((min(self.level, len(os.listdir('data/music/levels')) - 1))) + '.wav')
        pygame.mixer.music.set_volume(0.5)
        pygame.mixer.music.play(-1)

        self.player.death = False
        self.bird.death = False

        self.player.at_door = False
        self.bird.at_door = False

        self.background = self.assets['background'][(min(self.level, len(os.listdir('data/images/background')) - 1))]

        self.projectiles = []
        self.particles = []
        self.sparks = []
        self.chest = 0
        self.button = 0
        self.lever = 1
        self.key = 0
        self.key_state = 0
        self.platform_has_moved = False

        self.rats = 0
        self.rats_max = len(self.enemies)

        self.scroll = [0, 0]
        self.dead = 0
        self.transition = -30

    def run(self):
        while True:
            self.display.fill((0, 0, 0, 0))
            self.display_2.blit(self.background, (0, 0))

            self.screenshake = max(0, self.screenshake - 1)

            if self.player.at_door and self.bird.at_door and self.key:
                self.transition += 1
                if self.transition > 30:
                    self.level += 1
                    if self.level > (len(os.listdir('data/maps')) - 1):
                        self.end_menu()
                    else:
                        self.load_level(self.level)
            if self.transition < 0:
                self.transition += 1

            if (self.player.death or self.bird.death) and not self.dead:
                self.dead = 1

            if self.dead:
                if self.dead == 1:
                    for i in range(30):
                        angle = random.random() * math.pi * 2
                        speed = random.random() * 5
                        self.sparks.append(Spark(self.player.rect().center, angle, 2 + random.random()))
                        self.particles.append(Particles(self, 'particle', self.player.rect().center,
                                                        velocity=[math.cos(angle + math.pi) * speed * 0.5,
                                                                  math.sin(angle + math.pi) * speed],
                                                        frame=random.randint(0, 7)))
                self.dead += 1
                if self.dead >= 10:
                    self.transition = min(30, self.transition + 1)
                if self.dead > 40:
                    self.load_level(self.level)

            self.scroll[0] += (self.player.rect().centerx - self.display.get_width() / 2 - self.scroll[0]) / 30
            self.scroll[1] += (self.player.rect().centery - self.display.get_width() / 2 - self.scroll[1]) / 30
            render_scroll = (0, 0)

            self.tilemap.render(self.display, offset=render_scroll)

            for enemy in self.enemies.copy():
                kill = enemy.update(self.tilemap, (0, 0))
                enemy.render(self.display, offset=render_scroll)
                if kill:
                    self.enemies.remove(enemy)

            if self.rats_max:
                if self.rats == self.rats_max:
                    if self.key_state == 0:
                        self.tilemap.key_enable()

            if not self.dead:
                self.player.update(self.tilemap, (self.movement[1] - self.movement[0], 0), (3, 2))
                self.player.render(self.display, offset=render_scroll)
                self.bird.update(self.tilemap, (self.movement_bird[1] - self.movement_bird[0],
                                                self.movement_bird[3] - self.movement_bird[2]), (3, 3))
                self.bird.render(self.display, offset=render_scroll)

            for spark in self.sparks.copy():
                kill = spark.update()
                spark.render(self.display, offset=render_scroll)
                if kill:
                    self.sparks.remove(spark)

            display_mask = pygame.mask.from_surface(self.display)
            display_sillhouette = display_mask.to_surface(setcolor=(0, 0, 0, 180), unsetcolor=(0, 0, 0, 0))
            for offset in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                self.display_2.blit(display_sillhouette, offset)

            for particle in self.particles.copy():
                kill = particle.update()
                particle.render(self.display, offset=render_scroll)
                if particle.type == 'leaf':
                    particle.pos[0] += math.sin(particle.animation.frame * 0.035) * 0.3
                if kill:
                    self.particles.remove(particle)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    # Movement Bird
                    if event.key == pygame.K_LEFT:
                        self.movement_bird[0] = True
                    if event.key == pygame.K_RIGHT:
                        self.movement_bird[1] = True
                    if event.key == pygame.K_UP:
                        self.movement_bird[2] = True
                    if event.key == pygame.K_DOWN:
                        self.movement_bird[3] = True
                    # Movement Cat
                    if self.layout:
                        if event.key == pygame.K_a:
                            self.movement[0] = True
                        if event.key == pygame.K_w:
                            if self.player.jump():
                                self.sfx['jump'].play()
                    else:
                        if event.key == pygame.K_q:
                            self.movement[0] = True
                        if event.key == pygame.K_z:
                            if self.player.jump():
                                self.sfx['jump'].play()
                    if event.key == pygame.K_d:
                        self.movement[1] = True
                    if event.key == pygame.K_LSHIFT:
                        self.player.dash()
                    if event.key == pygame.K_l:
                        self.layout = not self.layout
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_LEFT:
                        self.movement_bird[0] = False
                    if event.key == pygame.K_RIGHT:
                        self.movement_bird[1] = False
                    if event.key == pygame.K_UP:
                        self.movement_bird[2] = False
                    if event.key == pygame.K_DOWN:
                        self.movement_bird[3] = False
                    if self.layout:
                        if event.key == pygame.K_a:
                            self.movement[0] = False
                    else:
                        if event.key == pygame.K_q:
                            self.movement[0] = False
                    if event.key == pygame.K_d:
                        self.movement[1] = False

            if self.transition:
                transition_surf = pygame.Surface(self.display.get_size())
                pygame.draw.circle(transition_surf, (255, 255, 255),
                                   (self.display.get_width() // 2, self.display.get_height() // 2),
                                   (30 - abs(self.transition)) * 40)
                transition_surf.set_colorkey((255, 255, 255))
                self.display.blit(transition_surf, (0, 0))

            self.display_2.blit(self.display, (0, 0))

            screenshake_offset = (random.random() * self.screenshake - self.screenshake / 2,
                                  random.random() * self.screenshake / 2)
            self.screen.blit(pygame.transform.scale(self.display_2, self.screen.get_size()),
                             (screenshake_offset[0], screenshake_offset[1]))
            pygame.display.update()
            self.clock.tick(60)

    def main_menu(self):
        pygame.mixer.music.load("data/music/menus/background_music.mp3")
        pygame.mixer.music.play(-1)
        while True:
            self.screen.blit(self.assets['menu'][0], (0, 0))

            MENU_MOUSE_POS = pygame.mouse.get_pos()

            PLAY_BUTTON = Button(load_image("menus/buttons/0.png"), pos=(960, 850),
                                 text_input="PLAY", font=get_font(100), base_color="Orange", hovering_color="Yellow")
            QUIT_BUTTON = Button(load_image("menus/buttons/0.png"), pos=(960, 1000),
                                 text_input="QUIT", font=get_font(50), base_color="White", hovering_color="Yellow")

            for button in [PLAY_BUTTON, QUIT_BUTTON]:
                button.change_color(MENU_MOUSE_POS)
                button.update(self.screen)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if PLAY_BUTTON.check_for_input(MENU_MOUSE_POS):
                        pygame.mixer.music.stop()
                        pygame.mixer.music.unload()
                        Game().run()
                    if QUIT_BUTTON.check_for_input(MENU_MOUSE_POS):
                        pygame.quit()
                        sys.exit()

            pygame.display.update()

    def end_menu(self):
        pygame.mixer.music.stop()
        pygame.mixer.music.load("data/music/menus/background_music.mp3")
        pygame.mixer.music.play(-1)
        self.level = 0
        while True:
            self.screen.blit(self.assets['menu'][1], (0, 0))

            MENU_MOUSE_POS = pygame.mouse.get_pos()

            REPLAY_BUTTON = Button(load_image("menus/buttons/0.png"), pos=(960, 850),
                                   text_input="REPLAY", font=get_font(100), base_color="Orange",
                                   hovering_color="Yellow")
            QUIT_BUTTON = Button(load_image("menus/buttons/0.png"), pos=(960, 1000),
                                 text_input="QUIT", font=get_font(50), base_color="White", hovering_color="Yellow")

            for button in [REPLAY_BUTTON, QUIT_BUTTON]:
                button.change_color(MENU_MOUSE_POS)
                button.update(self.screen)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if REPLAY_BUTTON.check_for_input(MENU_MOUSE_POS):
                        pygame.mixer.music.stop()
                        pygame.mixer.music.unload()
                        Game().run()
                    if QUIT_BUTTON.check_for_input(MENU_MOUSE_POS):
                        pygame.quit()
                        sys.exit()

            pygame.display.update()


Game().main_menu()
