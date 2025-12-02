import pygame
import sys
import random
import math
import os
import json

# --- CONFIGURATION ---
WIDTH, HEIGHT = 1280, 720
FPS = 60
MOVE_SPEED = 3
JUMP_FORCE = 10
GRAVITY_Z = 0.8
MAX_FUEL = 100
MAX_CARRY_BASE = 5

### --- DEV TOOLS CONFIGURATION --- ###
# Set to True to enable cheats by default, or toggle with '0' key in-game
DEV_MODE_ENABLED = True
### ------------------------------- ###

# --- COLORS ---
# Interface & Lighting
COLOR_BG_FOREST = (22, 20, 25)
COLOR_UI_BG = (0, 0, 0, 200)
COLOR_TEXT_MAIN = (255, 255, 255)
COLOR_TEXT_DIM = (150, 150, 170)
COLOR_PYRE_LIT = (255, 140, 0)

# Map / Minimap
COLOR_MAP_VISITED = (100, 100, 100)
COLOR_MAP_CURRENT = (255, 200, 0)
COLOR_MAP_HUB = (255, 50, 50)

# Biomes
COLOR_SNOW = (240, 245, 255)       # North
COLOR_DESERT = (235, 215, 160)     # South
COLOR_MOUNTAIN = (60, 55, 50)      # East
COLOR_OCEAN = (20, 40, 100)        # West
COLOR_GLACIER = (180, 255, 255)    # NW
COLOR_TUNDRA = (200, 200, 210)     # NE
COLOR_SWAMP = (25, 35, 20)         # SW
COLOR_BADLANDS = (160, 80, 40)     # SE

# Hazards / Terrain
COLOR_MUD = (45, 30, 15)
COLOR_WATER = (50, 100, 200)
COLOR_ICE_PATCH = (210, 230, 255)
COLOR_CLIFF = (50, 45, 40)

# --- NARRATIVE DATA ---
ARTIFACT_DATA = {
    "branch": ["It burns quickly.", "Better than freezing.", "Keep it bright."],
    "Wood": ["Solid fuel.", "A heavy log.", "Good for the fire."],
    "Rope": ["Strong fibers.", "Useful for binding."],
    "Reeds": ["Flexible swamp grass.", "Weaves easily."],
    "Flint": ["A spark in the dark.", "Sharp stone."],
    "Fur": ["Thick and warm.", "Smells of musk."],
    "Oil": ["Viscous fuel.", "Burns slow and hot."],
    "Iron": ["Rusted scrap.", "Old world metal."],
    "Fabric": ["Woven cloth.", "Basic protection."]
}

RECIPES = {
    "Fabric": {"cost": {"Reeds": 3}, "desc": "Woven plant fiber."},
    "Campfire": {"cost": {"Wood": 2, "Flint": 1}, "desc": "Portable heat (+20 Fire)."},
    "Tent": {"cost": {"Wood": 5, "Fabric": 2, "Fur": 1}, "desc": "Shelter. SAVES GAME."},
    "Lantern": {"cost": {"Iron": 2, "Oil": 1}, "desc": "Permanent light source."}
}


