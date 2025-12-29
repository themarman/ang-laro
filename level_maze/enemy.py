import pygame
import random
import math
import heapq

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
        self.state = "PATROL" # PATROL, CHASE, INVESTIGATE, STUCK_BACKOFF, PATHFINDING
        self.target_position = None
        self.patrol_timer = 0.0
        
        # Stuck Detection
        self.last_position = self.position.copy()
        self.stuck_timer = 0.0
        self.stuck_threshold = 5.0 # Distance moved in 1 second to not be considered stuck
        
        # Pathfinding / Backoff
        self.stuck_backoff_timer = 0.0
        self.path_step = 0
        self.repath_timer = 0.0

        # Bounce Loop Detection
        self.last_bounce_pos = None
        self.bounce_count = 0

        self.rect = pygame.Rect(x - radius, y - radius, radius * 2, radius * 2)

    def update(self, dt, player, arena, obstacles):
        # 0. Stuck Detection (Global Check)
        if self.state == "CHASE":
            self.stuck_timer += dt
            if self.stuck_timer >= 1.0:
                dist_moved = self.position.distance_to(self.last_position)
                if dist_moved < self.stuck_threshold:
                    print("Enemy Stuck! Switching to BACKOFF.")
                    self.state = "STUCK_BACKOFF"
                    self.stuck_backoff_timer = random.uniform(0.5, 1.0)
                    
                    # Pick a direction away from current look direction (which is likely into a wall)
                    # Simple heuristic: Reverse + random noise
                    angle = random.uniform(135, 225) 
                    current_angle = math.degrees(math.atan2(self.look_direction.y, self.look_direction.x))
                    new_angle = math.radians(current_angle + angle)
                    self.look_direction = pygame.Vector2(math.cos(new_angle), math.sin(new_angle))
                
                self.stuck_timer = 0
                self.last_position = self.position.copy()

        # 1. Vision Check (Simple LOS)
        can_see = self.check_line_of_sight(player, obstacles)
        
        if self.state == "STUCK_BACKOFF":
            self.stuck_backoff_timer -= dt
            if self.stuck_backoff_timer <= 0:
                print("Backoff done. Switching to PATHFINDING.")
                self.state = "PATHFINDING"
                self.path = self.find_path(self.position, player.position, obstacles, arena)
                self.path_step = 0
                self.repath_timer = 2.0 # Re-calculate path every 2 seconds if still pathfinding

        elif self.state == "PATHFINDING":
            self.repath_timer -= dt
            
            # Optimization: If we can see the player again, switch back to Chase!
            if can_see:
                 print("Regained LOS! Switching to CHASE.")
                 self.state = "CHASE"
                 self.target_position = player.position
            
            elif self.repath_timer <= 0:
                 self.path = self.find_path(self.position, player.position, obstacles, arena)
                 self.path_step = 0
                 self.repath_timer = 2.0
            
            if not self.path or self.path_step >= len(self.path):
                # Path finished or failed, try investigating last known pos
                self.state = "INVESTIGATE"
                self.target_position = player.position

        elif can_see and self.state != "STUCK_BACKOFF":
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
        
        elif self.state == "PATHFINDING":
             if self.path and self.path_step < len(self.path):
                 target_node = self.path[self.path_step]
                 to_node = target_node - self.position
                 if to_node.length() < 20: # Reached node
                     self.path_step += 1
                 else:
                     desired_direction = to_node.normalize()

        elif self.state == "STUCK_BACKOFF":
             desired_direction = self.look_direction

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
        
        if arena.contains(next_rect):
            # Check collisions
            colliding_obs = self.get_colliding_obstacle(next_rect, obstacles)
            
            if not colliding_obs:
                self.position = next_pos
                self.rect = next_rect
            else:
                # HIT OBSTACLE
                # 1. Physics Bounce
                # Determine collision normal
                # Simple AABB logic: Find axis of least penetration on the *current* position vs obstacle
                # OR just use relative centers
                
                # Let's verify which side we hit.
                # Use current position (before move) to determine relative direction
                dx = (self.rect.centerx - colliding_obs.rect.centerx) / (colliding_obs.rect.width / 2 + self.radius)
                dy = (self.rect.centery - colliding_obs.rect.centery) / (colliding_obs.rect.height / 2 + self.radius)
                
                bounce_force = 300
                
                if abs(dx) > abs(dy):
                    # Hit on sides
                    normal = pygame.Vector2(1 if dx > 0 else -1, 0)
                else:
                    # Hit on top/bottom
                    normal = pygame.Vector2(0, 1 if dy > 0 else -1)
                
                # Apply knockback
                self.apply_knockback(normal * bounce_force)
                
                # Check for Bounce Loop
                if self.last_bounce_pos and self.position.distance_to(self.last_bounce_pos) < 10:
                    self.bounce_count += 1
                else:
                    self.bounce_count = 1 # Reset if far from last bounce
                    self.last_bounce_pos = self.position.copy()
                
                if self.bounce_count >= 2:
                    print(f"Enemy stuck bouncing ({self.bounce_count} times)! Randomizing direction.")
                    # Pick random direction that is NOT the current normal (or close to it)
                    # Heuristic: Just random 360 for now, but ensure it's different enough?
                    # Random 360 is simplest and effective enough for loop breaking.
                    angle = random.uniform(0, 360)
                    rad = math.radians(angle)
                    self.look_direction = pygame.Vector2(math.cos(rad), math.sin(rad))
                    self.bounce_count = 0 # Reset
                
                # 2. AI Reaction
                if self.state == "PATROL" and self.knockback.length_squared() < 100:
                    self.patrol_timer = 0.0 # Force retarget
                
                if self.state == "STUCK_BACKOFF":
                     # Pick new random direction
                     angle = random.uniform(0, 360)
                     rad = math.radians(angle)
                     self.look_direction = pygame.Vector2(math.cos(rad), math.sin(rad))
        else:
             # Hit Arena Wall
             # Similar bounce logic for arena bounds
             bounce_force = 300
             normal = pygame.Vector2(0,0)
             if next_rect.left < arena.rect.left: normal.x = 1
             elif next_rect.right > arena.rect.right: normal.x = -1
             if next_rect.top < arena.rect.top: normal.y = 1
             elif next_rect.bottom > arena.rect.bottom: normal.y = -1
             
             if normal.length_squared() > 0:
                 self.apply_knockback(normal.normalize() * bounce_force)
                 
             if self.state == "PATROL": self.patrol_timer = 0.0

    def check_obstacle_collision(self, rect, obstacles):
        for obs in obstacles:
            if rect.colliderect(obs.rect):
                return True
        return False

    def get_colliding_obstacle(self, rect, obstacles):
        for obs in obstacles:
            if rect.colliderect(obs.rect):
                return obs
        return None

    def check_line_of_sight(self, player, obstacles):
        # Simple Raycast: Line from self to player does not intersect any obstacle
        line_start = self.position
        line_end = player.position
        
        for obs in obstacles:
            # clip_line returns the segment of the line inside the rect, or empty if none
            if obs.rect.clipline(line_start, line_end):
                return False
        return True

    def find_path(self, start, end, obstacles, arena):
        """
        Calculates A* path from start Vector2 to end Vector2.
        Uses a coarse grid overlay on the arena.
        """
        grid_size = 40 # Roughly enemy size + buffer
        
        # Helper to snap pos to grid center
        def to_grid(pos):
            return (int(pos.x // grid_size), int(pos.y // grid_size))
            
        def from_grid(grid_pos):
             return pygame.Vector2(grid_pos[0] * grid_size + grid_size/2, grid_pos[1] * grid_size + grid_size/2)

        start_node = to_grid(start)
        end_node = to_grid(end)
        
        # Arena bounds (in grid coords)
        min_x = int(arena.rect.left // grid_size)
        max_x = int(arena.rect.right // grid_size)
        min_y = int(arena.rect.top // grid_size)
        max_y = int(arena.rect.bottom // grid_size)
        
        open_set = []
        heapq.heappush(open_set, (0, start_node))
        
        came_from = {}
        g_score = {start_node: 0.0}
        f_score = {start_node: self.heuristic(start_node, end_node)}
        
        found = False
        
        while open_set:
            current = heapq.heappop(open_set)[1]
            
            if current == end_node:
                found = True
                break
            
            # Neighbors (up, down, left, right + diagonals)
            dirs = [(0,1), (0,-1), (1,0), (-1,0), (1,1), (-1,-1), (1,-1), (-1,1)]
            for dx, dy in dirs:
                neighbor = (current[0] + dx, current[1] + dy)
                
                # Bounds check
                if not (min_x <= neighbor[0] <= max_x and min_y <= neighbor[1] <= max_y):
                    continue
                
                # Collision Check (Check if grid cell overlaps any obstacle)
                # Create a rect for the grid cell
                # INFLATE the check slightly to ensure clearance for the enemy (radius 15 -> 30 size)
                # The grid is 40, so it's already "safe" if centered.
                # But let's check a slightly larger area to discourage hugging walls too tight
                
                check_size = grid_size # 40
                cell_rect = pygame.Rect(neighbor[0] * grid_size, neighbor[1] * grid_size, check_size, check_size)
                
                # Check walls (Arena) - technically handled by bounds but strict check good
                if not arena.rect.contains(cell_rect):
                    continue
                    
                # Check obstacles
                blocked = False
                for obs in obstacles:
                    # Inflate obstacle for the check?
                    # or inflate cell?
                    # If we inflate cell by, say, 10px, we ensure we stand 5px away from any obstacle edge
                    if cell_rect.inflate(10, 10).colliderect(obs.rect):
                        blocked = True
                        break
                if blocked:
                    continue
                
                # G Score
                dist = 1.414 if dx!=0 and dy!=0 else 1.0
                tentative_g = g_score[current] + dist
                
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + self.heuristic(neighbor, end_node)
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))
                    
        # Reconstruct path
        path = []
        if found:
            curr = end_node
            while curr in came_from:
                path.append(from_grid(curr))
                curr = came_from[curr]
            path.reverse()
        return path

    def heuristic(self, a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1]) # Manhattan distance

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.position.x), int(self.position.y)), self.radius)
        
        # Arrow
        arrow_tip = self.position + self.look_direction * (self.radius + 5)
        pygame.draw.line(surface, (255, 255, 255), self.position, arrow_tip, 3)

        # Path Debug
        if self.state == "PATHFINDING" and len(self.path) > 0:
             if self.path_step < len(self.path):
                # Draw remaining path
                pts = [self.position] + self.path[self.path_step:]
                if len(pts) > 1:
                    pygame.draw.lines(surface, (255, 255, 0), False, pts, 2)
                # Draw current target
                pygame.draw.circle(surface, (0, 255, 255), (int(self.path[self.path_step].x), int(self.path[self.path_step].y)), 5)

        # Health Bar
        pygame.draw.rect(surface, (255, 0, 0), (self.position.x - 15, self.position.y - 20, 30, 4))
        pygame.draw.rect(surface, (0, 255, 0), (self.position.x - 15, self.position.y - 20, 30 * (max(0, self.health) / 50.0), 4))

    def take_damage(self, amount):
        self.health -= amount
        print(f"Enemy took {amount} damage. HP: {self.health}")

    def apply_knockback(self, force_vector):
        self.knockback = force_vector
