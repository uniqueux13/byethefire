import pygame
import math
from settings import *


class Player:
    def __init__(self, x, y):
        self.pos_x = x
        self.pos_y = y
        self.z = 0
        self.vel_z = 0

        # Stats
        self.hp = PLAYER_MAX_HP
        self.max_hp = PLAYER_MAX_HP
        self.inventory = []

        # Equipment
        self.has_lantern = False
        self.carrying_torch = False
        self.torch_health = 0.0
        self.weapon_equipped = "Fists"

        # Movement
        self.speed = MOVE_SPEED
        self.velocity_mag = 0
        self.facing = "down"
        self.action = "idle"

        # Animation / Combat
        self.frame_index = 0
        self.animation_timer = 0
        self.attack_cooldown = 0
        self.is_attacking = False

    def get_rect(self):
        return pygame.Rect(self.pos_x - 10, self.pos_y - 8, 20, 16)

    def get_attack_rect(self):
        if self.facing == "up":
            return pygame.Rect(self.pos_x - 15, self.pos_y - 30, 30, 30)
        if self.facing == "down":
            return pygame.Rect(self.pos_x - 15, self.pos_y + 10, 30, 30)
        if self.facing == "left":
            return pygame.Rect(self.pos_x - 30, self.pos_y - 15, 30, 30)
        if self.facing == "right":
            return pygame.Rect(self.pos_x + 10, self.pos_y - 15, 30, 30)
        return pygame.Rect(self.pos_x, self.pos_y, 1, 1)

    def jump(self):
        if self.z == 0:
            penalty = 0
            if len(self.inventory) > 5:
                penalty = 4
            self.vel_z = max(5, JUMP_FORCE - penalty)

    def attack(self):
        if self.attack_cooldown == 0:
            self.is_attacking = True
            self.attack_cooldown = PLAYER_ATTACK_COOLDOWN
            return True
        return False

    def take_damage(self, amount):
        self.hp -= amount
        if self.facing == "left":
            self.pos_x += 10
        elif self.facing == "right":
            self.pos_x -= 10
        elif self.facing == "up":
            self.pos_y += 10
        else:
            self.pos_y -= 10

    def update_animation(self):
        self.animation_timer += 1
        if self.animation_timer >= 10:
            self.animation_timer = 0
            self.frame_index += 1

        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
            if self.attack_cooldown < 10:
                self.is_attacking = False

    def move(self, room):
        # 1. Keyboard Input
        keys = pygame.key.get_pressed()
        dx, dy = 0, 0
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy = -1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy = 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx = -1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx = 1

        # 2. Controller Input (Override Keyboard if active)
        if pygame.joystick.get_count() > 0:
            joy = pygame.joystick.Joystick(0)
            # Axis 0 = Left Stick Horizontal, Axis 1 = Left Stick Vertical
            # We use a deadzone of 0.2 to prevent drift
            jx = joy.get_axis(0)
            jy = joy.get_axis(1)
            if abs(jx) > 0.2:
                dx = jx
            if abs(jy) > 0.2:
                dy = jy

        # 3. Apply Movement Logic
        if dx != 0 or dy != 0:
            mag = math.hypot(dx, dy)
            # Normalize to prevent diagonal speed boost, but respect analog intensity
            if mag > 1:
                dx /= mag
                dy /= mag

            self.action = "walk"
            if abs(dx) > abs(dy):
                self.facing = "right" if dx > 0 else "left"
            else:
                self.facing = "down" if dy > 0 else "up"
        else:
            self.action = "idle"

        current_speed = self.speed
        if len(self.inventory) > MAX_CARRY_BASE:
            current_speed = max(1, self.speed - 1)

        p_rect = self.get_rect()

        if room.biome == 'swamp':
            for m in room.mud_patches:
                if p_rect.colliderect(m):
                    current_speed *= 0.4

        wind_x, wind_y = 0, 0
        if room.biome == 'tundra':
            wind_x = 0.5
            wind_y = 0.1

        on_ice = False
        for ice in room.ice_patches:
            if p_rect.colliderect(ice):
                on_ice = True

        if on_ice or room.biome == 'glacier':
            self.pos_x += dx * (current_speed * 0.3) + (dx*1.5)
            self.pos_y += dy * (current_speed * 0.3) + (dy*1.5)
        else:
            self.pos_x += dx * current_speed
            self.pos_y += dy * current_speed

        self.pos_x += wind_x
        self.pos_y += wind_y
        self.velocity_mag = math.hypot(dx, dy)

        if self.z > 0 or self.vel_z > 0:
            self.z += self.vel_z
            self.vel_z -= GRAVITY_Z
            if self.z <= 0:
                self.z = 0
                self.vel_z = 0

        p_rect = self.get_rect()
        for obs in room.obstacles:
            if p_rect.colliderect(obs['rect']):
                if self.z < obs['height']:
                    if dx > 0:
                        self.pos_x -= 5
                    if dx < 0:
                        self.pos_x += 5
                    if dy > 0:
                        self.pos_y -= 5
                    if dy < 0:
                        self.pos_y += 5
