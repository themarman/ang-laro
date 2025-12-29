import pygame
import math
import random

class BrickBomb:
    def __init__(self, position, direction, config, player_diameter=40):
        self.position = pygame.Vector2(position)
        self.direction = direction.normalize()
        self.speed = config.get("throw_speed", 400.0)
        self.fuse_timer = config.get("fuse_time", 3.0)
        self.init_fuse = self.fuse_timer
        self.size = config.get("size", 40)
        
        # Clearance Settings
        self.player_diameter = player_diameter
        self.clearance_dist = player_diameter * config.get("clearance_factor", 1.5)
        # We need 1.5x diameter clearance. 
        # Is it from CENTER or EDGE? "edges needs to be 1.5 the diameter ... away"
        # Edge-to-Edge distance >= 1.5 * diameter.
        
        self.rect = pygame.Rect(0, 0, self.size, self.size)
        self.rect.center = (int(self.position.x), int(self.position.y))
        
        self.is_active = True # Flying/Arming
        self.is_solidified = False # Turned into obstacle
        self.color = (200, 100, 50) # Brick color
        self.blink_timer = 0.0

    def update(self, dt, arena, obstacles, enemies=None):
        if self.is_solidified:
            return

        # Move
        velocity = self.direction * self.speed * dt
        self.position += velocity
        self.rect.center = (int(self.position.x), int(self.position.y))

        # 1. Wall Collisions (Bounce)
        # Check Arena Bounds
        if self.rect.left < arena.rect.left:
            self.position.x = arena.rect.left + self.rect.width/2
            self.direction.x *= -1
        elif self.rect.right > arena.rect.right:
            self.position.x = arena.rect.right - self.rect.width/2
            self.direction.x *= -1
            
        if self.rect.top < arena.rect.top:
            self.position.y = arena.rect.top + self.rect.height/2
            self.direction.y *= -1
        elif self.rect.bottom > arena.rect.bottom:
            self.position.y = arena.rect.bottom - self.rect.height/2
            self.direction.y *= -1

        # 2. Obstacle & Enemy Collisions (Bounce)
        # Combine list for checking
        collidables = list(obstacles)
        if enemies:
             # Wrap enemies in simple objects or use their rects?
             # Enemies have .rect, but we might want to treat them similar to obstacles for bouncing.
             collidables.extend(enemies)
             
        # Simple AABB reflection
        for obs in collidables:
            # For enemies, we might want to check if they are "active" or alive?
            # Assuming passed list is valid.
            if self.rect.colliderect(obs.rect):
                # Resolve Collision reflectively
                # Determine side of collision
                clip = self.rect.clip(obs.rect)
                
                # If wide collision, likely vertical
                if clip.width > clip.height:
                    # Vertical Bounce
                    self.direction.y *= -1
                    # Push out
                    if self.rect.center[1] < obs.rect.center[1]:
                         self.position.y -= clip.height
                    else:
                         self.position.y += clip.height
                else:
                    # Horizontal Bounce
                    self.direction.x *= -1
                     # Push out
                    if self.rect.center[0] < obs.rect.center[0]:
                         self.position.x -= clip.width
                    else:
                         self.position.x += clip.width
                
                self.rect.center = (int(self.position.x), int(self.position.y))
                break # Handle one at a time

        # Fuse Logic
        self.fuse_timer -= dt
        self.blink_timer += dt
        
        if self.fuse_timer <= 0:
            # Check Placement Validity
            if self.check_clearance(arena, obstacles):
                self.is_solidified = True
                self.is_active = False # Handled by main to convert
            else:
                # Keep moving if invalid? User said: "It will turn into a brick obstacle 3 seconds after deployment."
                # But also: "it would bounce off until it reached this distance."
                # Implication: Bouncing phase IS the seeking phase.
                # If timer ends and we are invalid, do we force move? Or keep bouncing?
                # "Until it reached this distance" implies it KEEPS bouncing if distance not met?
                # So if timer is <= 0 but invalid, keep bouncing!
                # Effectively, fuse doesn't trigger solidification UNLESS valid.
                # But what if it never finds it? infinite bounce?
                # Or does it turn into brick immediately 3s AFTER valid?
                # "It will turn into a brick obstacle 3 seconds after deployment." - Hard Constraint?
                # "The obstacle follow the same rule ... it would bounce off until it reached this distance" - Behavior.
                # Combined: Timer tries to solidify. If invalid, bounce/wait until valid?
                # Let's implementation: Once Fuse is 0, Try to Solidify. If fail, keep bouncing.
                pass

    def check_clearance(self, arena, obstacles):
        # Edges needs to be 1.5 * diameter away from other edges.
        # My Edge to Their Edge distance.
        required_dist = self.clearance_dist
        
        # 1. Check Walls
        # Dist to left wall = self.rect.left - arena.rect.left
        dist_left = self.rect.left - arena.rect.left
        dist_right = arena.rect.right - self.rect.right
        dist_top = self.rect.top - arena.rect.top
        dist_bottom = arena.rect.bottom - self.rect.bottom
        
        if dist_left < required_dist or dist_right < required_dist or dist_top < required_dist or dist_bottom < required_dist:
            return False
            
        # 2. Check Obstacles
        for obs in obstacles:
            # Calculate generic distance between rectangles?
            # Or simplified center distance?
            # "Edges ... away"
            # Rect distance is max(0, start1 - end2, start2 - end1) in each axis?
            # Actually, max(dx, dy) where dx is gap.
            
            # Gap X
            gap_x = 0
            if self.rect.right < obs.rect.left:
                gap_x = obs.rect.left - self.rect.right
            elif obs.rect.right < self.rect.left:
                gap_x = self.rect.left - obs.rect.right
            else:
                gap_x = 0 # Overlap in X
                
            # Gap Y
            gap_y = 0
            if self.rect.bottom < obs.rect.top:
                gap_y = obs.rect.top - self.rect.bottom
            elif obs.rect.bottom < self.rect.top:
                gap_y = self.rect.top - obs.rect.bottom
            else:
                gap_y = 0 # Overlap
            
            # Euclidean distance of gap
            dist = math.sqrt(gap_x**2 + gap_y**2)
            
            if dist < required_dist:
                return False
                
        return True

    def draw(self, surface):
        if self.is_solidified:
            pygame.draw.rect(surface, self.color, self.rect)
            pygame.draw.rect(surface, (150, 75, 40), self.rect, 3) 
            return
            
        # Draw Blinking Bomb (Projectile)
        # Should look like Roar Bomb Size (Radius 8)
        
        freq = 10.0 if self.fuse_timer < 1.0 else 5.0
        # Blink color/alpha
        alpha = 200 + 55 * math.sin(self.blink_timer * freq)
        
        # Draw Circle Core (Radius 8)
        center = (int(self.rect.centerx), int(self.rect.centery))
        pygame.draw.circle(surface, self.color, center, 8)
        
        # Blink/Pulse Overlay
        pulse_surf = pygame.Surface((20, 20), pygame.SRCALPHA)
        pulse_color = (255, 200, 0, int(alpha) if alpha > 0 else 0)
        pygame.draw.circle(pulse_surf, pulse_color, (10, 10), 8 + math.sin(self.blink_timer * 10) * 2)
        
        surface.blit(pulse_surf, (center[0] - 10, center[1] - 10), special_flags=pygame.BLEND_ADD)
        
        # Draw "Ghost" of full size to show where it will land?
        # User requested "while moving animation should be same size as roar bomb".
        # So we probably shouldn't draw the full box yet.
        # But maybe a faint outline to show the clearance zone?
        # Optional: clearance indicator
        # pygame.draw.rect(surface, (255, 255, 255), self.rect, 1)
