import pygame

class Obstacle:
    def __init__(self, x, y, width, height, color=(150, 50, 50), lifespan=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color
        self.health = 100 # Placeholder for future combat/destruction
        self.lifespan = lifespan
        self.is_expired = False

    def update(self, dt):
        if self.lifespan is not None:
            self.lifespan -= dt
            if self.lifespan <= 0:
                self.is_expired = True

    def draw(self, surface):
        # Optional: Blink if expiring soon?
        draw_color = self.color
        if self.lifespan and self.lifespan < 3.0:
             if int(self.lifespan * 10) % 2 == 0:
                 draw_color = (255, 255, 255)
                 
        pygame.draw.rect(surface, draw_color, self.rect)
