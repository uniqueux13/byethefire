import pygame
import os

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

# --- SAVES ---
SAVE_FILE = "savegame.json"
COLOR_SLOT_EMPTY = (50, 50, 50)
COLOR_SLOT_USED = (100, 100, 150)
COLOR_SLOT_HOVER = (150, 150, 200)

# settings.py (Add this to the bottom)

# --- PLAYER COMBAT ---
PLAYER_MAX_HP = 100
PLAYER_ATTACK_COOLDOWN = 30  # Frames (0.5 seconds)
PLAYER_DAMAGE = 25

# --- ENEMY CONFIGURATION ---
# Format: [HP, Speed, Damage, Detection_Range, Color_Placeholder]
ENEMY_DATA = {
    "wolf":      [50,  2.5, 10, 200, (100, 100, 100)],  # Forest
    "serpent":   [40,  3.0, 15, 100, (50, 200, 50)],   # Swamp
    "raider":    [80,  2.0, 20, 250, (200, 100, 100)],  # Badlands
    "spirit":    [30,  1.5, 15, 300, (200, 255, 255)],  # Tundra
    "yeti":      [150, 1.0, 30, 150, (240, 240, 255)],  # Glacier
    "crab":      [60,  2.0, 10, 150, (255, 100, 50)],  # Ocean
    "golem":     [200, 0.5, 40, 100, (80, 80, 80)],    # Mountain
    "scorpion":  [45,  3.5, 12, 180, (200, 200, 50)],  # Desert
}

# Map Biomes to Enemies
BIOME_ENEMIES = {
    "forest": "wolf",
    "swamp": "serpent",
    "badlands": "raider",
    "tundra": "spirit",
    "glacier": "yeti",
    "ocean": "crab",
    "mountain": "golem",
    "desert": "scorpion",
    "snow": "wolf"  # Fallback
}
