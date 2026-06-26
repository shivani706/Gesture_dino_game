import pygame
from config import *

class Dino:
    def __init__(self):
        self.x = 80
        self.y = GROUND_Y
        self.vel_y = 0
        self.is_jumping = False
        self.is_ducking = False

        self.width = 50
        self.height = 60

    def jump(self):
        if not self.is_jumping:
            self.vel_y = -15
            self.is_jumping = True

    def duck(self, state):
        self.is_ducking = state

    def update(self):
        self.vel_y += GRAVITY
        self.y += self.vel_y

        if self.y >= GROUND_Y:
            self.y = GROUND_Y
            self.vel_y = 0
            self.is_jumping = False

    def get_rect(self):
        height = 35 if self.is_ducking else self.height
        return pygame.Rect(self.x, self.y + (self.height - height), self.width, height)

    def draw(self, screen):
        pygame.draw.rect(screen, BLACK, self.get_rect())