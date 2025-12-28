import pygame

class Arena:
    def __init__(self, x, y, width, height, color=(100, 100, 100)):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color
        self.wall_thickness = 10
        self.wall_color = (200, 200, 200) # Lighter color for walls to distinguish from floor if needed

    def draw(self, surface):
        # Draw the floor
        # pygame.draw.rect(surface, self.color, self.rect)
        
        # Draw the walls (boundary)
        pygame.draw.rect(surface, self.wall_color, self.rect, self.wall_thickness)

    def contains(self, rect):
        """Checks if the given rect is fully inside the arena (considering wall thickness)."""
        # Inflate negative thickness to get the inner bounds
        inner_rect = self.rect.inflate(-self.wall_thickness * 2, -self.wall_thickness * 2)
        return inner_rect.contains(rect)

    def clamp(self, rect):
        """Clamps a rect to be inside the arena."""
        inner_rect = self.rect.inflate(-self.wall_thickness * 2, -self.wall_thickness * 2)
        return rect.clamp(inner_rect)
