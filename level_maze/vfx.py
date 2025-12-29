import pygame
import random
import math

class Particle:
    def __init__(self, pos, vel, color, size, life, decay_rate=1.0):
        self.pos = pygame.Vector2(pos)
        self.vel = pygame.Vector2(vel)
        self.color = color
        self.size = size
        self.life = life # seconds
        self.max_life = life
        self.decay_rate = decay_rate

    def update(self, dt):
        self.pos += self.vel * dt
        self.life -= self.decay_rate * dt
        
    def is_alive(self):
        return self.life > 0

class VFXManager:
    def __init__(self):
        self.particles = []

    def emit(self, pos, count, color, speed_min, speed_max, size_min=2, size_max=5, life=0.5):
        for _ in range(count):
            angle = random.uniform(0, 360)
            rad = math.radians(angle)
            speed = random.uniform(speed_min, speed_max)
            vel = pygame.Vector2(math.cos(rad) * speed, math.sin(rad) * speed)
            
            # Randomize color slightly?
            p_size = random.uniform(size_min, size_max)
            p_life = random.uniform(life * 0.5, life * 1.5)
            
            self.particles.append(Particle(pos, vel, color, p_size, p_life))

    def emit_directional(self, pos, direction, count, color, speed, spread_angle=30):
        # direction is Vector2
        base_angle = math.degrees(math.atan2(direction.y, direction.x))
        
        for _ in range(count):
            angle = base_angle + random.uniform(-spread_angle, spread_angle)
            rad = math.radians(angle)
            s = speed * random.uniform(0.8, 1.2)
            vel = pygame.Vector2(math.cos(rad) * s, math.sin(rad) * s)
            
            self.particles.append(Particle(pos, vel, color, random.uniform(2, 4), random.uniform(0.3, 0.6)))

    def update(self, dt):
        alive_particles = []
        for p in self.particles:
            p.update(dt)
            if p.is_alive():
                alive_particles.append(p)
        self.particles = alive_particles

    def draw(self, surface):
        # Use a separate surface for additive blending if needed, 
        # or just blit special surfaces. 
        # For simple particles, direct drawing with BLEND_ADD is fast.
        
        for p in self.particles:
            # Alpha based on life
            alpha = int(255 * (p.life / p.max_life))
            if alpha <= 0: continue
            
            # Create a small surface for the particle to handle Alpha + Blend
            s = pygame.Surface((int(p.size)*2, int(p.size)*2), pygame.SRCALPHA)
            
            # Draw circle on it
            # Color tuple needs to not have alpha for the draw, alpha is handled by blit or surface alpha
            # Actually, let's use the surface alpha
            c = (p.color[0], p.color[1], p.color[2], alpha)
            pygame.draw.circle(s, c, (p.size, p.size), p.size)
            
            # Blit with ADD
            dest = (p.pos.x - p.size, p.pos.y - p.size)
            surface.blit(s, dest, special_flags=pygame.BLEND_ADD)
