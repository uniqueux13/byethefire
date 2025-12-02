import pygame
import random
import math
from settings import *
from enemy import Enemy  # Make sure this import is here


class Item:
    def __init__(self, x, y, name):
        self.rect = pygame.Rect(x, y, 20, 20)
        self.name = name
        self.centerx = x + 10
        self.centery = y + 10


class Echo:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.rect = pygame.Rect(x, y, 20, 30)
        self.speed = 1.5

    def update(self, player):
        angle = math.atan2(player.pos_y - self.y, player.pos_x - self.x)
        self.x += math.cos(angle) * self.speed
        self.y += math.sin(angle) * self.speed
        self.rect.center = (self.x, self.y)


class SignalPyre:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 30, 40)
        self.lit = False

    def light(self):
        self.lit = True


class NPC:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 20, 30)
        self.lines = [
            "You are doing well.",
            "If you stack 5 Wood, I can help you.",
            "The fire keeps the cold away.",
            "The North West glacier is treacherous.",
            "Keep the fire lit.",
            "Don't let the light fade.",
            "Did you find anything?"
        ]

    def get_random_line(self):
        return random.choice(self.lines)


class Room:
    def __init__(self, coords):
        self.coords = coords
        self.obstacles = []
        self.items = []
        self.echoes = []
        self.decorations = []
        self.pyres = []
        self.ice_patches = []
        self.mud_patches = []
        self.water_tiles = []
        self.fragile_ice = []
        self.enemies = []  # Initialize empty enemy list
        self.has_tent = False

        # --- BIOME DETERMINATION ---
        # This MUST happen before we generate enemies
        x, y = coords
        if x > 1 and y < -1:
            self.biome = 'tundra'
        elif x < -1 and y < -1:
            self.biome = 'glacier'
        elif x > 1 and y > 1:
            self.biome = 'badlands'
        elif x < -1 and y > 1:
            self.biome = 'swamp'
        elif y < -1:
            self.biome = 'snow'
        elif y > 1:
            self.biome = 'desert'
        elif x > 1:
            self.biome = 'mountain'
        elif x < -1:
            self.biome = 'ocean'
        else:
            self.biome = 'forest'

        for _ in range(20):
            self.decorations.append(
                (random.randint(0, WIDTH), random.randint(0, HEIGHT)))

        # If this is the Hub (0,0), stop here.
        if coords == (0, 0):
            return

        # Generate the world content
        self.generate_terrain()
        self.generate_items()
        self.generate_enemies()  # Calls the method below

    def generate_enemies(self):
        if self.coords == (0, 0):
            return  # No enemies in hub

        # Difficulty scaling: further from center = more enemies
        dist = max(abs(self.coords[0]), abs(self.coords[1]))
        count = random.randint(1, 2) + int(dist/2)

        for _ in range(count):
            ex = random.randint(50, WIDTH-50)
            ey = random.randint(50, HEIGHT-50)
            # Pass the biome so the Enemy class knows what stats to load
            self.enemies.append(Enemy(ex, ey, self.biome))

    def generate_terrain(self):
        w, h = WIDTH, HEIGHT

        if self.biome == 'swamp':
            for _ in range(6):
                self.mud_patches.append(pygame.Rect(
                    random.randint(0, w), random.randint(0, h), 120, 120))
            for _ in range(5):
                self.obstacles.append({'rect': pygame.Rect(random.randint(
                    0, w), random.randint(0, h), 20, 60), 'height': 100, 'type': 'tree'})

        elif self.biome == 'glacier':
            self.water_tiles.append(pygame.Rect(0, 0, 100, h))
            for _ in range(8):
                r = pygame.Rect(random.randint(100, w),
                                random.randint(0, h), 80, 80)
                self.fragile_ice.append({'rect': r, 'integrity': 100})

        elif self.biome == 'badlands':
            for _ in range(15):
                self.obstacles.append({'rect': pygame.Rect(random.randint(
                    0, w), random.randint(0, h), 40, 40), 'height': 100, 'type': 'rock'})

        elif self.biome == 'tundra':
            for _ in range(5):
                self.obstacles.append({'rect': pygame.Rect(random.randint(
                    0, w), random.randint(0, h), 30, 20), 'height': 50, 'type': 'rock'})

        elif self.biome == 'mountain':
            for _ in range(10):
                width = random.randint(50, 200)
                z = random.choice([5, 12, 100])
                self.obstacles.append({'rect': pygame.Rect(random.randint(
                    0, w), random.randint(0, h), width, 30), 'height': z, 'type': 'cliff'})

        elif self.biome == 'snow':
            for _ in range(4):
                self.ice_patches.append(pygame.Rect(random.randint(
                    0, w-200), random.randint(0, h-200), 200, 150))
            for _ in range(5):
                self.obstacles.append({'rect': pygame.Rect(random.randint(
                    0, w), random.randint(0, h), 30, 40), 'height': 100, 'type': 'tree'})

        elif self.biome == 'ocean':
            self.water_tiles.append(pygame.Rect(200, 200, 600, 400))

        elif self.biome == 'desert':
            for _ in range(12):
                self.obstacles.append({'rect': pygame.Rect(random.randint(
                    0, w), random.randint(0, h), 30, 60), 'height': 100, 'type': 'cactus'})

        else:
            for _ in range(8):
                self.obstacles.append({'rect': pygame.Rect(random.randint(
                    0, w), random.randint(0, h), 30, 40), 'height': 100, 'type': 'tree'})

        if random.random() < 0.3:
            self.pyres.append(SignalPyre(random.randint(
                100, WIDTH-100), random.randint(100, HEIGHT-100)))
        if random.random() < 0.2:
            self.echoes.append(
                Echo(random.randint(0, WIDTH), random.randint(0, HEIGHT)))

    def generate_items(self):
        res_map = {
            'forest': ['Wood', 'branch'],
            'swamp': ['Reeds', 'Wood'],
            'badlands': ['Flint'],
            'tundra': ['Fur'],
            'glacier': ['Oil'],
            'mountain': ['Iron'],
            'desert': ['Flint', 'Wood'],
            'ocean': ['Reeds'],
            'snow': ['branch']
        }
        possibilities = res_map.get(self.biome, ['Wood'])
        for _ in range(random.randint(2, 4)):
            name = random.choice(possibilities)
            x, y = random.randint(50, WIDTH-50), random.randint(50, HEIGHT-50)
            if not any(w.collidepoint(x, y) for w in self.water_tiles):
                self.items.append(Item(x, y, name))
