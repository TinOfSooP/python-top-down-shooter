# importing modules
import pygame
from pygame.locals import *
from sys import exit
import math
from random import randint
from settings import *
from weapons import *

# initialise pygame
pygame.init()

# create window
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("game project")
clock = pygame.time.Clock()
pygame.mouse.set_visible(False)

# load background image
bg = pygame.transform.scale(pygame.image.load("grassbg.png").convert(), (SCREEN_WIDTH, SCREEN_HEIGHT))

# load images outside of the class to avoid reloading unnecessarily
try:
    player_image = pygame.transform.rotozoom(pygame.image.load("survivorrifle.png").convert_alpha(), 0, PLAYER_SIZE)
    crosshair_image = pygame.transform.rotozoom(pygame.image.load("crosshair.png").convert_alpha(), 0, CROSSHAIR_SIZE)
    bullet_image = pygame.image.load("boolettrail.png").convert_alpha()
    enemy_image = pygame.transform.rotozoom(pygame.image.load("enemy.png").convert_alpha(), 0, ENEMY_SIZE)
    enemy_dead_image = pygame.transform.rotozoom(pygame.image.load("enemy_dead.png").convert_alpha(), 0, ENEMY_DEAD_SIZE)
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
        self.pos += pygame.math.Vector2(self.velocity_x, self.velocity_y)
        self.hitbox.center = self.pos
        self.rect.center = self.hitbox.center

    # point player sprite in direction of mouse pointer
    def aim(self):
        self.mouse_pos = pygame.mouse.get_pos()
        self.direction = pygame.math.Vector2(self.mouse_pos[0] - self.hitbox.centerx, self.mouse_pos[1] - self.hitbox.centery)
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
        self.enemy_hit = None
        self.source = source
        
    # spawn bullet
    def spawn(self):
        self.spawn_time = pygame.time.get_ticks()

        # introduce random factor 
        self.random_factor = randint(-BULLET_SPREAD, BULLET_SPREAD)
        self.velocity = pygame.Vector2(math.cos(math.radians(self.theta + self.random_factor)), math.sin(math.radians(self.theta + self.random_factor))) * self.speed

    # bullet movement
    def bullet_move(self):
        self.current_time = pygame.time.get_ticks()
        self.pos += self.velocity
        self.rect.center = self.pos
       
        if self.current_time - self.spawn_time > self.lifetime:
            self.kill()

    # check for collision with enemy
    def check_collision(self, sprite):
        if self.source == "player" and isinstance(sprite, Enemy) and not sprite.is_dead:
            sprite.die()

    # update bullet
    def update(self):
        self.spawn()
        self.bullet_move()

        self.collisions = pygame.sprite.spritecollide(self, all_sprites_group, False, pygame.sprite.collide_rect)
        for self.collision_sprite in self.collisions:
            if self.collision_sprite != self:
                if isinstance(self.collision_sprite, (Player, Crosshair)):
                    continue
                if isinstance(self.collision_sprite, Enemy):
                    if self.rect.colliderect(self.collision_sprite.hitbox):
                        self.check_collision(self.collision_sprite)
                        self.kill()

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
        self.direction = player.pos - self.pos
        self.distance = self.direction.length()

        # check for zero division error
        if self.distance > 0:
            self.direction.normalize_ip()
            self.pos += self.direction * min(self.distance, self.speed)

            # redefine the enemy rect
            self.rect.center = (int(self.pos.x), int(self.pos.y))
            self.hitbox.center = self.rect.center

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

# instantiate classes
player = Player()
crosshair = Crosshair()
enemy = Enemy()

# sprites groups and bullets group
all_sprites_group = pygame.sprite.Group()
enemy_group = pygame.sprite.Group()
bullet_group = pygame.sprite.Group()

# add sprites to groups
all_sprites_group.add(enemy)
enemy_group.add(enemy)
all_sprites_group.add(player)
all_sprites_group.add(crosshair)

# main loop
while True:
    keys = pygame.key.get_pressed()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()
    
    # blit background to the screen
    screen.blit(bg, (0, 0))

    # draw sprite groups
    all_sprites_group.draw(screen)
    all_sprites_group.update()

    pygame.display.update()
    clock.tick_busy_loop(FPS)

