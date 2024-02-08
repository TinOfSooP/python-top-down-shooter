# importing modules
import pygame
from pygame.locals import *
from sys import exit
import math
from random import randint
from settings import *

# initialise pygame
pygame.init()

# create window
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("game project")
clock = pygame.time.Clock()

# load images outside of the class to avoid reloading unnecessarily
try:
    player_image = pygame.transform.rotozoom(pygame.image.load("player/survivorrifle.png").convert_alpha(), 0, PLAYER_SIZE)
    crosshair_image = pygame.transform.rotozoom(pygame.image.load("crosshair.png").convert_alpha(), 0, CROSSHAIR_SIZE)
    kill_indicator_image = pygame.transform.rotozoom(pygame.image.load("kill_indicator.png").convert_alpha(), 0, KILL_INDICATOR_SIZE)
    bullet_image = pygame.image.load("bullets/boolettrail.png").convert_alpha()
    enemy_image = pygame.transform.rotozoom(pygame.image.load("enemy.png").convert_alpha(), 0, ENEMY_SIZE)
    enemy_dead_image = pygame.transform.rotozoom(pygame.image.load("enemy_dead.png").convert_alpha(), 0, ENEMY_DEAD_SIZE)
    drop_gun_image = pygame.transform.rotozoom(pygame.image.load("enemy_gun.png").convert_alpha(), 0, DROP_WEAPON_SIZE)
except pygame.error as e:
    print("Error loading images", e)
    pygame.quit()
    exit()

