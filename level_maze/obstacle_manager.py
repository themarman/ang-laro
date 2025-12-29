import pygame
import random
from level_maze.obstacle import Obstacle

class ObstacleManager:
    def __init__(self):
        self.obstacles = []
        self.min_gap = 45 # 1.5 * Player Diameter (30)

    def generate_obstacles(self, arena, player_safe_zone, num_obstacles=10):
        self.obstacles = []
        
        attempts = 0
        max_attempts = 1000
        
        while len(self.obstacles) < num_obstacles and attempts < max_attempts:
            attempts += 1
            
            # Random size
            w = random.randint(30, 80)
            h = random.randint(30, 80)
            
            # Random position within arena (accounting for wall thickness ~10)
            # Inflation of - wall thickness and margin
            spawn_area = arena.rect.inflate(-40, -40) 
            
            if spawn_area.width <= w or spawn_area.height <= h:
                continue

            x = random.randint(spawn_area.left, spawn_area.right - w)
            y = random.randint(spawn_area.top, spawn_area.bottom - h)
            
            new_rect = pygame.Rect(x, y, w, h)
            
            # Check Player Safe Zone
            if new_rect.colliderect(player_safe_zone.inflate(self.min_gap, self.min_gap)):
                continue
                
            # Check overlap with existing obstacles with minimum gap (1.5 * Player Diameter)
            # Player Radius = 15 => Diameter = 30. 1.5 * 30 = 45.
            # Using 50 for safety.
            # ALSO need to check distance between edges/corners as requested.
            # Valid check: Inflate BOTH by gap/2? Or inflate one by gap?
            # If we inflate existing by gap, we ensure new rect doesn't touch inflated area.
            
            gap_required = 50 # > 1.5 * 30 (45)
            
            valid = True
            for obs in self.obstacles:
                # 1. Simple Rect Overlap with Gap
                check_rect = obs.rect.inflate(gap_required * 2, gap_required * 2) # inflate adds to width/height, so 2x gap total
                if new_rect.colliderect(check_rect):
                    valid = False
                    break
                
                # 2. Strict distance check for corners (optional but requested "check distances between edges and corners")
                # The colliderect with inflation covers "Manhattan" distance or box distance.
                # If we need Euclidean distance between corners (e.g. diagonal gap), it's more complex.
                # However, for a maze, box gaps are usually sufficient to prevent 
                # creating "diagonal squeezes" where player clips.
                # Since we use AABB collision for player, box inflation is actually CORRECT. 
                # If we inflated by gap, we ensure minimal axis-aligned space.
            
            if valid:
                self.obstacles.append(Obstacle(x, y, w, h))

    def draw(self, surface):
        for obs in self.obstacles:
            obs.draw(surface)

    def get_obstacles(self):
        return self.obstacles
