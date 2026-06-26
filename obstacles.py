import pygame
import random
from config import *

class Obstacle:
    def __init__(self):
        self.x = WIDTH
        self.y = GROUND_Y
        self.width = random.choice([30, 40])
        self.height = random.choice([40, 60])
        self.speed = GAME_SPEED

    def update(self):
        self.x -= self.speed

    def draw(self, screen):
        pygame.draw.rect(screen, GREEN,
                         pygame.Rect(self.x,
                                     self.y + (60 - self.height),
                                     self.width,
                                     self.height))

    def off_screen(self):
        return self.x < -50