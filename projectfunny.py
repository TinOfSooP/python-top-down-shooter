# importing modules
import pygame
from pygame.locals import *
from sys import exit
import math
from settings import *

pygame.init()

# creating window
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("game project")
clock = pygame.time.Clock()
pygame.mouse.set_visible(False)

# create background
bg = pygame.transform.scale(pygame.image.load("grassbg.png").convert(), (SCREEN_WIDTH, SCREEN_HEIGHT))

# player class
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.transform.rotozoom(pygame.image.load("survivorpistol.png").convert_alpha(), 0, PLAYER_SIZE)
        self.pos = pygame.math.Vector2(PLAYERSTART_X, PLAYERSTART_Y*0.5)
        self.speed = PLAYER_SPEED

    def user_input(self):
        self.velocity_x = 0
        self.velocity_y = 0

        keys = pygame.key.get_pressed()
        
        if keys[pygame.K_w]:
            self.velocity_y = -self.speed
        if keys[pygame.K_a]:
            self.velocity_x = -self.speed
        if keys[pygame.K_s]:
            self.velocity_y = self.speed
        if keys[pygame.K_d]:
            self.velocity_x = self.speed            
    
    def move(self):
        self.pos += pygame.math.Vector2(self.velocity_x, self.velocity_y)
        self.hitbox.center = self.pos
        self.rect.center = self.hitbox.center

    def aim(self):
        self.mouse_pos = pygame.mouse.get_pos()
        self.dx = (self.mouse_pos[0] - self.hitbox.centerx)
        self.dy = (self.mouse_pos[1] - self.hitbox.centery)
        self.theta = math.degrees(math.atan2(self.dy, self.dx))
        self.image = pygame.transform.rotate(self.image, -self.theta)
        self.rect = self.image.get_rect(center = self.hitbox.center)

    def update(self):
        self.user_input()
        self.move()
        self.aim()

# crosshair class
class Crosshair(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.transform.rotozoom(pygame.image.load("crosshair.png").convert_alpha(), 0, CROSSHAIR_SIZE)
        self.rect = self.image.get_rect()
    
    def update(self):
        self.rect.center = pygame.mouse.get_pos()

player = Player()

crosshair = Crosshair()
crosshair_group = pygame.sprite.Group()
crosshair_group.add(crosshair)

# main loop
while True:
    keys = pygame.key.get_pressed()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()
    
    screen.blit(bg, (0, 0))
    screen.blit(player.image, player.rect)
    crosshair_group.draw(screen)
    crosshair_group.update()
    player.update()

    pygame.display.update()
    clock.tick(FPS)

