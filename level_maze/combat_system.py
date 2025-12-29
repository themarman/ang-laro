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
        # 0. Check Invulnerability
        if player.is_invulnerable():
            return

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

    def resolve_enemy_collisions(self, enemies):
        # O(N^2) check - fine for small number of enemies (e.g. < 50)
        # If many enemies, would need spatial partition (QuadTree or Grid)
        
        count = len(enemies)
        if count < 2:
            return

        for i in range(count):
            e1 = enemies[i]
            for j in range(i + 1, count):
                e2 = enemies[j]
                
                # Check distance
                dist_vec = e1.position - e2.position
                dist_sq = dist_vec.length_squared()
                
                radius_sum = e1.radius + e2.radius
                min_dist_sq = radius_sum * radius_sum
                
                if dist_sq < min_dist_sq:
                    # Collision detected!
                    dist = dist_vec.length()
                    
                    if dist == 0:
                        dist_vec = pygame.Vector2(1, 0)
                        dist = 1.0
                    
                    overlap = radius_sum - dist
                    
                    # 1. Position Correction (Push apart)
                    # Move each away by half overlap
                    normal = dist_vec.normalize()
                    separation = normal * (overlap / 2.0)
                    
                    e1.position += separation
                    e2.position -= separation
                    
                    # Update Rects immediately so other collisions use fresh pos
                    e1.rect.center = (int(e1.position.x), int(e1.position.y))
                    e2.rect.center = (int(e2.position.x), int(e2.position.y))
                    
                    # 2. Physics Bounce (Knockback)
                    # Apply a force to separate them velocity-wise
                    bounce_force = 200 # Adjustable bounce strength
                    
                    # If they are moving towards each other, reflect?
                    # For now just apply additive knockback to ensure they fly apart
                    e1.apply_knockback(normal * bounce_force)
                    e2.apply_knockback(-normal * bounce_force)

    def resolve_bomb_collisions(self, bombs, enemies):
        for bomb in bombs:
            if not bomb.is_active:
                continue
                
            for enemy in enemies:
                # Apply Push Force
                # (Roar Bomb doesn't do damage, just pushes)
                force = bomb.get_push_force(enemy.position)
                if force.length_squared() > 0:
                     enemy.apply_knockback(force)
