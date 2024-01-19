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
pygame.mouse.set_visible(False)

# load images outside of the class to avoid reloading unnecessarily
try:
    player_image = pygame.transform.rotozoom(pygame.image.load("player/survivorrifle.png").convert_alpha(), 0, PLAYER_SIZE)
    crosshair_image = pygame.transform.rotozoom(pygame.image.load("crosshair.png").convert_alpha(), 0, CROSSHAIR_SIZE)
    bullet_image = pygame.image.load("bullets/boolettrail.png").convert_alpha()
    enemy_image = pygame.transform.rotozoom(pygame.image.load("enemy.png").convert_alpha(), 0, ENEMY_SIZE)
    enemy_dead_image = pygame.transform.rotozoom(pygame.image.load("enemy_dead.png").convert_alpha(), 0, ENEMY_DEAD_SIZE)
    wall_image = pygame.transform.rotozoom(pygame.image.load("wall.png").convert_alpha(), 0, TILE_SIZE)
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
        self.hitbox = self.default.get_rect(center = self.pos)
        self.rect = self.hitbox.copy()
        self.speed = PLAYER_SPEED
        self.shoot = False
        self.shoot_cooldown = 0

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
        if self.shoot_cooldown == 0 and self.shoot:
            self.shoot_cooldown = SHOOT_COOLDOWN
            self.create_bullet()

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

    # update player
    def update(self):
        self.user_input()
        self.move()
        self.aim()

        # reduce time before next shot each tick
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

# crosshair class
class Crosshair(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = crosshair_image.copy()
        self.rect = self.image.get_rect()

    # update crosshair
    def update(self):
        self.rect.center = pygame.mouse.get_pos()

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
        self.enemy_hit = None
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
            sprite.die()
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
                if isinstance(collision_sprite, (Player, Crosshair)):
                    continue
                if isinstance(collision_sprite, Enemy):
                    self.check_enemy_collision(collision_sprite)

# enemy class
class Enemy(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = enemy_image.copy()
        self.pos = pygame.math.Vector2(randint(0, SCREEN_WIDTH), randint(0, SCREEN_HEIGHT))

        # create copy of original, non-transformed image
        self.default = self.image
        self.hitbox = self.default.get_rect(center = self.pos)
        self.rect = self.hitbox.copy()
        self.speed = ENEMY_SPEED
        self.enemy_shoot_cooldown = 0
        self.is_dead = False

    # move enemy
    def move(self):
        # save current position
        self.original_pos = self.pos.copy()

        self.direction = player.pos - self.pos
        self.distance = self.direction.length()

        # check for zero division error
        if self.distance > 0:
            self.direction.normalize_ip()
            self.pos += self.direction * min(self.distance, self.speed)

            # redefine the enemy rect
            self.rect.center = (int(self.pos.x), int(self.pos.y))
            self.hitbox.center = self.rect.center

            # check for wall collision
            if tile_map.is_wall(self.rect.centerx, self.rect.centery):
                self.pos = self.original_pos
                self.hitbox.center = self.pos
                self.rect.center = self.hitbox.center

    # aim enemy
    def aim(self):
        self.enemy_theta = math.degrees(math.atan2(self.direction.y, self.direction.x))
        self.image = pygame.transform.rotate(self.default, -self.enemy_theta)
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

    # die
    def die(self):
        self.is_dead = True
        self.image = pygame.transform.rotate(enemy_dead_image, -self.enemy_theta)
        self.hitbox = pygame.Rect(0, 0, 0, 0)

    # update enemy
    def update(self):
        if not self.is_dead:
            self.move()
            self.aim()
            self.shoot()

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

    def draw(self, surface, position=(0, 0)):
        self.tile_map.draw(surface, position=(-self.offset.x, -self.offset.y))

# tile map class
class TileMap(pygame.sprite.Sprite):
    def __init__(self, map_filename):
        super().__init__()

        # open and read data from map file
        with open(map_filename, "r") as file:
            map_data = [line.strip() for line in file.readlines()]

        map_width = len(map_data[0])
        map_length = len(map_data)

        # create surface to hold tiles
        self.image = pygame.Surface((map_width * TILE_SIZE, map_length * TILE_SIZE))
        self.rect = self.image.get_rect()

        # create wall surface
        wall_surface = pygame.Surface((TILE_SIZE, TILE_SIZE))
        wall_surface.fill(GREEN)

        # iterate through map data to convert each character to a tile
        for y, map_line in enumerate(map_data):
            for x, map_symbol in enumerate(map_line):
                tile_rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                if map_symbol == '#':
                    self.image.blit(wall_surface, tile_rect.topleft)

        # initial position of tile map
        self.rect.topleft = (0, 0)

        # create tile data
        self.tile_data = [[True if char == '#' else False for char in line] for line in map_data]

    # check if tile type is a wall
    def is_wall(self, x, y):
        tile_x = int(x // TILE_SIZE)
        tile_y = int(y // TILE_SIZE)

        # return true if wall, false if not
        return 0 <= tile_y < len(self.tile_data) and 0 <= tile_x < len(self.tile_data[0]) and self.tile_data[tile_y][tile_x]

    # draw the map
    def draw(self, surface, position=(0,0)):
        self.rect.topleft = position
        surface.blit(self.image, self.rect)

# instantiate classes
tile_map = TileMap("map1.txt")
camera = Camera(tile_map)
player = Player()
crosshair = Crosshair()
enemy = Enemy()

# sprite groups and bullets group
all_sprites_group = pygame.sprite.Group()
enemy_group = pygame.sprite.Group()
bullet_group = pygame.sprite.Group()
crosshair_group = pygame.sprite.Group()
tile_map_group = pygame.sprite.GroupSingle()

# add sprites to groups
all_sprites_group.add(enemy)
enemy_group.add(enemy)
all_sprites_group.add(player)
crosshair_group.add(crosshair)
tile_map_group.add(tile_map)

# main loop
while True:
    keys = pygame.key.get_pressed()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()

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

    # draw crosshair
    screen.blit(crosshair.image, crosshair.rect)
    crosshair_group.update()

    pygame.display.update()
    clock.tick_busy_loop(FPS)

