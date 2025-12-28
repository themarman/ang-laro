import pygame
import random
from level_maze.xtra import HealthPack

class XtraManager:
    def __init__(self):
        self.xtras = []
        self.spawn_timer = 0
        self.spawn_interval_min = 5.0
        self.spawn_interval_max = 15.0
        self.next_spawn_time = 5.0

    def update(self, dt, arena, obstacles):
        # Update existing
        for xtra in self.xtras:
            xtra.update(dt)
        
        # Remove expired
        self.xtras = [x for x in self.xtras if x.active]

        # Spawning Logic
        self.spawn_timer += dt
        if self.spawn_timer >= self.next_spawn_time:
            self.spawn_timer = 0
            self.next_spawn_time = random.uniform(self.spawn_interval_min, self.spawn_interval_max)
            self.spawn_xtra(arena, obstacles)

    def spawn_xtra(self, arena, obstacles):
        # Try to find valid spot
        for _ in range(10): # 10 attempts
            w, h = 20, 20
            spawn_area = arena.rect.inflate(-40, -40)
            x = random.randint(spawn_area.left, spawn_area.right - w)
            y = random.randint(spawn_area.top, spawn_area.bottom - h)
            new_rect = pygame.Rect(x, y, w, h)
            
            # Check collision with obstacles
            valid = True
            for obs in obstacles:
                if new_rect.colliderect(obs.rect):
                    valid = False
                    break
            
            if valid:
                # Add Health Pack (Only type for now)
                self.xtras.append(HealthPack(x, y))
                print("Spawned Health Pack")
                break

    def draw(self, surface):
        for xtra in self.xtras:
            xtra.draw(surface)

    def get_xtras(self):
        return self.xtras
