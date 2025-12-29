import pygame
import math

class RoarBomb:
    def __init__(self, start_pos, direction, config):
        self.position = pygame.Vector2(start_pos)
        self.config = config
        
        speed = self.config.get("throw_speed", 500.0)
        self.velocity = direction.normalize() * speed
        self.friction = 2.0 # Slow down over time
        
        self.duration = self.config.get("duration", 10.0)
        self.max_radius = self.config.get("radius", 150.0)
        self.push_force = self.config.get("push_force", 300.0)
        
        self.life_timer = self.duration
        self.is_active = True
        
        # VFX pulse state
        self.pulse_timer = 0.0
        self.waves = []
        self.wave_spawn_timer = 0.0

    def update(self, dt, arena):
        if not self.is_active:
            return

        self.life_timer -= dt
        if self.life_timer <= 0:
            self.is_active = False
            
        # Move
        if self.velocity.length_squared() > 10:
            self.position += self.velocity * dt
            # Apply Friction
            self.velocity = self.velocity.move_towards(pygame.Vector2(0,0), self.friction * 200 * dt)
            
            # Bounce off arena walls
            # Simple clamp for now, essentially stops at wall
            rect = pygame.Rect(self.position.x - 5, self.position.y - 5, 10, 10)
            clamped = arena.clamp(rect)
            if clamped.center != (int(self.position.x), int(self.position.y)):
                self.position = pygame.Vector2(clamped.center)
                self.velocity = pygame.Vector2(0,0) # Stop on hit

        self.pulse_timer += dt
        
        # Spawn Waves Periodically
        self.wave_spawn_timer -= dt
        if self.wave_spawn_timer <= 0:
            self.wave_spawn_timer = 0.6 # Spawn wave every 0.6s
            self.waves.append({
                'radius': 10.0,
                'alpha': 255,
                'max_radius': self.max_radius,
                'thickness': 3
            })
            
        # Update Waves
        active_waves = []
        for wave in self.waves:
            wave['radius'] += 150 * dt # Expansion speed (slower than player roar for persistence feel)
            wave['alpha'] -= 100 * dt
            if wave['alpha'] > 0 and wave['radius'] < wave['max_radius']:
                active_waves.append(wave)
        self.waves = active_waves

    def get_push_force(self, target_pos):
        # Calculate force vector on target
        diff = target_pos - self.position
        dist = diff.length()
        
        if dist < self.max_radius:
            # Inside radius
            if dist == 0: dist = 0.1
            direction = diff.normalize()
            
            # Linear falloff? Or constant spread?
            # Let's do constant push but weaker at edge
            strength = self.push_force * (1.0 - (dist / self.max_radius))
            return direction * strength
            
        return pygame.Vector2(0,0)

    def draw(self, surface):
        # Draw Bomb Core
        core_color = (255, 100, 0)
        pygame.draw.circle(surface, core_color, (int(self.position.x), int(self.position.y)), 8)
        
        # Draw Waves
        for wave in self.waves:
            r = int(wave['radius'])
            wave_surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            
            alpha = int(max(0, min(255, wave['alpha'])))
            color = (255, 150, 0, alpha)
            
            center = (r, r)
            pygame.draw.circle(wave_surf, color, center, r, wave['thickness'])
            
            # Blit centered
            surface.blit(wave_surf, (self.position.x - r, self.position.y - r), special_flags=pygame.BLEND_ADD)
        
        # Draw faint area tint logic removed in favor of waves, or keep?
        # Let's keep a very faint static ring to show the actual boundary
        radius_surf = pygame.Surface((int(self.max_radius * 2), int(self.max_radius * 2)), pygame.SRCALPHA)
        pygame.draw.circle(radius_surf, (255, 100, 0, 20), (int(self.max_radius), int(self.max_radius)), int(self.max_radius), 2)
        surface.blit(radius_surf, (self.position.x - self.max_radius, self.position.y - self.max_radius), special_flags=pygame.BLEND_ADD)
