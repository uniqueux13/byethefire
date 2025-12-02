import pygame
import math
import random
import os
from settings import *


class Enemy:
    def __init__(self, x, y, biome_type):
        self.x = x
        self.y = y
        self.rect = pygame.Rect(x, y, 30, 30)

        # 1. Base Stats
        base_name = BIOME_ENEMIES.get(biome_type, "wolf")
        stats = ENEMY_DATA.get(base_name, ENEMY_DATA["wolf"])

        # 2. VARIANT LOGIC (Only for wolves for now)
        self.name = base_name
        self.hp = stats[0]
        self.max_hp = stats[0]
        self.speed = stats[1]
        self.damage = stats[2]
        self.detection_range = stats[3]
        self.color = stats[4]

        if base_name == "wolf":
            # Roll for variant
            roll = random.randint(1, 100)
            if roll <= 60:
                self.name = "grey_wolf"
                # Standard stats
            elif roll <= 90:
                self.name = "brown_wolf"
                self.speed += 0.5  # Faster
                self.hp += 20
                self.max_hp += 20
            else:
                self.name = "black_wolf"
                self.damage = 50  # 2-Shot Kill (Player has 100 HP)
                self.hp += 50
                self.max_hp += 50
                self.speed += 0.2
                self.detection_range += 100  # Spots you from further away

        # AI State Machine
        self.state = "IDLE"  # IDLE, CHASE, ATTACK, HOWL, HIT
        self.cooldown_timer = 0
        self.stun_timer = 0

        # Animation State
        self.facing = "down"
        self.frame_index = 0
        self.anim_timer = 0

        # Load Assets
        self.animations = {}
        self.load_animations()

    def load_animations(self):
        actions = ["idle", "walk", "attack", "howl"]
        directions = ["down", "up", "left", "right"]

        for action in actions:
            for direction in directions:
                # This now looks for "black_wolf_walk_down.png", etc.
                filename = f"{self.name}_{action}_{direction}.png"
                path = os.path.join("assets", filename)
                key = f"{action}_{direction}"

                if os.path.exists(path):
                    try:
                        sheet = pygame.image.load(path).convert_alpha()
                        sprite_w, sprite_h = 32, 32
                        sheet_w = sheet.get_width()
                        frames_count = sheet_w // sprite_w

                        frames = []
                        for i in range(frames_count):
                            frames.append(sheet.subsurface(
                                (i * sprite_w, 0, sprite_w, sprite_h)))

                        self.animations[key] = frames

                    except Exception as e:
                        print(f"Error loading {filename}: {e}")
                        self.animations[key] = self.make_placeholder(action)
                else:
                    self.animations[key] = self.make_placeholder(action)

    def make_placeholder(self, action):
        frames = []
        c = self.color
        if "black" in self.name:
            c = (50, 50, 50)
        elif "brown" in self.name:
            c = (139, 69, 19)
        elif "grey" in self.name:
            c = (128, 128, 128)

        if action == "attack":
            c = (255, 0, 0)
        if action == "howl":
            c = (0, 0, 255)

        s = pygame.Surface((30, 30))
        s.fill(c)
        pygame.draw.rect(s, (0, 0, 0), (0, 0, 30, 30), 1)
        pygame.draw.rect(s, (0, 0, 0), (5, 5, 5, 5))
        return [s]

    def update(self, player, all_enemies):
        dist = math.hypot(player.pos_x - self.x, player.pos_y - self.y)

        # Animation Tick
        self.anim_timer += 1
        if self.anim_timer > 10:
            self.anim_timer = 0
            self.frame_index += 1

        # --- FIX 1: STUN LOGIC ---
        if self.state == "HIT":
            self.stun_timer -= 1
            if self.stun_timer <= 0:
                # FORCE WAKE UP
                self.state = "CHASE"
                self.frame_index = 0
            return  # Skip movement while stunned

        dx, dy = 0, 0

        # --- STATE MACHINE ---
        if self.state == "IDLE":
            if dist < self.detection_range:
                self.state = "CHASE"

        elif self.state == "CHASE":
            if dist < 40:
                self.state = "ATTACK"
                self.frame_index = 0
            elif dist > self.detection_range * 1.5:
                self.state = "IDLE"
            else:
                # Move towards player
                angle = math.atan2(player.pos_y - self.y,
                                   player.pos_x - self.x)
                dx = math.cos(angle)
                dy = math.sin(angle)

                # --- FIX 2: SEPARATION (Don't stack) ---
                for other in all_enemies:
                    if other != self:
                        d = math.hypot(other.x - self.x, other.y - self.y)
                        if d < 30:  # If too close
                            # Push away
                            push_angle = math.atan2(
                                self.y - other.y, self.x - other.x)
                            dx += math.cos(push_angle) * 0.5
                            dy += math.sin(push_angle) * 0.5
                # ----------------------------------------

                self.x += dx * self.speed
                self.y += dy * self.speed

        elif self.state == "ATTACK":
            attack_key = f"attack_{self.facing}"
            frames = self.animations.get(
                attack_key, self.make_placeholder("attack"))
            duration = len(frames) * 10

            if self.frame_index * 10 >= max(30, duration):
                if dist < 40:
                    player.take_damage(self.damage)

                self.state = "HOWL"
                self.frame_index = 0

        elif self.state == "HOWL":
            howl_key = f"howl_{self.facing}"
            frames = self.animations.get(
                howl_key, self.make_placeholder("howl"))
            duration = len(frames) * 10

            if self.frame_index * 10 >= max(30, duration):
                self.state = "CHASE"

        # --- DETERMINE FACING ---
        if abs(dx) > 0 or abs(dy) > 0:
            if abs(dx) > abs(dy):
                self.facing = "right" if dx > 0 else "left"
            else:
                self.facing = "down" if dy > 0 else "up"

        elif self.state in ["ATTACK", "HOWL"]:
            if abs(player.pos_x - self.x) > abs(player.pos_y - self.y):
                self.facing = "right" if player.pos_x > self.x else "left"
            else:
                self.facing = "down" if player.pos_y > self.y else "up"

        self.rect.topleft = (self.x, self.y)

    def take_damage(self, dmg):
        self.hp -= dmg
        # --- FIX 1 PART B: FORCE HIT STATE ---
        self.state = "HIT"
        self.stun_timer = 20  # 20 frames of stun

        # Knockback
        self.x += random.randint(-15, 15)
        self.y += random.randint(-15, 15)

    def draw(self, screen):
        action = "idle"
        if self.state == "ATTACK":
            action = "attack"
        elif self.state == "HOWL":
            action = "howl"
        elif self.state == "CHASE":
            action = "walk"
        elif self.state == "HIT":
            action = "idle"  # Use idle frame for hit, or make a hit sprite

        key = f"{action}_{self.facing}"
        frames = self.animations.get(key)

        if not frames:
            frames = self.animations.get(
                f"idle_{self.facing}", self.make_placeholder(action))

        img = frames[self.frame_index % len(frames)]
        screen.blit(img, (self.x, self.y))

        # Health Bar
        if self.hp < self.max_hp:
            ratio = self.hp / self.max_hp
            pygame.draw.rect(screen, (50, 0, 0), (self.x, self.y-5, 30, 4))
            pygame.draw.rect(screen, (255, 0, 0),
                             (self.x, self.y-5, 30*ratio, 4))
