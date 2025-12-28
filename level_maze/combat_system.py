import pygame

class CombatSystem:
    def __init__(self):
        self.damage_value = 10
        self.knockback_multiplier = 50 # Force per point of damage
        self.cooldown_timers = {} # Key: enemy_id, Value: time since last hit
        self.hit_cooldown = 0.5 # Seconds before same pair can collide again (prevents mulit-frame hits)

    def resolve_collisions(self, player, enemies, dt):
        # Cooldown management (simple cleanup logic could go here, but for now just check)
        
        # Player vs Enemies
        player_rect = player.rect
        player_center = player.position

        for enemy in enemies:
             # Check collision
             if player_rect.colliderect(enemy.rect):
                 # Check internal cooldown for this interaction if persistent
                 # Since objects are recreated/not persistent IDs in simple list, just rely on physical separation for now
                 # But if bounce is failing, they die instantly.
                 # Let's trust bounce for now.
                 
                 # Resolve
                 self.apply_combat_interaction(player, enemy)

    def apply_combat_interaction(self, player, enemy):
        # 1. Calculate direction
        diff = player.position - enemy.position
        if diff.length_squared() == 0:
            diff = pygame.Vector2(1, 0) # Random push if exact overlap
        
        direction_to_player = diff.normalize()
        direction_to_enemy = -direction_to_player
        
        # 2. Apply Damage
        player.take_damage(self.damage_value)
        enemy.take_damage(self.damage_value)
        
        # 3. Apply Knockback
        force = self.damage_value * self.knockback_multiplier
        
        player.apply_knockback(direction_to_player * force)
        enemy.apply_knockback(direction_to_enemy * force)
        
        # 4. Immediate separation to prevent sticking (Micro-step)
        # Move them out a tiny bit so next frame doesn't trigger collision before update
        # However, bounce velocity should handle it in next update.
