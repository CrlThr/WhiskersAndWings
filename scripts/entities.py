import math
import random

import pygame

from scripts.particles import Particles
from scripts.spark import Spark


class PhysicsEntity:
    def __init__(self, game, e_type, pos, size):
        self.game = game
        self.type = e_type
        self.pos = list(pos)
        self.size = size
        self.velocity = [0, 0]
        self.collisions = {'up': False, 'down': False, 'left': False, 'right': False}
        self.death = False
        self.at_door = False

        self.action = ''
        self.anim_offset = (-3, -3)
        self.flip = False
        self.set_action('idle')

        self.last_movement = [0, 0]

    def rect(self):
        return pygame.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1])

    def set_action(self, action):
        if action != self.action:
            self.action = action
            self.animation = self.game.assets[self.type + '/' + self.action].copy()

    def update(self, tilemap, movement=(0, 0), speed=(1, 1)):
        self.collisions = {'up': False, 'down': False, 'left': False, 'right': False}

        frame_movement = ((movement[0] + self.velocity[0]) * speed[0], (movement[1] + self.velocity[1]) * speed[1])

        self.pos[0] += frame_movement[0]

        entity_rect = self.rect()
        if not self.game.chest:
            for rect in tilemap.chest_rects_around(self.pos):
                if rect.colliderect(entity_rect):
                    self.game.chest = 1
                    tilemap.chest_state(self.pos)
        if self.game.key_state == 1:
            for rect in tilemap.key_rects_around(self.pos):
                if rect.colliderect(entity_rect):
                    self.game.key += 1
                    tilemap.key_disable()
                    print(self.game.key, self.game.key_state)
        for rect in tilemap.door_rects_around(self.pos):
            if rect.colliderect(entity_rect):
                self.at_door = True
            else:
                self.at_door = False

        entity_rect = self.rect()
        for rect in tilemap.button_rects_around(self.pos):
            if rect.colliderect(entity_rect):
                self.game.button = 1
                tilemap.button_state(self.pos)

        entity_rect = self.rect()
        for rect in tilemap.lever_rects_around(self.pos):
            if rect.colliderect(entity_rect):
                self.game.lever = 1
                tilemap.lever_state(self.pos)

        entity_rect = self.rect()
        for rect in tilemap.physics_rects_around(self.pos):
            if entity_rect.colliderect(rect):
                if frame_movement[0] > 0:
                    entity_rect.right = rect.left
                    self.collisions['right'] = True
                if frame_movement[0] < 0:
                    entity_rect.left = rect.right
                    self.collisions['left'] = True
                self.pos[0] = entity_rect.x

        entity_rect = self.rect()
        for rect in tilemap.platform_rects_around(self.pos):
            if entity_rect.colliderect(rect):
                if frame_movement[0] > 0:
                    entity_rect.right = rect.left
                    self.collisions['right'] = True
                if frame_movement[0] < 0:
                    entity_rect.left = rect.right
                    self.collisions['left'] = True
                self.pos[0] = entity_rect.x

        self.pos[1] += frame_movement[1]

        entity_rect = self.rect()
        for rect in tilemap.death_rects_around(self.pos):
            if entity_rect.colliderect(rect):
                if frame_movement[1] != 0 or frame_movement[0] != 0:
                    self.death = True

        entity_rect = self.rect()
        for rect in tilemap.physics_rects_around(self.pos):
            if entity_rect.colliderect(rect):
                if frame_movement[1] > 0:
                    entity_rect.bottom = rect.top
                    self.collisions['down'] = True
                if frame_movement[1] < 0:
                    entity_rect.top = rect.bottom
                    self.collisions['up'] = True
                self.pos[1] = entity_rect.y

        entity_rect = self.rect()
        for rect in tilemap.platform_rects_around(self.pos):
            if entity_rect.colliderect(rect):
                if frame_movement[1] > 0:
                    entity_rect.bottom = rect.top
                    self.collisions['down'] = True
                    self.pos[1] = entity_rect.bottom - self.size[1]
                if frame_movement[1] < 0:
                    entity_rect.top = rect.bottom
                    self.collisions['up'] = True
                    self.pos[1] = entity_rect.y

        if movement[0] > 0:
            self.flip = False
        if movement[0] < 0:
            self.flip = True

        self.last_movement = movement

        if self.type != 'player2':
            self.velocity[1] = min(5, self.velocity[1] + 0.1)

        if self.collisions['down'] or self.collisions['up']:
            self.velocity[1] = 0

        self.animation.update()

    def render(self, surf, offset=(0, 0)):
        surf.blit(pygame.transform.flip(self.animation.img(), self.flip, False),
                  (self.pos[0] - offset[0] + self.anim_offset[0], self.pos[1] - offset[1] + self.anim_offset[1]))


