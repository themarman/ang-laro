import pygame
import math

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
        
        self.dash_cooldown_max = self.dash_config.get("cooldown", 10.0)
        self.dash_dist_mult = self.dash_config.get("distance_multiplier", 2.0)
        
        self.roar_cooldown_max = self.roar_config.get("cooldown", 30.0)
        self.roar_push_mult = self.roar_config.get("push_distance_multiplier", 5.0)
        
        self.dash_timer = 0.0
        self.roar_timer = 0.0
        
        # XP System
        self.xp = 0
        self.level = 1
        self.xp_to_next_level = 100
        
        # Rect for simple collision (centered on position)
        self.rect = pygame.Rect(x - radius, y - radius, radius * 2, radius * 2)

    def update(self, delta_time, input_handler, arena):
        # 0. Handle Cooldowns
        if self.dash_timer > 0:
            self.dash_timer -= delta_time
        if self.roar_timer > 0:
            self.roar_timer -= delta_time

        # 0.5 Handle Knockback Decay
        if self.knockback.length_squared() > 100: # Threshold
             self.knockback = self.knockback.move_towards(pygame.Vector2(0,0), self.friction * 200 * delta_time)
        else:
             self.knockback = pygame.Vector2(0,0)

        # 1. Handle Input
        move_vec = input_handler.get_move_vector()
        look_vec = input_handler.get_look_vector(self.position)

        # 2. Update Look Direction (if input exists)
        # Note: If input_handler returns valid look vector, use it.
        # If stick is neutral, we might want to keep last direction.
        # The input handler returns a default or calculates one.
        # We need to refine InputHandler to return None if neutral so we don't snap to (1,0)
        # But for now, let's assume valid vector or same as previous if handled there.
        # Actually input_handle logic:
        # Controller: returns (0,0) if neutral? No, code says checking deadzone.
        # Mouse: always returns vector.
        
        # Let's adjust logic:
        # If look_vec is length > 0, update
        if look_vec.length_squared() > 0.1:
             # Just ensures we don't snap to 0
             self.look_direction = look_vec

        # 3. Update Position
        old_pos = self.position.copy()
        
        # Combine input movement and knockback
        velocity = (move_vec * self.speed) + self.knockback
        
        self.position += velocity * delta_time

        # 4. Arena Collision (Clamping)
        # Update rect to new position to check
        self.rect.center = (int(self.position.x), int(self.position.y))
        
        # Clamp to arena
        clamped_rect = arena.clamp(self.rect)
        self.rect = clamped_rect
        self.position = pygame.Vector2(self.rect.centerx, self.rect.centery)

    def draw(self, surface):
        # Draw Body
        pygame.draw.circle(surface, self.color, (int(self.position.x), int(self.position.y)), self.radius)
        
        # Draw Look Indicator (Arrow)
        # Calculate arrow tip
        arrow_length = self.radius + 5
        arrow_tip = self.position + self.look_direction * arrow_length
        pass # To be fully implemented with a nice triangle, for now a line
        pygame.draw.line(surface, (255, 255, 255), self.position, arrow_tip, 3)
        
        # Draw small circle at tip
        pygame.draw.circle(surface, (255, 0, 0), (int(arrow_tip.x), int(arrow_tip.y)), 3)

        # Draw Level/XP (Above Head)
        # Font needed? Should init font in main or pass it. 
        # For prototype, just print to console or crude bar.
        # Let's draw a small yellow bar for XP
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

    def take_damage(self, amount):
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
        self.health = 100 # Full heal on level up?
        
        print(f"LEVEL UP! Level {self.level}. Cooldowns reduced.")

    def apply_knockback(self, force_vector):
        self.knockback = force_vector

    def attempt_dash(self):
        if self.dash_timer <= 0:
            # Dash!
            # Moves 2x diameter in facing direction.
            # Diameter = 2*radius. 2x diameter = 4 * radius.
            distance = 4 * self.radius # GDD: "2 times its diameter"
            
            # Apply as an immediate position shift? Or high velocity impulse?
            # GDD says "move very quickly". Teleporting might clip walls.
            # Impulse is safer for physics engine, but here we have manual placement.
            # Let's add a massive burst of velocity to knockback/momentum or just direct shift checked against walls.
            # Since we have "step" logic in update, applying a huge velocity frame 1 is fine if we separate it.
            # However, simpler implementation: Instant shift checked by arena clamp.
            
            # Use current look direction
            dash_vector = self.look_direction.normalize() * distance
            
            # We can just apply this to position immediately, update loop will clamp it.
            self.position += dash_vector
            
            self.dash_timer = self.dash_cooldown_max
            print("Player Dashed!")
            return True
        return False

    def attempt_roar(self):
        if self.roar_timer <= 0:
            self.roar_timer = self.roar_cooldown_max
            print("Player Roared!")
            return True # Signal to main loop to handle effects
        return False
        
    def get_roar_radius(self):
        # "5 times the player's diameter" -> 10 * radius
        return 10 * self.radius