class AssetManager:
    def __init__(self):
        self.images = {}
        self.animations = {}
        self.load_assets()

    def load_assets(self):
        # 1. Helper: Create colored rect if image fails
        def make_placeholder(color, size=(20, 30)):
            s = pygame.Surface(size)
            s.fill(color)
            pygame.draw.rect(s, (0, 0, 0), s.get_rect(), 1)  # Border
            return s

        # 2. Helper: Load single image
        def load_img(name, fallback_color, size=(20, 20)):
            path = os.path.join("assets", f"{name}.png")
            try:
                img = pygame.image.load(path).convert_alpha()
                return img
            except:
                return make_placeholder(fallback_color, size)

        # 3. Helper: Load Sprite Sheet
        def load_sheet(name, frames, fallback_color, size=(20, 30)):
            path = os.path.join("assets", f"{name}.png")
            anim_list = []
            try:
                sheet = pygame.image.load(path).convert_alpha()
                w = sheet.get_width() // frames
                h = sheet.get_height()
                for i in range(frames):
                    anim_list.append(sheet.subsurface((i*w, 0, w, h)))
            except:
                for _ in range(frames):
                    anim_list.append(make_placeholder(fallback_color, size))
            return anim_list

        # --- LOAD STATIC IMAGES ---
        self.images['keeper'] = load_img("keeper", (100, 100, 255), (20, 30))
        self.images['pyre'] = load_img("pyre", (80, 80, 80), (30, 40))
        self.images['tent'] = load_img("tent", (200, 50, 50), (60, 40))

        # Terrain Objects
        self.images['tree'] = load_img("tree", (50, 100, 50), (40, 80))
        self.images['cactus'] = load_img("cactus", (50, 150, 50), (30, 60))
        self.images['rock'] = load_img("rock", (100, 100, 100), (30, 30))

        # Items
        self.images['Wood'] = load_img("wood", (139, 69, 19))
        self.images['branch'] = load_img("branch", (160, 82, 45))
        self.images['Rope'] = load_img("rope", (193, 154, 107))
        self.images['Reeds'] = load_img("reeds", (100, 255, 100))
        self.images['Flint'] = load_img("flint", (50, 50, 50))
        self.images['Fur'] = load_img("fur", (220, 220, 220))
        self.images['Oil'] = load_img("oil", (20, 0, 50))
        self.images['Iron'] = load_img("iron", (150, 50, 0))
        self.images['Fabric'] = load_img("fabric", (255, 255, 255))

        # --- LOAD ANIMATIONS ---
        self.animations['fire'] = load_sheet(
            "fire", 8, (255, 100, 0), (20, 20))

        # Player
        self.animations['idle_down'] = load_sheet(
            "idle_down", 2, (255, 255, 255))
        self.animations['idle_up'] = load_sheet("idle_up", 2, (255, 255, 255))
        self.animations['idle_left'] = load_sheet(
            "idle_left", 4, (255, 255, 255))
        self.animations['idle_right'] = load_sheet(
            "idle_right", 4, (255, 255, 255))
        self.animations['walk_down'] = load_sheet(
            "walk_down", 4, (255, 255, 255))
        self.animations['walk_up'] = load_sheet("walk_up", 4, (255, 255, 255))
        self.animations['walk_left'] = load_sheet(
            "walk_left", 4, (255, 255, 255))
        self.animations['walk_right'] = load_sheet(
            "walk_right", 4, (255, 255, 255))

    def get_image(self, name):
        return self.images.get(name, self.images['branch'])


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
        self.has_tent = False

        # --- BIOME DETERMINATION ---
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

        if coords == (0, 0):
            return

        self.generate_terrain()
        self.generate_items()

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


class Player:
    def __init__(self, x, y):
        self.pos_x = x
        self.pos_y = y
        self.z = 0
        self.vel_z = 0
        self.inventory = []
        self.has_lantern = False
        self.carrying_torch = False
        self.torch_health = 0.0

        self.speed = MOVE_SPEED
        self.velocity_mag = 0
        self.facing = "down"
        self.action = "idle"
        self.frame_index = 0
        self.animation_timer = 0

    def get_rect(self):
        return pygame.Rect(self.pos_x - 10, self.pos_y - 8, 20, 16)

    def jump(self):
        if self.z == 0:
            penalty = 0
            if len(self.inventory) > 5:
                penalty = 4
            self.vel_z = max(5, JUMP_FORCE - penalty)

    def update_animation(self):
        self.animation_timer += 1
        if self.animation_timer >= 10:
            self.animation_timer = 0
            self.frame_index += 1

    def move(self, room):
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

        if dx != 0 or dy != 0:
            mag = math.hypot(dx, dy)
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