class Enemy(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'enemy', pos, size)

        self.walking = 0

    def update(self, tilemap, movement=(0, 0)):
        if self.walking:
            if tilemap.solid_check((self.rect().centerx + (-7 if self.flip else 7), self.pos[1] + 23)):
                if self.collisions['right'] or self.collisions['left']:
                    self.flip = not self.flip
                else:
                    movement = (movement[0] - 0.5 if self.flip else 0.5, movement[1])
            elif tilemap.solid_check_platform((self.rect().centerx + (-7 if self.flip else 7), self.pos[1] + 23)):
                if self.collisions['right'] or self.collisions['left']:
                    self.flip = not self.flip
                else:
                    movement = (movement[0] - 0.5 if self.flip else 0.5, movement[1])
            else:
                self.flip = not self.flip
            self.walking = max(0, self.walking - 1)
            if not self.walking:
                dis = (self.game.player.pos[0] - self.pos[0], self.game.player.pos[1] - self.pos[1])
                if abs(dis[1]) < 16:
                    if self.flip and dis[0] < 0:
                        self.game.sfx['shoot'].play()
                        self.game.projectiles.append([[self.rect().centerx - 7, self.rect().centery], -1.5, 0])
                        for i in range(4):
                            self.game.sparks.append(Spark(
                                self.game.projectiles[-1][0],
                                random.random() - 0.5 + math.pi,
                                2 + random.random()))
                    if not self.flip and dis[0] > 0:
                        self.game.sfx['shoot'].play()
                        self.game.projectiles.append([[self.rect().centerx + 7, self.rect().centery], 1.5, 0])
                        for i in range(4):
                            self.game.sparks.append(Spark(
                                self.game.projectiles[-1][0],
                                random.random() - 0.5,
                                2 + random.random()))
        elif random.random() < 0.01:
            self.walking = random.randint(30, 120)

        super().update(tilemap, movement=movement)

        if movement[0] != 0:
            self.set_action('run')
        else:
            self.set_action('idle')

        if self.rect().colliderect(self.game.player.rect()) or self.rect().colliderect(self.game.bird.rect()):
            self.game.screenshake = max(16, self.game.screenshake)
            self.game.sfx['hit'].play()
            for i in range(30):
                angle = random.random() * math.pi * 2
                speed = random.random() * 5
                self.game.sparks.append(Spark(self.rect().center, angle, 2 + random.random()))
                self.game.particles.append(
                    Particles(self.game, 'particle', self.rect().center,
                              velocity=[math.cos(angle + math.pi) * speed * 0.5,
                                        math.sin(angle + math.pi) * speed],
                              frame=random.randint(0, 7)))
            self.game.sparks.append(Spark(self.rect().center, 0, 5 + random.random()))
            self.game.sparks.append(Spark(self.rect().center, math.pi, 5 + random.random()))
            self.game.rats += 1
            return True

    def render(self, surf, offset=(0, 0)):
        super().render(surf, offset=offset)


class Player(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'player', pos, size)
        self.air_time = 0
        self.jumps = 1
        self.wall_slide = False
        self.dashing = 0

    def update(self, tilemap, movement=(0, 0), speed=(1, 1)):
        super().update(tilemap, movement=movement, speed=speed)

        self.air_time += 1

        if self.air_time > 300:
            if not self.game.dead:
                self.game.screenshake = max(16, self.game.screenshake)
            self.game.dead += 1

        if self.collisions['down']:
            self.air_time = 0
            self.jumps = 1

        self.wall_slide = False
        if (self.collisions['right'] or self.collisions['left']) and self.air_time > 4:
            self.air_time = 5
            self.wall_slide = True
            self.velocity[1] = min(self.velocity[1], 0.5)
            if self.collisions['right']:
                self.flip = False
            else:
                self.flip = True
            self.set_action('wall_slide')

        if not self.wall_slide:
            if self.air_time > 4:
                self.set_action('jump')
            elif movement[0] != 0:
                self.set_action('run')
            else:
                self.set_action('idle')

        if abs(self.dashing) in (60, 50):
            for i in range(20):
                angle = random.random() * math.pi * 2
                speed = random.random() * 0.5 + 0.5
                pvelocity = [math.cos(angle) * speed, math.sin(angle) * speed]
                self.game.particles.append(Particles(self.game, 'particle', self.rect().center,
                                                     velocity=pvelocity,
                                                     frame=random.randint(0, 7)))
        if self.dashing > 0:
            self.dashing = max(0, self.dashing - 1)
        if self.dashing < 0:
            self.dashing = min(0, self.dashing + 1)
        if abs(self.dashing) > 50:
            self.velocity[0] = abs(self.dashing) / self.dashing * 8
            if abs(self.dashing) == 51:
                self.velocity[0] *= 0.1
            pvelocity = [abs(self.dashing) / self.dashing * random.random() * 3, 0]
            self.game.particles.append(Particles(self.game, 'particle', self.rect().center,
                                                 velocity=pvelocity,
                                                 frame=random.randint(0, 7)))

        if self.velocity[0] > 0:
            self.velocity[0] = max(self.velocity[0] - 0.1, 0)
        else:
            self.velocity[0] = min(self.velocity[0] + 0.1, 0)

    def render(self, surf, offset=(0, 0)):

        super().render(surf, offset=offset)

    def jump(self):
        if self.wall_slide:
            if self.flip and self.last_movement[0] < 0:
                self.velocity[0] = 3.5
                self.velocity[1] = -2.5
                self.air_time = 5
                self.jumps = max(0, self.jumps - 1)
                return True
            elif not self.flip and self.last_movement[0] > 0:
                self.velocity[0] = -3.5
                self.velocity[1] = -2.5
                self.air_time = 5
                self.jumps = max(0, self.jumps - 1)
                return True

        elif self.jumps:
            self.velocity[1] = -3
            self.jumps -= 1
            self.air_time = 5
            return True

    def dash(self):
        if not self.dashing:
            self.game.sfx['dash'].play()
            if self.flip:
                self.dashing = -60
            else:
                self.dashing = 60


class Bird(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'player2', pos, size)

    def update(self, tilemap, movement=(0, 0), speed=(1, 1)):
        super().update(tilemap, movement=movement, speed=speed)

        if self.velocity[0] > 0:
            self.velocity[0] = max(self.velocity[0] - 0.1, 0)
        else:
            self.velocity[0] = min(self.velocity[0] + 0.1, 0)

    def render(self, surf, offset=(0, 0)):
        super().render(surf, offset=offset)
