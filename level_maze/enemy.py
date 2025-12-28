import pygame
import random
import math

class Enemy:
    def __init__(self, x, y, radius=15, color=(255, 50, 50)):
        self.position = pygame.Vector2(x, y)
        self.radius = radius
        self.color = color
        self.speed = 100 # Slower than player
        self.look_direction = pygame.Vector2(1, 0)
        
        self.health = 50
        self.knockback = pygame.Vector2(0, 0)
        self.friction = 3.0 # Friction for knockback decay
        
        # State
        self.state = "PATROL" # PATROL, CHASE, INVESTIGATE
        self.target_position = None
        self.patrol_timer = 0
        
        self.rect = pygame.Rect(x - radius, y - radius, radius * 2, radius * 2)

    def update(self, dt, player, arena, obstacles):
        # 1. Vision Check (Simple LOS)
        can_see = self.check_line_of_sight(player, obstacles)
        
        if can_see:
            self.state = "CHASE"
            self.target_position = player.position
        elif self.state == "CHASE":
            # Lost sight, go to last known pos
            self.state = "INVESTIGATE"
        
        # 2. Behavior
        desired_direction = pygame.Vector2(0, 0)
        
        if self.state == "CHASE" or self.state == "INVESTIGATE":
            if self.target_position:
                to_target = self.target_position - self.position
                if to_target.length() > 10: # Reached target check
                    desired_direction = to_target.normalize()
                else:
                    if self.state == "INVESTIGATE":
                        self.state = "PATROL" # Arrived at last known, resume patrol
        
        elif self.state == "PATROL":
            self.patrol_timer -= dt
            if self.patrol_timer <= 0:
                # Pick random direction
                angle = random.uniform(0, 360)
                rad = math.radians(angle)
                self.look_direction = pygame.Vector2(math.cos(rad), math.sin(rad))
                self.patrol_timer = random.uniform(1.0, 3.0)
            
            desired_direction = self.look_direction

        # 3. Movement (Tank Style: Move in Look Direction)
        # Combine AI movement with knockback
        
        # Decay knockback
        if self.knockback.length_squared() > 100:
             self.knockback = self.knockback.move_towards(pygame.Vector2(0,0), self.friction * 200 * dt)
        else:
             self.knockback = pygame.Vector2(0,0)

        # Basic velocity
        velocity = pygame.Vector2(0,0)
        if desired_direction.length_squared() > 0:
            self.look_direction = desired_direction # Instant turn
            velocity = self.look_direction * self.speed
        
        # Apply combined velocity
        total_velocity = velocity + self.knockback
        next_pos = self.position + total_velocity * dt
        
        next_rect = self.rect.copy()
        next_rect.center = (int(next_pos.x), int(next_pos.y))
        
        # Checking Collision
        if arena.contains(next_rect) and not self.check_obstacle_collision(next_rect, obstacles):
            self.position = next_pos
            self.rect = next_rect
        else:
            # Hit wall/obstacle
            # If purely due to knockback, we might want to slide, but for now just stop
             if self.state == "PATROL" and self.knockback.length_squared() == 0:
                self.patrol_timer = 0 # Force retarget

    def check_obstacle_collision(self, rect, obstacles):
        for obs in obstacles:
            if rect.colliderect(obs.rect):
                return True
        return False

    def check_line_of_sight(self, player, obstacles):
        # Simple Raycast: Line from self to player does not intersect any obstacle
        line_start = self.position
        line_end = player.position
        
        for obs in obstacles:
            # clip_line returns the segment of the line inside the rect, or empty if none
            if obs.rect.clipline(line_start, line_end):
                return False
        return True

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.position.x), int(self.position.y)), self.radius)
        
        # Arrow
        arrow_tip = self.position + self.look_direction * (self.radius + 5)
        pygame.draw.line(surface, (255, 255, 255), self.position, arrow_tip, 3)

        # Health Bar
        pygame.draw.rect(surface, (255, 0, 0), (self.position.x - 15, self.position.y - 20, 30, 4))
        pygame.draw.rect(surface, (0, 255, 0), (self.position.x - 15, self.position.y - 20, 30 * (max(0, self.health) / 50.0), 4))

    def take_damage(self, amount):
        self.health -= amount
        print(f"Enemy took {amount} damage. HP: {self.health}")

    def apply_knockback(self, force_vector):
        self.knockback = force_vector
