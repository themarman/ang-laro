import pygame

class Xtra:
    def __init__(self, x, y, width, height, lifetime=10.0):
        self.rect = pygame.Rect(x, y, width, height)
        self.lifetime = lifetime
        self.color = (255, 255, 255) # Default
        self.active = True

    def update(self, dt):
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.active = False

    def draw(self, surface):
        if self.active:
            pygame.draw.rect(surface, self.color, self.rect)
    
    def on_collect(self, entity):
        pass

class HealthPack(Xtra):
    def __init__(self, x, y):
        super().__init__(x, y, 20, 20, lifetime=10.0)
        self.color = (0, 255, 0)
        self.value = 50 

    def draw(self, surface):
        if self.active:
            super().draw(surface)
            # Draw Cross symbol
            center = self.rect.center
            pygame.draw.line(surface, (255, 255, 255), (center[0] - 5, center[1]), (center[0] + 5, center[1]), 3)
            pygame.draw.line(surface, (255, 255, 255), (center[0], center[1] - 5), (center[0], center[1] + 5), 3)

    def on_collect(self, entity):
        # Entity must have health
        if hasattr(entity, 'health'):
            restore = self.value
            # Check if player or enemy (simple class name check or prop)
            # GDD: Player 100%, Enemy 50%
            is_player = hasattr(entity, 'flash_dash') or type(entity).__name__ == 'Player' # Hacky check or purely largely based on context. 
            # Better: Player class name is 'Player'
            if type(entity).__name__ == 'Enemy':
                restore = self.value * 0.5
            
            entity.health = min(entity.health + restore, 100 if type(entity).__name__ == 'Player' else 50) # Cap? GDD didn't specify Max HP strictly but implied default is max.
            # Assuming max HP is starting HP
            print(f"{type(entity).__name__} collected HealthPack. Healed {restore}. HP: {entity.health}")