# player class
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = player_image.copy()
        self.pos = pygame.math.Vector2(PLAYERSTART_X, PLAYERSTART_Y*0.5)

        # create copy of original, non-transformed image
        self.default = self.image
        self.hitbox_size = pygame.Vector2(80, 80)
        self.hitbox_offset = pygame.Vector2(-self.hitbox_size.x // 2, -self.hitbox_size.y // 2)

        # calculate hitbox rect
        self.hitbox = pygame.Rect(self.pos.x + self.hitbox_offset.x, self.pos.y + self.hitbox_offset.y, self.hitbox_size.x, self.hitbox_size.y)
        self.rect = self.hitbox.copy()
        self.speed = PLAYER_SPEED
        self.shoot = False
        self.shoot_cooldown = 0
        self.ammo = AMMO_COUNT
        self.theta = 0

    # detect user input
    def user_input(self):
        self.velocity_x = 0
        self.velocity_y = 0

        # check for key presses
        keys = pygame.key.get_pressed()

        if keys[pygame.K_w]:
            self.velocity_y = -self.speed
        if keys[pygame.K_a]:
            self.velocity_x = -self.speed
        if keys[pygame.K_s]:
            self.velocity_y = self.speed
        if keys[pygame.K_d]:
            self.velocity_x = self.speed

        # check for diagonal movement
        if self.velocity_x != 0 and self.velocity_y != 0:
            self.velocity_x /= math.sqrt(2)
            self.velocity_y /= math.sqrt(2)

        # check for mouse button presses
        if pygame.mouse.get_pressed() == (1, 0, 0):
            self.shoot = True
            self.is_shooting()
        else:
            self.shoot = False

    # move character
    def move(self):
        # save current position
        self.original_pos = self.pos.copy()

        # move player
        self.pos += pygame.math.Vector2(self.velocity_x, self.velocity_y)
        self.hitbox.center = self.pos
        self.rect.center = self.hitbox.center

        # check if player is moving into a wall
        if tile_map.is_wall(self.rect.centerx, self.rect.centery):
            self.pos = self.original_pos
            self.hitbox.center = self.pos
            self.rect.center = self.hitbox.center

    # point player sprite in direction of mouse pointer
    def aim(self):
        self.mouse_pos = pygame.mouse.get_pos()
        self.direction = pygame.math.Vector2(self.mouse_pos[0] - SCREEN_WIDTH // 2, self.mouse_pos[1] - SCREEN_HEIGHT // 2)
        self.theta = math.degrees(math.atan2(self.direction.y, self.direction.x))
        self.image = pygame.transform.rotate(self.default, -self.theta)
        self.rect = self.image.get_rect(center = self.hitbox.center)

    # refresh shooting cooldown
    def is_shooting(self):
        if self.shoot_cooldown == 0 and self.shoot and self.ammo > 0:
            self.shoot_cooldown = SHOOT_COOLDOWN
            self.create_bullet()

            # change ammo counter
            self.ammo -= 1
            self.ammo_counter()

    # instantiate a bullet
    def create_bullet(self):
        self.gun_offset = pygame.math.Vector2(GUN_OFFSET_X, GUN_OFFSET_Y)
        self.rotated_gun_offset = self.gun_offset.rotate(self.theta)
        bullet_pos = self.pos + self.rotated_gun_offset
        bullet_rect = bullet_image.get_rect(center=(bullet_pos.x, bullet_pos.y))

        if not tile_map.is_wall(bullet_rect.centerx, bullet_rect.centery):
            self.bullet = Bullet(bullet_pos.x, bullet_pos.y, self.theta, bullet_image, source="player")

            # add bullet to all sprites and bullet group
            all_sprites_group.add(self.bullet)
            bullet_group.add(self.bullet)

    # check for collision between player and gun drop
    def ammo_pickup(self):
        collisions = pygame.sprite.spritecollide(self, drops_group, True)
        for weapon in collisions:
            self.ammo = AMMO_COUNT

    # display ammo counter with outline
    def ammo_counter(self):
        outline_text(72, "Ammo: {}".format(self.ammo), 130, SCREEN_HEIGHT - 35)

    # draw player hitbox for debugging
    def draw_hitbox(self, surface, camera_offset):
        adjusted_hitbox = self.hitbox.move(-camera_offset[0], -camera_offset[1])
        pygame.draw.rect(surface, RED, adjusted_hitbox, 2)

    # update player
    def update(self):
        self.user_input()
        self.move()
        self.aim()
        self.ammo_pickup()

        # reduce time before next shot each tick
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

# crosshair class
class Crosshair(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = crosshair_image.copy()
        self.kill_indicator_image = kill_indicator_image.copy()
        self.rect = self.image.get_rect()
        self.lifespan = 10

    # show kill indicator when enemy is killed
    def show_kill_indicator(self):
        self.image = self.kill_indicator_image
        self.kill_indicator_time = pygame.time.get_ticks()
        
    # update crosshair
    def update(self):
        self.rect.center = pygame.mouse.get_pos()
        if self.image == self.kill_indicator_image:
            self.lifespan -= 1
            if self.lifespan <= 0:
                self.lifespan = 10
                self.image = crosshair_image.copy()

# bullet class
class Bullet(pygame.sprite.Sprite):
    def __init__(self, x ,y, theta, image, source):
        super().__init__()
        self.image = pygame.transform.rotozoom(image, -theta, BULLET_SIZE)
        self.rect = self.image.get_rect(center=(x, y))
        self.pos = pygame.Vector2(x, y)
        self.theta = theta
        self.speed = BULLET_SPEED
        self.lifetime = BULLET_LIFETIME
        self.spawn_time = pygame.time.get_ticks()
        self.source = source

    # spawn bullet with random factor
    def spawn(self):
        self.random_factor = randint(-BULLET_SPREAD, BULLET_SPREAD)
        self.velocity = pygame.Vector2(math.cos(math.radians(self.theta + self.random_factor)), math.sin(math.radians(self.theta + self.random_factor))) * self.speed

    # bullet movement
    def bullet_move(self):
        self.current_time = pygame.time.get_ticks()
        self.pos += self.velocity
        self.rect.center = self.pos

        if pygame.time.get_ticks() - self.spawn_time > self.lifetime:
            self.kill()

    # check for collision with wall
    def check_wall_collision(self):
       if tile_map.is_wall(self.rect.centerx, self.rect.centery):
           self.kill()

    # check for collision with enemies
    def check_enemy_collision(self, sprite):
        if self.source == "player" and isinstance(sprite, Enemy) and not sprite.is_dead:
            if self.rect.colliderect(sprite.hitbox):
                sprite.die()
                self.kill()

    # check for collision with player
    def check_player_collision(self, player):
        if self.source == "enemy" and isinstance(player, Player):
            if self.rect.colliderect(player.hitbox):
                player.kill()
                self.kill()

    # update bullet
    def update(self):
        self.spawn()
        self.bullet_move()

        # check for collision with wall
        self.check_wall_collision()

        # check for collision with enemies
        self.collisions = pygame.sprite.spritecollide(self, all_sprites_group, False, pygame.sprite.collide_rect)
        for collision_sprite in self.collisions:
            if collision_sprite != self:
                if isinstance(collision_sprite, (Player)):
                    self.check_player_collision(collision_sprite)
                elif isinstance(collision_sprite, Enemy):
                    self.check_enemy_collision(collision_sprite)

# dropped weapon class
class DroppedWeapon(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = drop_gun_image.copy()
        self.rect = self.image.get_rect(center=(x, y))

    def update(self):
        pass

# enemy class
class Enemy(pygame.sprite.Sprite):
    def __init__(self, spawn_location):
        super().__init__()
        self.image = enemy_image.copy()
        self.pos = pygame.math.Vector2(spawn_location)

        # create copy of original, non-transformed image
        self.default = self.image
        self.hitbox = self.default.get_rect(center = self.pos)
        self.rect = self.hitbox.copy()
        self.speed = ENEMY_SPEED
        self.enemy_theta = 0
        self.reaction_time = ENEMY_REACTION_TIME
        self.enemy_shoot_cooldown = 0
        self.is_dead = False

    # move enemy
    def move(self):
        # save current position
        self.original_pos = self.pos.copy()

        self.direction = player.pos - self.pos
        self.distance = self.direction.length()

        # # check for zero division error
        # if self.distance > 0:
        #     self.direction.normalize_ip()
        #     self.pos += self.direction * min(self.distance, self.speed)

        #     # redefine the enemy rect
        #     self.rect.center = (int(self.pos.x), int(self.pos.y))
        #     self.hitbox.center = self.rect.center

        #     # check for wall collision
        #     if tile_map.is_wall(self.rect.centerx, self.rect.centery):
        #         self.pos = self.original_pos
        #         self.hitbox.center = self.pos
        #         self.rect.center = self.hitbox.center

    # aim enemy
    def aim(self):
        self.enemy_theta = self.direction.angle_to(pygame.math.Vector2(1, 0))
        self.image = pygame.transform.rotate(self.default, self.enemy_theta)
        self.rect = self.image.get_rect(center = self.hitbox.center)

    # enemy shooting logic
    def shoot(self):
        if self.enemy_shoot_cooldown == 0:
            self.enemy_shoot_cooldown = ENEMY_SHOOT_COOLDOWN
            self.create_bullet()

    # create bullet
    def create_bullet(self):
        self.enemy_theta = math.atan2(self.direction.y, self.direction.x)
        self.bullet_pos = self.pos + pygame.math.Vector2(ENEMY_GUN_OFFSET_X, ENEMY_GUN_OFFSET_Y).rotate(math.degrees(self.enemy_theta))
        bullet_rect = bullet_image.get_rect(center=(self.bullet_pos.x, self.bullet_pos.y))

        if not tile_map.is_wall(bullet_rect.centerx, bullet_rect.centery):
            # instantiate enemy bullet
            self.bullet = Bullet(self.bullet_pos.x, self.bullet_pos.y, math.degrees(self.enemy_theta), bullet_image, source="enemy")
            all_sprites_group.add(self.bullet)
            bullet_group.add(self.bullet)

    def has_line_of_sight(self, player_rect):
        # calculate line segment between player and enemy rects
        ray_cast = pygame.math.Vector2(player_rect.center) - pygame.math.Vector2(self.rect.center)

        # iterate over tiles in line of sight and check for walls
        for i in range(int(ray_cast.length())):
            current_tile = pygame.math.Vector2(self.rect.center) + ray_cast.normalize() * i
            tile_x = int(current_tile.x // TILE_SIZE)
            tile_y = int(current_tile.y // TILE_SIZE)

            # check if current tile is a wall
            if 0 <= tile_y < len(tile_map.tile_data) and 0 <= tile_x < len(tile_map.tile_data[0]) and tile_map.tile_data[tile_y][tile_x]:
                return False

        return True

    # swap to dead sprite and remove collider
    def die(self):
        self.is_dead = True
        self.image = pygame.transform.rotate(enemy_dead_image, -self.enemy_theta)
        self.hitbox = pygame.Rect(0, 0, 0, 0)
        enemy_group.remove(self)
        crosshair.show_kill_indicator()

        # probability for enemy to drop a gun
        if randint(1, 100) <= DROP_CHANCE:
            dropped_weapon = DroppedWeapon(self.pos.x, self.pos.y)
            all_sprites_group.add(dropped_weapon)
            drops_group.add(dropped_weapon)

    # draw hitbox for debugging
    def draw_hitbox(self, surface, camera_offset):
        drawn_hitbox = self.hitbox.move(-camera_offset[0], -camera_offset[1])
        pygame.draw.rect(surface, RED, drawn_hitbox, 2)

    # update enemy
    def update(self):
        if not self.is_dead:
            # self.draw_hitbox(screen, camera.offset)
            self.move()
            los_result = self.has_line_of_sight(player.rect)

            # if enemy has line of sight to the player
            if los_result:
                self.reaction_time -= 1
                if self.reaction_time <= 0:
                    self.aim()
                    self.shoot()
            
            # otherwise refresh reaction time
            else:
                self.reaction_time = ENEMY_REACTION_TIME

            # reduce cooldown
            if self.enemy_shoot_cooldown > 0:
                self.enemy_shoot_cooldown -= 1

# camera class
class Camera(pygame.sprite.Group):
    def __init__(self, tile_map):
        super().__init__()
        self.offset = pygame.math.Vector2()
        self.tile_map = tile_map

    # move camera
    def move_camera(self):
        target_x = player.rect.centerx - SCREEN_WIDTH / 2
        target_y = player.rect.centery - SCREEN_HEIGHT / 2

        self.offset.x = target_x
        self.offset.y = target_y

    def draw(self, surface):
        self.tile_map.draw(surface, position=(-self.offset.x, -self.offset.y))

# tile map class
class TileMap(pygame.sprite.Sprite):
    def __init__(self, map_filename):
        super().__init__()

        # open and read data from map file
        with open(map_filename, "r") as f:
            map_data = []
            for line in f.readlines():
                map_data.append(line.strip())

        # calculate map width and length
        map_width = len(map_data[0])
        map_length = len(map_data)

        # create surface to hold tiles
        self.image = pygame.Surface((map_width * TILE_SIZE, map_length * TILE_SIZE))
        self.rect = self.image.get_rect()

        self.tile_data = []
        self.enemy_spawn_locations = []
        self.player_spawn_location = []

        # iterate through map data
        for y, map_line in enumerate(map_data):
            tile_row = []
            for x, map_symbol in enumerate(map_line):
                tile_rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)

                # draw green tile if symbol is #
                if map_symbol == "#":
                    pygame.draw.rect(self.image, GREEN, tile_rect)
                    tile_row.append(True)

                # spawn enemy on tile if symbol is E
                elif map_symbol == "E":
                    tile_row.append(False)  
                    self.enemy_spawn_locations.append((x * TILE_SIZE, y * TILE_SIZE))

                # spawn player on tile if symbol is P
                elif map_symbol == "P":
                    tile_row.append(False)
                    self.player_spawn_location.append((x * TILE_SIZE, y * TILE_SIZE))

                # spawn exit tile if symbol is X
                elif map_symbol == "X":
                    pygame.draw.rect(self.image, RED, tile_rect)
                    tile_row.append(True)
                    self.exit_tile_location = (x * TILE_SIZE, y * TILE_SIZE)
                    break

                else:
                    tile_row.append(False)
            self.tile_data.append(tile_row)
                
    # check if tile is within range and if type is a wall
    def is_wall(self, x, y):
        tile_x = int(x // TILE_SIZE)
        tile_y = int(y // TILE_SIZE)

        # return true if wall, false if not
        return 0 <= tile_y < len(self.tile_data) and 0 <= tile_x < len(self.tile_data[0]) and self.tile_data[tile_y][tile_x]#
    
    # return enemy spawn locations
    def get_enemy_spawn_locations(self):
        return self.enemy_spawn_locations

    # draw the map
    def draw(self, surface, position=(0,0)):
        self.rect.topleft = position
        surface.blit(self.image, self.rect)

start_time = 0

# restart game after death
def new_game():
    global player, enemy, game_paused, start_time
    game_paused = False

    # kill all relevant sprites
    for i in all_sprites_group:
        i.kill()

    # empty all relevant sprite groups
    all_sprites_group.empty()
    enemy_group.empty()
    bullet_group.empty()

    start_time = pygame.time.get_ticks()

    # respawn all relevant sprites at initial positions
    player = Player()
    all_sprites_group.add(player)
    if tile_map.player_spawn_location:
        player.pos = pygame.math.Vector2(tile_map.player_spawn_location[0])

    enemy_spawn_locations = tile_map.get_enemy_spawn_locations()
    enemy = [Enemy(spawn_location) for spawn_location in enemy_spawn_locations]
    for i in enemy:
        enemy_group.add(enemy)
        all_sprites_group.add(enemy)

# draw timer with outline
def draw_timer(elapsed_time):
    outline_text(72, "{:.2f}".format(elapsed_time / 1000), SCREEN_WIDTH // 2, 50)

# outline text
def outline_text(font_size, content, x, y):
    font = pygame.font.SysFont(None, font_size)

    text_surface = font.render(content, True, (BLACK))

    offsets = [(-1, -1), (1, -1), (-1, 1), (1, 1)]

    for offset in offsets:
        text_rect = text_surface.get_rect(center=(x + offset[0], y + offset[1]))
        screen.blit(text_surface, text_rect)

    text_surface = font.render(content, True, (WHITE))
    text_rect = text_surface.get_rect(center=(x, y))
    screen.blit(text_surface, text_rect)

# controls screen
def controls_screen(screen):
    font = pygame.font.Font(None, 56)
    controls_text = [
        "Controls:",
        "Move - SADW",
        "Shoot - LMB",
        "Restart - R",
        "Exit to menu - Esc",

        "",
        "Aim:",
        "Eliminate all enemies on the map then reach the exit",

        "",
        "Tips:",
        "- Use your birds-eye view to scout out enemies",
        "- Peek enemies quickly or get your head blown off",
        "- Avoid long corridors or find out why...",
        "- Running out of ammo is a bad idea",

        "",
        "Don't forget:",
        "You die in 1 hit... but so do the enemies!",
    ]
    screen.fill(BLACK)
    text_y = 50
    for line in controls_text:
        text_surface = font.render(line, True, WHITE)
        screen.blit(text_surface, (50, text_y))
        text_y += 50

    pygame.display.update()

# display end screen
def end_screen(elapsed_time):
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if button_rect.collidepoint(event.pos):
                    record_time(elapsed_time)
                    return False

        # clear the screen
        screen.fill(BLACK)

        # display end screen message
        pygame.mouse.set_visible(True)
        font = pygame.font.SysFont(None, 40)
        text_surface = font.render("Stage Completed", True, WHITE)
        text_rect = text_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
        screen.blit(text_surface, text_rect)

        # display time to 2 decimal places
        time_text = "Your time: {:.2f} seconds".format(elapsed_time / 1000)
        time_surface = font.render(time_text, True, WHITE)
        time_rect = time_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        screen.blit(time_surface, time_rect)

        # display button to return to menu
        button_rect = pygame.Rect((SCREEN_WIDTH - BUTTON_WIDTH) // 2, (SCREEN_HEIGHT + 100) // 2, BUTTON_WIDTH, BUTTON_HEIGHT)
        pygame.draw.rect(screen, GREEN, button_rect)
        button_text = font.render('Main Menu', True, WHITE)
        button_text_rect = button_text.get_rect(center=button_rect.center)
        screen.blit(button_text, button_text_rect)

        pygame.display.update()

# instantiate classes
tile_map = TileMap("map1.txt")
camera = Camera(tile_map)

# spawn player at tilemap location
player = Player()
if tile_map.player_spawn_location:
    player.pos = pygame.math.Vector2(tile_map.player_spawn_location[0])

# create crosshair
crosshair = Crosshair()

# spawn enemies from the tilemap locations
enemy_spawn_locations = tile_map.get_enemy_spawn_locations()
enemy = [Enemy(spawn_location) for spawn_location in enemy_spawn_locations]

# sprite groups and bullets group
all_sprites_group = pygame.sprite.Group()
enemy_group = pygame.sprite.Group()
bullet_group = pygame.sprite.Group()
crosshair_group = pygame.sprite.Group()
tile_map_group = pygame.sprite.GroupSingle()
drops_group = pygame.sprite.Group()

# add sprites to groups
for i in enemy:
    enemy_group.add(enemy)
    all_sprites_group.add(enemy)
all_sprites_group.add(player)
crosshair_group.add(crosshair)
tile_map_group.add(tile_map)

# record time to file
def record_time(elapsed_time):
    with open("times.txt", "a") as file:
        file.write(str(elapsed_time) + "\n")

# read top 5 times
def read_top_times():
    with open("times.txt", "r") as file:
        lines = file.readlines()
        top_times = [float(line.strip()) for line in lines]
        top_times.sort()
        return top_times[:5]

# main menu screen
def main_menu():
    show_controls = False
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if start_button_rect.collidepoint(event.pos):
                    pygame.time.delay(100)
                    new_game()
                    return True
                elif controls_button_rect.collidepoint(event.pos):
                    print("Controls button clicked")
                    show_controls = True
                    pygame.display.update()
                elif quit_button_rect.collidepoint(event.pos):
                    pygame.quit()
                    exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    show_controls = False

        # configure window
        screen.fill(BLACK)
        pygame.mouse.set_visible(True)

        # create start and quit buttons
        start_button_rect = pygame.Rect((SCREEN_WIDTH - BUTTON_WIDTH) // 2, (SCREEN_HEIGHT - BUTTON_HEIGHT) // 2, BUTTON_WIDTH, BUTTON_HEIGHT)
        controls_button_rect = start_button_rect.copy()
        controls_button_rect.y += BUTTON_HEIGHT + BUTTON_SPACING
        quit_button_rect = start_button_rect.copy()
        quit_button_rect.y += 2 * BUTTON_HEIGHT + 2 * BUTTON_SPACING

        # draw start button
        pygame.draw.rect(screen, (GREEN), start_button_rect)
        font = pygame.font.Font(None, 36)
        start_text = font.render('Start Game', True, (WHITE))
        start_text_rect = start_text.get_rect(center=start_button_rect.center)
        screen.blit(start_text, start_text_rect)

        # draw controls button
        pygame.draw.rect(screen, (GREEN), controls_button_rect)
        controls_text = font.render('Controls', True, (WHITE))
        controls_text_rect = controls_text.get_rect(center=controls_button_rect.center)
        screen.blit(controls_text, controls_text_rect)

        # draw quit button
        pygame.draw.rect(screen, (GREEN), quit_button_rect)
        quit_text = font.render('Quit', True, (WHITE))
        quit_text_rect = quit_text.get_rect(center=quit_button_rect.center)
        screen.blit(quit_text, quit_text_rect)

        # display top 5 times
        top_times_rect = pygame.Rect(50, (SCREEN_HEIGHT - 400) // 2, 200, 400)
        pygame.draw.rect(screen, BLACK, top_times_rect)
        font = pygame.font.Font(None, 28)
        label_text = font.render('Top 5 Times', True, WHITE)
        label_text_rect = label_text.get_rect(center=(top_times_rect.centerx, top_times_rect.y + 30))
        screen.blit(label_text, label_text_rect)

        # read top 5 times from file
        top_times = read_top_times()
        if top_times:
            text_y = label_text_rect.bottom + 20
            for idx, time in enumerate(top_times, start=1):
                time_text = font.render(f'{idx}. {time / 1000:.2f} seconds', True, WHITE)
                time_text_rect = time_text.get_rect(center=(top_times_rect.centerx, text_y))
                screen.blit(time_text, time_text_rect)
                text_y += 30

        if show_controls:
            controls_screen(screen)

        pygame.display.update()

if not main_menu():
    pygame.quit()
    exit()

# main game loop
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if game_paused:
                    game_paused = False
                elif not main_menu():
                    pygame.quit()
                    exit()

    keys = pygame.key.get_pressed()

    # handle player alive and game running
    if player.alive() and not game_paused:
        pygame.mouse.set_visible(False)

        # clear screen
        screen.fill(BLACK)

        # move camera and draw map
        camera.move_camera()
        camera.draw(screen)

        # draw sprites
        all_sprites_group.update()

        # draw other sprites
        for sprite in all_sprites_group:
            if sprite != player:
                offset_pos = sprite.rect.topleft - camera.offset
                screen.blit(sprite.image, offset_pos)

        # draw player at the center of the screen
        offset_pos = player.rect.topleft - camera.offset
        screen.blit(player.image, offset_pos)

        # draw hitboxes for testing and debugging
        # player.draw_hitbox(screen, camera.offset)

        # update timer
        current_time = pygame.time.get_ticks()
        elapsed_time = current_time - start_time

        # draw timer
        draw_timer(elapsed_time)

        # draw crosshair
        screen.blit(crosshair.image, crosshair.rect)
        crosshair_group.update()

        # refresh ammo counter value
        player.ammo_counter()

        # check if player has reached exit and all enemies are killed
        if tile_map.exit_tile_location and player.rect.collidepoint(tile_map.exit_tile_location) and len(enemy_group) == 0:
            # calculate elapsed time
            elapsed_time = pygame.time.get_ticks() - start_time

            # return to main menu
            if not end_screen(elapsed_time):
                main_menu()

        pygame.display.update()
        clock.tick_busy_loop(FPS)

    # handle player dead or game paused
    else:
        outline_text(40, "Press R to restart", SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        pygame.display.update()

        # check for key presses
        if keys[pygame.K_r]:
            # restart game
            new_game()
            game_paused = False
        elif keys[pygame.K_ESCAPE]:
            # return to main menu
            if not main_menu():
                pygame.quit()
                exit()
