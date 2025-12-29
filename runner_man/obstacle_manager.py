import pygame
import random

class ObstacleManager:
    def __init__(self, screen_width, screen_height):
        self.obstacles = []
        self.screen_width = screen_width
        self.ground_y = 500 # Should match player ground (y + height/2 + offset?)
        # Player is at y=400 in main (plan), ground needs to be consistent.
        # Player size 60. passed Y=400.
        
        self.spawn_timer = 0.0
        self.spawn_interval = 2.0
        self.enabled = True
    
    def toggle(self):
        self.enabled = not self.enabled
        if not self.enabled:
            self.obstacles = [] # Clear if disabled
    
    def update(self, dt, current_speed):
        if not self.enabled: return
        
        # Spawning
        self.spawn_timer -= dt
        if self.spawn_timer <= 0:
            self.spawn_obstacle()
            # Randomize next interval based on speed?
            # Faster speed -> faster spawning to keep density constant?
            # Or faster speed -> obstacles come faster naturally.
            self.spawn_timer = random.uniform(1.0, 3.0)
            
        # Move Obstacles
        active_obs = []
        for obs in self.obstacles:
            obs['rect'].x -= current_speed * dt
            if obs['rect'].right > 0:
                active_obs.append(obs)
        self.obstacles = active_obs
        
    def spawn_obstacle(self):
        # Simple Rect Obstacle
        h = random.randint(40, 80)
        w = random.randint(30, 50)
        # Position: Just offscreen right
        # Y: Ground - h (To sit on ground)
        # Assuming ground plane is at Y=500? (Need to sync with main)
        ground_y = 460 # Sync with Player logic later
        
        rect = pygame.Rect(self.screen_width + 10, ground_y - h, w, h)
        self.obstacles.append({'rect': rect, 'color': (255, 100, 100)})
        
    def draw(self, surface):
        for obs in self.obstacles:
            pygame.draw.rect(surface, obs['color'], obs['rect'])
            
    def check_collision(self, player_rect):
        for obs in self.obstacles:
            if player_rect.colliderect(obs['rect']):
                return obs
        return None
