import pygame
import sys
import random
import math
import os
import json

# --- IMPORT COMPONENTS ---
from settings import *
from player import Player
from world import Room, NPC


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


class Game:
    def __init__(self):
        pygame.init()
        pygame.joystick.init()
        self.joysticks = [pygame.joystick.Joystick(
            x) for x in range(pygame.joystick.get_count())]
        for joy in self.joysticks:
            joy.init()

        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Kindle: Survival RPG")
        self.clock = pygame.time.Clock()

        self.font = pygame.font.SysFont("Courier New", 16)
        self.dialogue_font = pygame.font.SysFont("Georgia", 20, italic=True)
        self.title_font = pygame.font.SysFont("Courier New", 60, bold=True)
        self.ui_title = pygame.font.SysFont("Courier New", 24, bold=True)

        self.assets = AssetManager()

        # ### STATE VARIABLES ###
        self.state = "MENU"  # MENU, PLAY, GAME_OVER, SLOT_MENU, TYPING
        self.crafting_open = False

        # Save System Variables
        self.save_mode = "LOAD"  # "LOAD" or "SAVE"
        self.slots_data = self.load_all_slots()
        self.input_text = ""
        self.selected_slot = 1
        # ###########################

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

    ### SAVE SYSTEM METHODS ###
    def load_all_slots(self):
        default_data = {"1": None, "2": None, "3": None}
        if not os.path.exists(SAVE_FILE):
            return default_data
        try:
            with open(SAVE_FILE, "r") as f:
                return json.load(f)
        except:
            return default_data

    def perform_save(self, slot_num, save_name):
        data = {
            "name": save_name,
            "fire": self.fire_health,
            "inventory": self.player.inventory,
            "stockpile": self.wood_stockpile,
            "room": self.current_room_coords,
            "pos": (self.player.pos_x, self.player.pos_y),
            "revealed": list(self.revealed_map),
            "tents": self.tents,
            "automation": self.automation_unlocked,
            "hp": self.player.hp  # Save HP
        }
        self.slots_data[str(slot_num)] = data
        try:
            with open(SAVE_FILE, "w") as f:
                json.dump(self.slots_data, f)
            self.trigger_dialogue(f"Saved to Slot {slot_num}", 120)
        except:
            print("Save failed")

    def perform_load(self, slot_num):
        slot_data = self.slots_data.get(str(slot_num))
        if slot_data:
            self.fire_health = slot_data["fire"]
            self.player.inventory = slot_data["inventory"]
            self.wood_stockpile = slot_data["stockpile"]
            self.automation_unlocked = slot_data["automation"]
            self.player.pos_x, self.player.pos_y = slot_data["pos"]
            self.revealed_map = set(tuple(x) for x in slot_data["revealed"])
            self.tents = [tuple(x) for x in slot_data["tents"]]
            self.player.hp = slot_data.get("hp", PLAYER_MAX_HP)  # Load HP
            self.load_room(tuple(slot_data["room"]))
            self.state = "PLAY"
            self.trigger_dialogue(f"Loaded: {slot_data['name']}", 120)
        else:
            self.trigger_dialogue("Empty Slot", 60)
    ### ----------------------- ###

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
            # 1. Quit
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # 2. Mouse Inputs
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.state == "PLAY":
                    if event.button == 1:  # Left Click
                        if self.player.attack():
                            self.handle_combat()

            # 3. Controller Inputs
            if event.type == pygame.JOYBUTTONDOWN:
                # Button 0 (A/Cross) - Jump or Confirm
                if event.button == 0:
                    if self.state == "PLAY":
                        self.player.jump()
                    elif self.state == "SLOT_MENU":
                        if self.save_mode == "LOAD":
                            self.perform_load(self.selected_slot)
                        else:
                            self.state = "TYPING"  # Hard to type with controller, but allows progress

                # Button 1 (B/Circle) - Interact or Back
                if event.button == 1:
                    if self.state == "PLAY":
                        self.handle_interaction()
                    elif self.state == "SLOT_MENU":
                        self.state = "MENU"

                # Button 2 (X/Square) - Attack
                if event.button == 2:
                    if self.state == "PLAY":
                        if self.player.attack():
                            self.handle_combat()

                # Button 3 (Y/Triangle) - Inventory
                if event.button == 3:
                    if self.state == "PLAY":
                        self.crafting_open = not self.crafting_open

                # Button 7 (Start) - Pause/Menu
                if event.button == 7:
                    if self.state == "PLAY":
                        self.state = "MENU"

                # D-Pad / Bumper support for Crafting Menu
                if self.state == "PLAY" and self.crafting_open:
                    if event.button == 0:
                        self.craft("Fabric")
                    if event.button == 2:
                        self.craft("Campfire")
                    if event.button == 1:
                        self.craft("Tent")
                    if event.button == 3:
                        self.craft("Lantern")

            # 4. Keyboard Inputs
            if event.type == pygame.KEYDOWN:
                # --- STATE: TYPING ---
                if self.state == "TYPING":
                    if event.key == pygame.K_RETURN:
                        if len(self.input_text) > 0:
                            self.perform_save(
                                self.selected_slot, self.input_text)
                            self.state = "PLAY"
                            if self.current_room_coords not in self.tents:
                                self.tents.append(self.current_room_coords)
                                self.current_room.has_tent = True
                    elif event.key == pygame.K_BACKSPACE:
                        self.input_text = self.input_text[:-1]
                    elif event.key == pygame.K_ESCAPE:
                        self.state = "PLAY"
                    else:
                        if len(self.input_text) < 15:
                            self.input_text += event.unicode
                    return

                # --- STATE: SLOT MENU ---
                if self.state == "SLOT_MENU":
                    if event.key == pygame.K_1:
                        self.selected_slot = 1
                    if event.key == pygame.K_2:
                        self.selected_slot = 2
                    if event.key == pygame.K_3:
                        self.selected_slot = 3
                    if event.key == pygame.K_ESCAPE:
                        if self.save_mode == "LOAD":
                            self.state = "MENU"
                        else:
                            self.state = "PLAY"
                    if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                        if self.save_mode == "LOAD":
                            self.perform_load(self.selected_slot)
                        else:
                            self.input_text = ""
                            self.state = "TYPING"
                    return

                # --- DEV TOOLS ---
                if event.key == pygame.K_0:
                    self.free_crafting = not self.free_crafting
                    state = "ON" if self.free_crafting else "OFF"
                    self.trigger_dialogue(f"DEV: Free Crafting {state}", 60)

                # --- NORMAL GAMEPLAY ---
                if self.state == "MENU":
                    if event.key == pygame.K_SPACE:
                        self.state = "PLAY"
                        self.reset_game()
                    if event.key == pygame.K_l:
                        self.state = "SLOT_MENU"
                        self.save_mode = "LOAD"
                        self.slots_data = self.load_all_slots()

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

        if not self.free_crafting:
            temp = self.player.inventory[:]
            for k, v in recipe['cost'].items():
                if temp.count(k) < v:
                    can_craft = False

        if can_craft:
            if not self.free_crafting:
                for k, v in recipe['cost'].items():
                    for _ in range(v):
                        self.player.inventory.remove(k)

            if item_name == "Tent":
                if not self.current_room.has_tent:
                    # Open Save Menu instead of instant save
                    self.save_mode = "SAVE"
                    self.state = "SLOT_MENU"
                    self.slots_data = self.load_all_slots()
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

    # --- NEW: COMBAT LOGIC ---
    def handle_combat(self):
        hitbox = self.player.get_attack_rect()
        for enemy in self.current_room.enemies[:]:
            if hitbox.colliderect(enemy.rect):
                enemy.take_damage(PLAYER_DAMAGE)

                # Make the name look nice (e.g., "grey_wolf" -> "Grey Wolf")
                display_name = enemy.name.replace("_", " ").title()

                self.trigger_dialogue(f"Hit {display_name}!", 30)

                if enemy.hp <= 0:
                    self.current_room.enemies.remove(enemy)
                    self.trigger_dialogue(f"Slain {display_name}", 60)
    # -------------------------

    def handle_interaction(self):
        p_rect = self.player.get_rect()

        # 1. Pickup
        for item in self.current_room.items[:]:
            if math.hypot(item.centerx - self.player.pos_x, item.centery - self.player.pos_y) < 50:
                self.current_room.items.remove(item)
                self.player.inventory.append(item.name)
                self.trigger_dialogue(f"Got {item.name}", 60)
                return

        # 2. Pyres (Lighting beacons)
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

        # 3. TENT INTERACTION (Saving)
        if self.current_room.has_tent:
            dist_tent = math.hypot(
                WIDTH//2 - self.player.pos_x, (HEIGHT//2 - 80) - self.player.pos_y)
            if dist_tent < 60:
                self.save_mode = "SAVE"
                self.state = "SLOT_MENU"
                self.slots_data = self.load_all_slots()
                return

        # 4. Hub Interactions (The Main Fire Area)
        if self.current_room_coords == (0, 0):
            # A. The Main Fire
            if math.hypot(WIDTH//2 - self.player.pos_x, HEIGHT//2 - self.player.pos_y) < 70:
                if len(self.player.inventory) > 0:
                    # Feed fire manually
                    item = self.player.inventory.pop()
                    self.fire_health = min(MAX_FUEL, self.fire_health + 15)
                    desc = ARTIFACT_DATA.get(item, ["It burns."])
                    if isinstance(desc, list):
                        desc = random.choice(desc)
                    self.trigger_dialogue(f"NPC: \"{desc}\"", 120)
                else:
                    # Take a torch
                    self.player.carrying_torch = True
                    self.player.torch_health = 100.0
                    self.trigger_dialogue("Torch Lit.", 120)
                return

            # B. The NPC (Keeper)
            if p_rect.colliderect(self.npc.rect):
                # FIXED LOGIC: Check the STOCKPILE size, not player inventory
                if not self.automation_unlocked:
                    if len(self.wood_stockpile) >= 5:
                        self.automation_unlocked = True
                        self.trigger_dialogue(
                            "NPC: \"Good stockpile. I will keep the fire alive.\"", 180)
                    else:
                        self.trigger_dialogue(
                            "NPC: \"Stack 5 items in the pile, and I will help.\"", 120)
                else:
                    self.trigger_dialogue(
                        f"NPC: \"{self.npc.get_random_line()}\"", 120)
                return

            # C. The Stockpile (Wood Pile)
            if p_rect.colliderect(self.stockpile_rect):
                if len(self.player.inventory) > 0:
                    # Put item IN pile
                    item = self.player.inventory.pop()
                    self.wood_stockpile.append(item)
                    self.trigger_dialogue(f"Stored {item}", 60)
                elif len(self.wood_stockpile) > 0:
                    # Take item OUT of pile
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

        # Don't update game logic while in menu or saving
        if self.state != "PLAY":
            return

        if not self.crafting_open:
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

            # --- UPDATE ENEMIES ---
            for enemy in self.current_room.enemies:
                # CRITICAL CHANGE: We now pass the 'enemies' list as the second argument
                # This allows the wolf to see other wolves and push away from them.
                enemy.update(self.player, self.current_room.enemies)

            if self.player.hp <= 0:
                self.state = "GAME_OVER"
            # ---------------------------

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

        elif self.state in ["PLAY", "SLOT_MENU", "TYPING"]:
            self.draw_game()
            # Overlay menus if needed
            if self.state == "SLOT_MENU":
                self.draw_slot_menu()
            elif self.state == "TYPING":
                self.draw_typing_menu()

        elif self.state == "GAME_OVER":
            self.draw_game()
            o = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            o.fill((0, 0, 0, 200))
            self.screen.blit(o, (0, 0))
            t = self.title_font.render(
                "THE COLD TOOK YOU", True, COLOR_PYRE_LIT)
            self.screen.blit(t, (WIDTH//2 - t.get_width()//2, HEIGHT//2))

        pygame.display.flip()

    ### UI DRAWING METHODS ###
    def draw_slot_menu(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        title = self.title_font.render(
            f"{self.save_mode} GAME", True, (255, 255, 255))
        self.screen.blit(title, (WIDTH//2 - title.get_width()//2, 100))

        hint = self.font.render(
            "Press 1, 2, or 3 to Select | ENTER to Confirm | ESC to Cancel", True, (180, 180, 180))
        self.screen.blit(hint, (WIDTH//2 - hint.get_width()//2, HEIGHT - 50))

        # Draw 3 Slots
        start_y = 250
        for i in range(1, 4):
            slot_key = str(i)
            data = self.slots_data.get(slot_key)

            # Color Logic
            c = COLOR_SLOT_EMPTY
            if data:
                c = COLOR_SLOT_USED
            if self.selected_slot == i:
                c = COLOR_SLOT_HOVER

            # Box
            rect = pygame.Rect(WIDTH//2 - 200, start_y, 400, 80)
            pygame.draw.rect(self.screen, c, rect)
            pygame.draw.rect(self.screen, (255, 255, 255), rect, 2)  # Border

            # Text
            slot_name = "Empty"
            info = "--"
            if data:
                slot_name = data.get("name", f"Slot {i}")
                info = f"HP: {data.get('hp', 100)} | Fire: {int(data['fire'])}%"

            t1 = self.ui_title.render(
                f"{i}. {slot_name}", True, (255, 255, 255))
            t2 = self.font.render(info, True, (200, 200, 200))

            self.screen.blit(t1, (rect.x + 20, rect.y + 15))
            self.screen.blit(t2, (rect.x + 20, rect.y + 50))

            start_y += 100

    def draw_typing_menu(self):
        # Darken background
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))

        # Box
        center_x, center_y = WIDTH//2, HEIGHT//2
        pygame.draw.rect(self.screen, (30, 30, 30),
                         (center_x - 200, center_y - 100, 400, 200))
        pygame.draw.rect(self.screen, (255, 255, 255),
                         (center_x - 200, center_y - 100, 400, 200), 2)

        title = self.ui_title.render("NAME YOUR SAVE", True, (255, 255, 255))
        self.screen.blit(
            title, (center_x - title.get_width()//2, center_y - 70))

        # Input Field
        pygame.draw.rect(self.screen, (0, 0, 0),
                         (center_x - 150, center_y, 300, 40))

        # Blinking cursor logic
        txt = self.input_text
        if self.frame_count % 60 < 30:
            txt += "|"

        inp = self.font.render(txt, True, (255, 255, 255))
        self.screen.blit(inp, (center_x - 140, center_y + 10))

        help_t = self.font.render("Press ENTER to Save", True, (150, 150, 150))
        self.screen.blit(
            help_t, (center_x - help_t.get_width()//2, center_y + 60))
    ### -------------------------- ###

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

        # --- NEW: ADD ENEMIES TO RENDER LIST ---
        for e in self.current_room.enemies:
            render_list.append({"y": e.y, "type": "enemy", "obj": e})
        # ---------------------------------------

        # Draw Tent with offset (North of fire)
        tent_y = HEIGHT//2 - 80
        if self.current_room.has_tent:
            render_list.append({"y": tent_y, "type": "tent"})

        render_list.sort(key=lambda x: x['y'])

        for r in render_list:
            if r['type'] == "tent":
                self.screen.blit(
                    self.assets.images['tent'], (WIDTH//2 - 30, tent_y - 20))
            elif r['type'] == "item":
                self.screen.blit(self.assets.get_image(
                    r['obj'].name), r['obj'].rect)
            elif r['type'] == "echo":
                pygame.draw.circle(
                    self.screen, (200, 200, 255, 100), r['obj'].rect.center, 15)
            elif r['type'] == "enemy":
                r['obj'].draw(self.screen)
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

        # --- NEW: PLAYER HEALTH BAR ---
        pygame.draw.rect(self.screen, (50, 0, 0), (20, 50, 200, 20))
        ratio = max(0, self.player.hp / self.player.max_hp)
        pygame.draw.rect(self.screen, (0, 255, 0), (20, 50, 200*ratio, 20))
        hp_text = self.font.render(
            f"HP: {self.player.hp}", True, (255, 255, 255))
        self.screen.blit(hp_text, (25, 52))

        # Debug: Attack Box
        if self.player.is_attacking:
            r = self.player.get_attack_rect()
            pygame.draw.rect(self.screen, (255, 255, 255), r, 1)
        # -----------------------------

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
