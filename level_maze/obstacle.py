import pygame

class Obstacle:
    def __init__(self, x, y, width, height, color=(150, 50, 50)):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color
        self.health = 100 # Placeholder for future combat/destruction

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect)
