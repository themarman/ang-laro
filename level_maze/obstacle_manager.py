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
                
            # Check overlap with existing obstacles with minimum gap
            valid = True
            for obs in self.obstacles:
                # Inflate existing obstacle by gap to check safety
                check_rect = obs.rect.inflate(self.min_gap, self.min_gap)
                if new_rect.colliderect(check_rect):
                    valid = False
                    break
            
            if valid:
                self.obstacles.append(Obstacle(x, y, w, h))

    def draw(self, surface):
        for obs in self.obstacles:
            obs.draw(surface)

    def get_obstacles(self):
        return self.obstacles
