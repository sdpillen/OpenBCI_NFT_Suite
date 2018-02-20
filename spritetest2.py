#!/usr/bin/python

import pygame
from pygame.locals import KEYDOWN

width  = 320
height = 240
size   = [width, height]
pygame.init()
screen = pygame.display.set_mode(size)
background = pygame.Surface(screen.get_size())
print(background)

b = pygame.sprite.Sprite() # create sprite
b.image = pygame.image.load("ball.png").convert() # load ball image
b.image.convert_alpha()
b.rect = b.image.get_rect() # use image extent values
b.rect.topleft = [0, 0] # put the ball in the top left corner
screen.blit(b.image, b.rect)
print(b.rect.y)
print(b.rect.x)

pygame.display.update()
while pygame.event.poll().type != KEYDOWN:
    pygame.time.delay(100)