class Game:
    def __init__(self):
        pygame.init()
        pygame.joystick.init()
        self.joysticks = [pygame.joystick.Joystick(
            x) for x in range(pygame.joystick.get_count())]
        for joy in self.joysticks:
            joy.init()

        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Kindle: Dev Edition")
        self.clock = pygame.time.Clock()

        self.font = pygame.font.SysFont("Courier New", 16)
        self.dialogue_font = pygame.font.SysFont("Georgia", 20, italic=True)
        self.title_font = pygame.font.SysFont("Courier New", 60, bold=True)
        self.ui_title = pygame.font.SysFont("Courier New", 24, bold=True)

        self.assets = AssetManager()
        self.state = "MENU"
        self.crafting_open = False

        # Dev Tools
        self.free_crafting = DEV_MODE_ENABLED

        self.fire_health = MAX_FUEL
        self.wood_stockpile = []
        self.automation_unlocked = False
        self.visited_rooms = set()
        self.revealed_map = set()
        self.rooms = {}
        self.tents = []

        self.player = Player(WIDTH // 2, HEIGHT // 2)
        self.npc = NPC(WIDTH//2 + 90, HEIGHT//2 - 20)
        self.stockpile_rect = pygame.Rect(
            WIDTH//2 - 100, HEIGHT//2 - 20, 40, 40)

        self.current_room_coords = (0, 0)
        self.load_room((0, 0))

        self.current_dialogue = ""
        self.dialogue_timer = 0
        self.show_map = False
        self.frame_count = 0

    def save_game(self):
        data = {
            "fire": self.fire_health,
            "inventory": self.player.inventory,
            "stockpile": self.wood_stockpile,
            "room": self.current_room_coords,
            "pos": (self.player.pos_x, self.player.pos_y),
            "revealed": list(self.revealed_map),
            "tents": self.tents,
            "automation": self.automation_unlocked
        }
        try:
            with open("savegame.json", "w") as f:
                json.dump(data, f)
            self.trigger_dialogue("Game Saved.", 120)
        except:
            print("Save failed")

    def load_game(self):
        try:
            with open("savegame.json", "r") as f:
                data = json.load(f)
                self.fire_health = data["fire"]
                self.player.inventory = data["inventory"]
                self.wood_stockpile = data["stockpile"]
                self.automation_unlocked = data["automation"]
                self.player.pos_x, self.player.pos_y = data["pos"]
                self.revealed_map = set(tuple(x) for x in data["revealed"])
                self.tents = [tuple(x) for x in data["tents"]]
                self.load_room(tuple(data["room"]))
                self.state = "PLAY"
                self.trigger_dialogue("Welcome back.", 120)
        except:
            self.trigger_dialogue("No save found.", 120)

    def get_room(self, coords):
        if coords not in self.rooms:
            self.rooms[coords] = Room(coords)
        return self.rooms[coords]

    def load_room(self, coords):
        self.current_room = self.get_room(coords)
        self.current_room_coords = coords
        self.visited_rooms.add(coords)
        self.revealed_map.add(coords)
        self.current_room.has_tent = coords in self.tents
        if self.current_room.biome in ['snow', 'glacier']:
            self.trigger_dialogue("It is freezing here...", 60)

    def trigger_dialogue(self, text, duration):
        self.current_dialogue = text
        self.dialogue_timer = duration

    def run(self):
        while True:
            self.input()
            self.update()
            self.draw()
            self.clock.tick(FPS)

    def input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                # --- DEV TOOLS START ---
                if event.key == pygame.K_0:
                    self.free_crafting = not self.free_crafting
                    state = "ON" if self.free_crafting else "OFF"
                    self.trigger_dialogue(f"DEV: Free Crafting {state}", 60)
                # --- DEV TOOLS END ---

                if self.state == "MENU":
                    if event.key == pygame.K_SPACE:
                        self.state = "PLAY"
                        self.reset_game()
                    if event.key == pygame.K_l:
                        self.load_game()
                elif self.state == "PLAY":
                    if event.key == pygame.K_i:
                        self.crafting_open = not self.crafting_open
                    if self.crafting_open:
                        if event.key == pygame.K_1:
                            self.craft("Fabric")
                        if event.key == pygame.K_2:
                            self.craft("Campfire")
                        if event.key == pygame.K_3:
                            self.craft("Tent")
                        if event.key == pygame.K_4:
                            self.craft("Lantern")
                    else:
                        if event.key == pygame.K_SPACE:
                            self.player.jump()
                        if event.key == pygame.K_e:
                            self.handle_interaction()
                        if event.key == pygame.K_m:
                            self.show_map = not self.show_map
                elif self.state == "GAME_OVER":
                    if event.key == pygame.K_r:
                        self.state = "MENU"

    def craft(self, item_name):
        recipe = RECIPES[item_name]
        can_craft = True

        # --- DEV CHEAT LOGIC ---
        if self.free_crafting:
            can_craft = True
        else:
            temp = self.player.inventory[:]
            for k, v in recipe['cost'].items():
                if temp.count(k) < v:
                    can_craft = False
        # -----------------------

        if can_craft:
            if not self.free_crafting:
                for k, v in recipe['cost'].items():
                    for _ in range(v):
                        self.player.inventory.remove(k)

            if item_name == "Tent":
                if not self.current_room.has_tent:
                    self.current_room.has_tent = True
                    self.tents.append(self.current_room_coords)
                    self.save_game()
                    self.trigger_dialogue("Tent built & Game Saved.", 120)
                else:
                    self.trigger_dialogue("Tent already here.", 60)
            elif item_name == "Campfire":
                self.fire_health = min(MAX_FUEL, self.fire_health + 20)
                self.trigger_dialogue("Fire stoked.", 60)
            elif item_name == "Lantern":
                self.player.has_lantern = True
                self.trigger_dialogue("Lantern equipped!", 60)
            else:
                self.player.inventory.append(item_name)
                self.trigger_dialogue(f"Crafted {item_name}", 60)
        else:
            self.trigger_dialogue("Not enough materials.", 60)

    def handle_interaction(self):
        p_rect = self.player.get_rect()

        # 1. Pickup
        for item in self.current_room.items[:]:
            if math.hypot(item.centerx - self.player.pos_x, item.centery - self.player.pos_y) < 50:
                self.current_room.items.remove(item)
                self.player.inventory.append(item.name)
                self.trigger_dialogue(f"Got {item.name}", 60)
                return

        # 2. Pyres
        for pyre in self.current_room.pyres:
            if math.hypot(pyre.rect.centerx - self.player.pos_x, pyre.rect.centery - self.player.pos_y) < 60:
                if not pyre.lit:
                    if self.player.has_lantern or self.player.carrying_torch or self.current_room_coords == (0, 0):
                        pyre.light()
                        self.revealed_map.add(self.current_room_coords)
                        self.trigger_dialogue("Signal lit.", 60)
                    else:
                        self.trigger_dialogue("Need a light source!", 60)
                return

        # 3. TENT INTERACTION (Placed 80px North of center)
        if self.current_room.has_tent:
            # Check distance to tent location (WIDTH//2, HEIGHT//2 - 80)
            dist_tent = math.hypot(
                WIDTH//2 - self.player.pos_x, (HEIGHT//2 - 80) - self.player.pos_y)
            if dist_tent < 60:
                self.save_game()
                return

        # 4. Hub Interactions
        if self.current_room_coords == (0, 0):
            # Fire
            if math.hypot(WIDTH//2 - self.player.pos_x, HEIGHT//2 - self.player.pos_y) < 70:
                if len(self.player.inventory) > 0:
                    item = self.player.inventory.pop()
                    self.fire_health = min(MAX_FUEL, self.fire_health + 15)
                    desc = ARTIFACT_DATA.get(item, ["It burns."])
                    if isinstance(desc, list):
                        desc = random.choice(desc)
                    self.trigger_dialogue(f"NPC: \"{desc}\"", 120)
                else:
                    self.player.carrying_torch = True
                    self.player.torch_health = 100.0
                    self.trigger_dialogue("Torch Lit.", 120)
                return

            # NPC
            if p_rect.colliderect(self.npc.rect):
                if not self.automation_unlocked and self.player.inventory.count("Wood") >= 5:
                    for _ in range(5):
                        self.player.inventory.remove("Wood")
                    self.automation_unlocked = True
                    self.trigger_dialogue(
                        "NPC: \"I will now tend the fire.\"", 180)
                else:
                    self.trigger_dialogue(
                        f"NPC: \"{self.npc.get_random_line()}\"", 120)
                return

            # Stockpile
            if p_rect.colliderect(self.stockpile_rect):
                if len(self.player.inventory) > 0:
                    item = self.player.inventory.pop()
                    self.wood_stockpile.append(item)
                    self.trigger_dialogue(f"Stored {item}", 60)
                elif len(self.wood_stockpile) > 0:
                    item = self.wood_stockpile.pop()
                    self.player.inventory.append(item)
                    self.trigger_dialogue(f"Took {item}", 60)

    def reset_game(self):
        self.fire_health = MAX_FUEL
        self.wood_stockpile = []
        self.automation_unlocked = False
        self.player = Player(WIDTH//2, HEIGHT//2)
        self.rooms = {}
        self.load_room((0, 0))

    def update(self):
        self.frame_count += 1
        if self.state == "PLAY" and not self.crafting_open:
            self.player.update_animation()
            self.fire_health -= 0.005

            if self.player.carrying_torch:
                self.player.torch_health -= 0.1
                if self.current_room.biome in ['snow', 'glacier']:
                    self.player.torch_health -= 0.15
                if self.player.torch_health <= 0:
                    self.player.carrying_torch = False
                    self.trigger_dialogue("Torch faded.", 120)

            if self.automation_unlocked and self.fire_health < 30 and len(self.wood_stockpile) > 0:
                if random.randint(0, 100) < 2:
                    self.wood_stockpile.pop()
                    self.fire_health += 15
                    self.trigger_dialogue("NPC burned a log.", 60)

            if self.fire_health <= 0:
                self.state = "GAME_OVER"

            self.player.move(self.current_room)
            p_rect = self.player.get_rect()

            if self.current_room.biome == 'glacier':
                for ice in self.current_room.fragile_ice:
                    if p_rect.colliderect(ice['rect']):
                        if self.player.velocity_mag < 0.2:
                            ice['integrity'] -= 1
                            if ice['integrity'] <= 0:
                                self.fire_health -= 15
                                self.player.pos_x = WIDTH//2
                                self.trigger_dialogue(
                                    "Ice broke! -15 Fire", 120)

            if self.player.z <= 0:
                for w in self.current_room.water_tiles:
                    if p_rect.colliderect(w):
                        self.fire_health -= 10
                        self.player.pos_x = WIDTH//2
                        self.player.pos_y = HEIGHT//2
                        self.trigger_dialogue("Fell in water.", 60)

            for echo in self.current_room.echoes:
                echo.update(self.player)
                if p_rect.colliderect(echo.rect) and self.player.z < 10:
                    if len(self.player.inventory) > 0:
                        self.player.inventory.pop()
                    else:
                        self.fire_health -= 5
                    angle = math.atan2(self.player.pos_y -
                                       echo.y, self.player.pos_x - echo.x)
                    self.player.pos_x += math.cos(angle)*80
                    self.player.pos_y += math.sin(angle)*80

            if self.player.pos_x > WIDTH:
                self.load_room(
                    (self.current_room_coords[0]+1, self.current_room_coords[1]))
                self.player.pos_x = 20
            elif self.player.pos_x < 0:
                self.load_room(
                    (self.current_room_coords[0]-1, self.current_room_coords[1]))
                self.player.pos_x = WIDTH-20
            elif self.player.pos_y > HEIGHT:
                self.load_room(
                    (self.current_room_coords[0], self.current_room_coords[1]+1))
                self.player.pos_y = 20
            elif self.player.pos_y < 0:
                self.load_room(
                    (self.current_room_coords[0], self.current_room_coords[1]-1))
                self.player.pos_y = HEIGHT-20

            if self.dialogue_timer > 0:
                self.dialogue_timer -= 1

    def draw(self):
        b = self.current_room.biome
        c = COLOR_BG_FOREST
        if b == 'snow':
            c = COLOR_SNOW
        elif b == 'desert':
            c = COLOR_DESERT
        elif b == 'mountain':
            c = COLOR_MOUNTAIN
        elif b == 'ocean':
            c = COLOR_OCEAN
        elif b == 'glacier':
            c = COLOR_GLACIER
        elif b == 'tundra':
            c = COLOR_TUNDRA
        elif b == 'swamp':
            c = COLOR_SWAMP
        elif b == 'badlands':
            c = COLOR_BADLANDS
        self.screen.fill(c)

        if self.state == "MENU":
            t = self.title_font.render("KINDLE", True, (255, 255, 255))
            self.screen.blit(t, (WIDTH//2 - t.get_width()//2, 200))
            i = self.font.render(
                "Press SPACE to Start | L to Load", True, (200, 200, 200))
            self.screen.blit(i, (WIDTH//2 - i.get_width()//2, 300))
        elif self.state == "PLAY":
            self.draw_game()
        elif self.state == "GAME_OVER":
            self.draw_game()
            o = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            o.fill((0, 0, 0, 200))
            self.screen.blit(o, (0, 0))
            t = self.title_font.render(
                "THE COLD TOOK YOU", True, COLOR_PYRE_LIT)
            self.screen.blit(t, (WIDTH//2 - t.get_width()//2, HEIGHT//2))

        pygame.display.flip()

    def draw_game(self):
        for w in self.current_room.water_tiles:
            pygame.draw.rect(self.screen, COLOR_WATER, w)
        for m in self.current_room.mud_patches:
            pygame.draw.rect(self.screen, COLOR_MUD, m)
        for i in self.current_room.ice_patches:
            pygame.draw.rect(self.screen, COLOR_ICE_PATCH, i)
        for i in self.current_room.fragile_ice:
            v = max(50, i['integrity']*2)
            pygame.draw.rect(self.screen, (v, v, 255), i['rect'])

        for pyre in self.current_room.pyres:
            self.screen.blit(self.assets.images['pyre'], pyre.rect)
            if pyre.lit:
                f = self.assets.animations['fire'][(self.frame_count//5) % 8]
                self.screen.blit(f, (pyre.rect.centerx-10, pyre.rect.top-20))

        if self.current_room_coords == (0, 0):
            f = self.assets.animations['fire'][(self.frame_count//5) % 8]
            scale = 0.5 + (self.fire_health/MAX_FUEL)
            fs = pygame.transform.scale(f, (int(20*scale*2), int(20*scale*2)))
            self.screen.blit(fs, (WIDTH//2 - fs.get_width() //
                             2, HEIGHT//2 - fs.get_height()//2))
            self.screen.blit(self.assets.images['keeper'], self.npc.rect)
            pygame.draw.rect(self.screen, (100, 60, 30), self.stockpile_rect)
            for i in range(min(len(self.wood_stockpile), 10)):
                self.screen.blit(
                    self.assets.images['Wood'], (self.stockpile_rect.x + (i*2), self.stockpile_rect.y - 10))

        render_list = []
        render_list.append({"y": self.player.pos_y, "type": "player"})
        for o in self.current_room.obstacles:
            render_list.append(
                {"y": o['rect'].bottom, "type": "obs", "obj": o})
        for i in self.current_room.items:
            render_list.append({"y": i.rect.bottom, "type": "item", "obj": i})
        for e in self.current_room.echoes:
            render_list.append({"y": e.y, "type": "echo", "obj": e})

        # Draw Tent with offset (North of fire)
        tent_y = HEIGHT//2 - 80
        if self.current_room.has_tent:
            render_list.append({"y": tent_y, "type": "tent"})

        render_list.sort(key=lambda x: x['y'])

        for r in render_list:
            if r['type'] == "tent":
                # Centered horizontally, but north vertically
                self.screen.blit(
                    self.assets.images['tent'], (WIDTH//2 - 30, tent_y - 20))
            elif r['type'] == "item":
                self.screen.blit(self.assets.get_image(
                    r['obj'].name), r['obj'].rect)
            elif r['type'] == "echo":
                pygame.draw.circle(
                    self.screen, (200, 200, 255, 100), r['obj'].rect.center, 15)
            elif r['type'] == "obs":
                o = r['obj']
                if o.get('type') == 'cliff':
                    pygame.draw.rect(self.screen, COLOR_CLIFF, o['rect'])
                else:
                    self.screen.blit(self.assets.images.get(
                        o.get('type'), self.assets.images['tree']), o['rect'])
            elif r['type'] == "player":
                pygame.draw.ellipse(
                    self.screen, (0, 0, 0), (self.player.pos_x-10, self.player.pos_y-5, 20, 8))
                draw_y = self.player.pos_y - self.player.z - 25
                anim_key = f"{self.player.action}_{self.player.facing}"
                frames = self.assets.animations.get(
                    anim_key, self.assets.animations['idle_down'])
                idx = self.player.frame_index % len(frames)
                self.screen.blit(frames[idx], (self.player.pos_x - 10, draw_y))
                if self.player.has_lantern or self.player.carrying_torch:
                    pygame.draw.circle(self.screen, (255, 255, 100), (int(
                        self.player.pos_x + 10), int(draw_y + 10)), 5)

        self.draw_lighting()

        if self.current_dialogue:
            t = self.dialogue_font.render(
                f"\"{self.current_dialogue}\"", True, (255, 255, 200))
            bg = pygame.Surface((t.get_width()+20, t.get_height()+10))
            bg.fill((0, 0, 0))
            bg.set_alpha(180)
            self.screen.blit(
                bg, (WIDTH//2 - t.get_width()//2 - 10, HEIGHT - 100))
            self.screen.blit(t, (WIDTH//2 - t.get_width()//2, HEIGHT - 95))

        hud_c = (20, 20, 20) if self.current_room.biome in [
            'snow', 'glacier'] else (200, 200, 200)
        hud = self.font.render(
            f"Fire: {int(self.fire_health)}% | LOCATION: {self.current_room.biome.upper()}", True, hud_c)
        self.screen.blit(hud, (20, 20))

        if self.show_map:
            self.draw_map_overlay()
        if self.crafting_open:
            self.draw_crafting()

    def draw_lighting(self):
        dark = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        alpha = 200
        if self.current_room_coords == (0, 0):
            alpha = max(50, 255 - int(self.fire_health*3))
        dark.fill((10, 15, 25, alpha))

        def cut_hole(pos, radius):
            pygame.draw.circle(dark, (0, 0, 0, 0), pos, radius)

        rad = 60
        if self.player.has_lantern:
            rad = 150
        elif self.player.carrying_torch:
            rad = 120
        cut_hole((int(self.player.pos_x), int(
            self.player.pos_y - self.player.z)), rad)

        if self.current_room_coords == (0, 0):
            cut_hole((WIDTH//2, HEIGHT//2),
                     int((self.fire_health/MAX_FUEL)*300))

        for p in self.current_room.pyres:
            if p.lit:
                cut_hole(p.rect.center, 100)

        self.screen.blit(dark, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)

    def draw_crafting(self):
        overlay = pygame.Surface((600, 500))
        overlay.fill((20, 20, 25))
        overlay.set_alpha(240)
        self.screen.blit(overlay, (WIDTH//2 - 300, HEIGHT//2 - 250))

        # Titles
        head = self.ui_title.render("SURVIVAL MENU", True, (255, 255, 255))
        self.screen.blit(
            head, (WIDTH//2 - head.get_width()//2, HEIGHT//2 - 230))

        if self.free_crafting:
            t = self.font.render(
                "-- DEV MODE: FREE CRAFTING --", True, (255, 0, 0))
            self.screen.blit(t, (WIDTH//2 - t.get_width()//2, HEIGHT//2 - 200))

        # --- LEFT SIDE: BACKPACK ---
        pack_t = self.font.render("BACKPACK", True, (200, 200, 255))
        self.screen.blit(pack_t, (WIDTH//2 - 250, HEIGHT//2 - 180))

        # Count Items
        counts = {}
        for i in self.player.inventory:
            counts[i] = counts.get(i, 0) + 1

        y_off = 0
        for item, count in counts.items():
            t = self.font.render(f"{item}: x{count}", True, (255, 255, 255))
            self.screen.blit(t, (WIDTH//2 - 250, HEIGHT//2 - 150 + y_off))
            y_off += 25

        if not counts:
            t = self.font.render("(Empty)", True, (100, 100, 100))
            self.screen.blit(t, (WIDTH//2 - 250, HEIGHT//2 - 150))

        # --- RIGHT SIDE: CRAFTING ---
        craft_t = self.font.render("RECIPES", True, (255, 200, 200))
        self.screen.blit(craft_t, (WIDTH//2 + 50, HEIGHT//2 - 180))

        y = 0
        idx = 1
        for name, data in RECIPES.items():
            cost_s = ", ".join([f"{k} x{v}" for k, v in data['cost'].items()])
            # Check afford
            afford = True
            temp = self.player.inventory[:]
            for k, v in data['cost'].items():
                if temp.count(k) < v:
                    afford = False

            if self.free_crafting:
                afford = True

            c = (255, 255, 255) if afford else (100, 100, 100)
            t1 = self.font.render(f"[{idx}] {name}", True, c)
            t2 = self.font.render(f"Cost: {cost_s}", True, (150, 150, 150))
            self.screen.blit(t1, (WIDTH//2 + 50, HEIGHT//2 - 150 + y))
            self.screen.blit(t2, (WIDTH//2 + 50, HEIGHT//2 - 130 + y))
            y += 60
            idx += 1

    def draw_map_overlay(self):
        s = pygame.Surface((200, 200))
        s.fill((0, 0, 0))
        s.set_alpha(200)
        cx, cy = 100, 100
        for c in self.revealed_map:
            off_x = c[0] - self.current_room_coords[0]
            off_y = c[1] - self.current_room_coords[1]
            dx = cx + (off_x*15)
            dy = cy + (off_y*15)
            if 0 <= dx < 200 and 0 <= dy < 200:
                col = COLOR_MAP_VISITED
                if c == (0, 0):
                    col = COLOR_MAP_HUB   # Red Hub
                if c == self.current_room_coords:
                    col = COLOR_MAP_CURRENT  # Yellow Current
                pygame.draw.rect(s, col, (dx, dy, 12, 12))
        self.screen.blit(s, (WIDTH-220, 20))


if __name__ == "__main__":
    Game().run()
