import pygame
import random
from config import *
from dino import Dino
from obstacles import Obstacle

class Game:
    def __init__(self):
        self.dino = Dino()
        self.obstacles = []
        self.score = 0
        self.spawn_timer = 0
        self.game_over = False

    def update(self):
        if self.game_over:
            return

        self.dino.update()

        self.spawn_timer += 1
        if self.spawn_timer > 90:
            self.obstacles.append(Obstacle())
            self.spawn_timer = 0

        for obs in self.obstacles:
            obs.update()
            if obs.x < self.dino.x:
                self.score += 1

        self.obstacles = [o for o in self.obstacles if not o.off_screen()]

        # Collision
        for obs in self.obstacles:
            if self.dino.get_rect().colliderect(
                pygame.Rect(obs.x,
                            obs.y + (60 - obs.height),
                            obs.width,
                            obs.height)
            ):
                self.game_over = True

    def draw(self, screen):
        screen.fill(WHITE)

        pygame.draw.line(screen, BLACK, (0, 400), (WIDTH, 400), 3)

        self.dino.draw(screen)

        for obs in self.obstacles:
            obs.draw(screen)

        font = pygame.font.SysFont("Arial", 25)
        score_text = font.render(f"Score: {self.score}", True, BLACK)
        screen.blit(score_text, (20, 20))

        if self.game_over:
            over = font.render("GAME OVER", True, (200, 0, 0))
            screen.blit(over, (WIDTH//2 - 80, HEIGHT//2))