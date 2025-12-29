from level_maze.vfx import VFXManager
from level_maze.roar_bomb import RoarBomb
import random
import pygame
import math

class Player:
    def __init__(self, x, y, config_manager, radius=15, color=(0, 100, 255)):
        self.position = pygame.Vector2(x, y)
        self.radius = radius
        self.color = color
        self.speed = 300 # Pixels per second
        self.look_direction = pygame.Vector2(1, 0) # Facing right initially
        self.health = 100
        self.knockback = pygame.Vector2(0, 0)
        self.friction = 5.0 # Friction for knockback decay
        
        # Abilities Config
        self.dash_config = config_manager.get_ability_config("dash")
        self.roar_config = config_manager.get_ability_config("roar")
        self.bomb_config = config_manager.get("abilities.roar_bomb") # Direct get as it might not be in default helper
        
        self.dash_cooldown_max = self.dash_config.get("cooldown", 10.0)
        self.dash_dist_mult = self.dash_config.get("distance_multiplier", 2.0)
        
        self.roar_cooldown_max = self.roar_config.get("cooldown", 30.0)
        self.roar_push_mult = self.roar_config.get("push_distance_multiplier", 5.0)
        
        self.bomb_cooldown_max = self.bomb_config.get("cooldown", 15.0) if self.bomb_config else 15.0
        
        self.dash_timer = 0.0
        self.dash_active_timer = 0.0 # Timer for i-frames
        self.dash_duration = 0.25 # Duration of invulnerability after dash
        self.roar_timer = 0.0
        self.bomb_timer = 0.0
        
        # Radial Menu State
        self.selected_ability = "roar_bomb" # Default
        self.is_radial_menu_open = False
        self.available_abilities = ["roar_bomb"] # Extendable
        
        # XP System
        self.xp = 0
        self.level = 1
        self.xp_to_next_level = 100
        
        # Rect for simple collision (centered on position)
        self.rect = pygame.Rect(x - radius, y - radius, radius * 2, radius * 2)

        # VFX State
        self.vfx = VFXManager()
        self.trail_ghosts = [] # List of tuples: (position_vector, alpha_int, color_tuple)
        self.roar_waves = [] # List of objects: {'pos': vec, 'radius': float, 'alpha': int, 'max_radius': float, 'thickness': int}
        
        # Frame Flags for Main Loop
        self.just_dashed = False
        self.just_roared = False

    def update(self, delta_time, input_handler, arena, obstacles):
        # Reset frame flags
        self.just_dashed = False
        self.just_roared = False

        # 0. Handle Cooldowns
        if self.dash_timer > 0:
            self.dash_timer -= delta_time
        if self.dash_active_timer > 0:
            self.dash_active_timer -= delta_time
            
        if self.roar_timer > 0:
            self.roar_timer -= delta_time
        if self.bomb_timer > 0:
            self.bomb_timer -= delta_time
            
        # VFX Updates
        self.vfx.update(delta_time)
        
        # Menu State handled in main.py
        
        # 1. Update Ghosts (Fade out)
        active_ghosts = []
        for ghost in self.trail_ghosts:
            pos, alpha, col = ghost
            new_alpha = alpha - (600 * delta_time) # Faster fade
            if new_alpha > 0:
                active_ghosts.append((pos, new_alpha, col))
        self.trail_ghosts = active_ghosts
        
        # 2. Update Roar Waves (Expand and Fade)
        active_waves = []
        for wave in self.roar_waves:
            wave['radius'] += 400 * delta_time # Expansion speed
            wave['alpha'] -= 200 * delta_time # Fade speed
            if wave['alpha'] > 0 and wave['radius'] < wave['max_radius']:
                active_waves.append(wave)
        self.roar_waves = active_waves

        # 0.5 Handle Knockback Decay
        if self.knockback.length_squared() > 100: # Threshold
             self.knockback = self.knockback.move_towards(pygame.Vector2(0,0), self.friction * 200 * delta_time)
        else:
             self.knockback = pygame.Vector2(0,0)

        # 1. Handle Input
        move_vec = input_handler.get_move_vector()
        look_vec = input_handler.get_look_vector(self.position)

        # 2. Update Look Direction (if input exists)
        if look_vec.length_squared() > 0.1:
             self.look_direction = look_vec

        # 3. Update Position
        old_pos = self.position.copy()
        
        # Combine input movement and knockback
        velocity = (move_vec * self.speed) + self.knockback
        
        # Calculate potential new position
        potential_pos = self.position + velocity * delta_time
        potential_rect = self.rect.copy()
        potential_rect.center = (int(potential_pos.x), int(potential_pos.y))
        
        # 4. Arena & Obstacle Collision
        # First check simple arena bounds
        clamped_rect = arena.clamp(potential_rect)
        
        # Then check obstacles
        if not self.check_obstacle_collision(clamped_rect, obstacles):
            # No collision, apply move
            self.rect = clamped_rect
            self.position = pygame.Vector2(self.rect.centerx, self.rect.centery)
        else:
            # Collision!
            # Simple response: Stop.
            # Ideally: Slide along wall.
            # Attempt sliding (x only, then y only)
            
            # X Only
            pos_x = pygame.Vector2(potential_pos.x, self.position.y)
            rect_x = self.rect.copy()
            rect_x.center = (int(pos_x.x), int(pos_x.y))
            rect_x = arena.clamp(rect_x)
            
            if not self.check_obstacle_collision(rect_x, obstacles):
                 self.position.x = pos_x.x
                 self.rect = rect_x
            else:
                # Y Only
                pos_y = pygame.Vector2(self.position.x, potential_pos.y)
                rect_y = self.rect.copy()
                rect_y.center = (int(pos_y.x), int(pos_y.y))
                rect_y = arena.clamp(rect_y)
                
                if not self.check_obstacle_collision(rect_y, obstacles):
                     self.position.y = pos_y.y
                     self.rect = rect_y
                # Else: Blocked completely (Corner usually)
    
    def check_obstacle_collision(self, rect, obstacles):
        for obs in obstacles:
            if rect.colliderect(obs.rect):
                return True
        return False

    def check_obstacle_collision(self, rect, obstacles):
        for obs in obstacles:
            if rect.colliderect(obs.rect):
                return True
        return False

    def set_active_ability(self, ability_name):
        if ability_name in self.available_abilities:
            self.selected_ability = ability_name
            print(f"Ability set to: {ability_name}")

    def draw(self, surface):
        # Draw Dash Ghosts (Additive)
        for pos, alpha, col in self.trail_ghosts:
            ghost_surf = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
            # Tint color towards Cyan for juice
            c = (col[0], col[1], col[2], int(alpha))
            pygame.draw.circle(ghost_surf, c, (self.radius, self.radius), self.radius)
            surface.blit(ghost_surf, (pos.x - self.radius, pos.y - self.radius), special_flags=pygame.BLEND_ADD)
            
        # Draw Roar Waves (Glowing Rings)
        for wave in self.roar_waves:
            max_r = int(wave['max_radius'])
            wave_surf = pygame.Surface((max_r * 2, max_r * 2), pygame.SRCALPHA)
            center = (max_r, max_r)
            
            # Glowing Orange/Gold
            alpha = int(wave['alpha'])
            color = (255, 150, 50, alpha) 
            
            # Draw multiple rings for "thick" pulse
            pygame.draw.circle(wave_surf, color, center, int(wave['radius']), wave['thickness'])
            # Inner faint ring
            if wave['radius'] > 10:
                pygame.draw.circle(wave_surf, (255, 200, 100, int(alpha/2)), center, int(wave['radius'] - 5), 2)
            
            # Blit at position where roar occurred
            draw_pos = (wave['pos'].x - max_r, wave['pos'].y - max_r)
            surface.blit(wave_surf, draw_pos, special_flags=pygame.BLEND_ADD)
            
        # Draw Particles
        self.vfx.draw(surface)
            
        # Draw Body
        body_color = self.color
        # Flash white if invulnerable
        if self.is_invulnerable():
             if int(pygame.time.get_ticks() / 50) % 2 == 0:
                 body_color = (200, 255, 255)
        
        pygame.draw.circle(surface, body_color, (int(self.position.x), int(self.position.y)), self.radius)
        
        # Draw Look Indicator (Arrow)
        # Calculate arrow tip
        arrow_length = self.radius + 5
        arrow_tip = self.position + self.look_direction * arrow_length
        pygame.draw.line(surface, (255, 255, 255), self.position, arrow_tip, 3)
        
        # Draw small circle at tip
        pygame.draw.circle(surface, (255, 0, 0), (int(arrow_tip.x), int(arrow_tip.y)), 3)

        # Draw Level/XP (Above Head)
        pygame.draw.rect(surface, (255, 255, 0), (self.position.x - 20, self.position.y - 32, 40 * (self.xp / self.xp_to_next_level), 3))

        # Draw Health Bar (Simple)
        pygame.draw.rect(surface, (255, 0, 0), (self.position.x - 20, self.position.y - 25, 40, 5))
        pygame.draw.rect(surface, (0, 255, 0), (self.position.x - 20, self.position.y - 25, 40 * (self.health / 100.0), 5))
        
        # Draw Cooldown Indicators
        # Dash: Blue Bar below Health
        if self.dash_timer > 0:
            ratio = self.dash_timer / self.dash_cooldown_max
            pygame.draw.rect(surface, (0, 0, 100), (self.position.x - 20, self.position.y + 20, 18, 4))
            pygame.draw.rect(surface, (100, 100, 255), (self.position.x - 20, self.position.y + 20, 18 * (1.0 - ratio), 4))
        else:
            # Ready indicator (small dot)
            pygame.draw.circle(surface, (100, 200, 255), (int(self.position.x - 15), int(self.position.y + 22)), 2)

        # Roar: Red/Orange Bar below Health
        if self.roar_timer > 0:
            ratio = self.roar_timer / self.roar_cooldown_max
            pygame.draw.rect(surface, (100, 50, 0), (self.position.x + 2, self.position.y + 20, 18, 4))
            pygame.draw.rect(surface, (255, 100, 0), (self.position.x + 2, self.position.y + 20, 18 * (1.0 - ratio), 4))
        else:
             # Ready indicator
            pygame.draw.circle(surface, (255, 150, 0), (int(self.position.x + 15), int(self.position.y + 22)), 2)
            
        # Draw Radial Menu if Open
        if self.is_radial_menu_open:
            self.draw_radial_menu(surface)

    def draw_radial_menu(self, surface):
        # Draw ring around player
        center = (int(self.position.x), int(self.position.y))
        radius = 80
        
        # Semi-transparent BG
        menu_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(menu_surf, (0, 0, 0, 150), (radius, radius), radius)
        
        # Draw Selection Slots
        # Currently only Roar Bomb (Top)
        # Draw icon/text
        font = pygame.font.SysFont("Arial", 16, bold=True)
        text = font.render("Roar Bomb", True, (255, 255, 255))
        
        # Position at top
        text_rect = text.get_rect(center=(radius, radius - 50))
        menu_surf.blit(text, text_rect)
        
        # Highlight Selected
        if self.selected_ability == "roar_bomb":
            pygame.draw.circle(menu_surf, (0, 255, 0), (radius, radius - 50), 5)
        
        surface.blit(menu_surf, (center[0] - radius, center[1] - radius))

    def take_damage(self, amount):
        if self.is_invulnerable():
            print("Player Invulnerable! Damage blocked.")
            return

        self.health -= amount
        print(f"Player took {amount} damage. HP: {self.health}")

    def gain_xp(self, amount):
        self.xp += amount
        print(f"Player gained {amount} XP. Total: {self.xp}")
        if self.xp >= self.xp_to_next_level:
            self.level_up()

    def level_up(self):
        self.level += 1
        self.xp -= self.xp_to_next_level
        self.xp_to_next_level = int(self.xp_to_next_level * 1.2) # Curve
        
        # Buffs (Reduce cooldowns by 10%)
        self.dash_cooldown_max *= 0.9
        self.roar_cooldown_max *= 0.9
        self.bomb_cooldown_max *= 0.9
        self.health = 100 # Full heal on level up?
        
        print(f"LEVEL UP! Level {self.level}. Cooldowns reduced.")

    def apply_knockback(self, force_vector):
        self.knockback = force_vector

    def attempt_dash(self):
        if self.dash_timer <= 0:
            # Dash!
            distance = 4 * self.radius 
            dash_vector = self.look_direction.normalize() * distance
            
            # Spawn Ghosts + Particles
            start_pos = self.position.copy()
            for i in range(1, 6): # More ghosts (5)
                 ghost_pos = start_pos + dash_vector * (i / 5.0)
                 # Cyan/Blue tint for electric feel
                 self.trail_ghosts.append((ghost_pos, 200, (0, 255, 255)))
                 
            # Emit Spark Particles backwards
            # Direction is -dash_vector
            reverse_dir = -dash_vector.normalize()
            self.vfx.emit_directional(start_pos, reverse_dir, 20, (100, 255, 255), 200, spread_angle=45)

            self.position += dash_vector
            
            self.dash_timer = self.dash_cooldown_max
            self.dash_active_timer = self.dash_duration # Trigger invulnerability
            self.just_dashed = True
            print("Player Dashed!")
            return True
        return False

    def is_invulnerable(self):
        return self.dash_active_timer > 0

    def attempt_roar(self):
        if self.roar_timer <= 0:
            self.roar_timer = self.roar_cooldown_max
            
            # Spawn Multi-Ring Roar Wave
            rings = 3
            for i in range(rings):
                self.roar_waves.append({
                    'pos': self.position.copy(),
                    'radius': 10.0 + (i * 20),
                    'alpha': 255,
                    'max_radius': self.get_roar_radius() + (i * 30),
                    'thickness': 5 - i # Inner rings thinner
                })
            
            # Emit Burst Particles
            self.vfx.emit(self.position, 60, (255, 100, 0), 100, 300, size_max=6, life=0.6)
            
            self.just_roared = True
            print("Player Roared!")
            return True 
        return False
        
    def attempt_secondary_ability(self):
        if self.selected_ability == "roar_bomb":
            if self.bomb_timer <= 0:
                self.bomb_timer = self.bomb_cooldown_max
                
                # Throw Bomb backwards? Or forwards?
                # User request: "chuck behind"
                # But typically abilities are aimed.
                # Request says: "it is something the player can chuck behind"
                # This implies backward throw.
                direction = -self.look_direction
                
                bomb = RoarBomb(self.position, direction, self.bomb_config)
                print("Player threw Roar Bomb!")
                return bomb
            else:
                print("Bomb on cooldown")
        return None

    def get_roar_radius(self):
        return 10 * self.radius
