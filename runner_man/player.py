import pygame

class Player:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 40, 60)
        self.velocity_y = 0.0
        self.gravity = 1200.0
        self.jump_force = -600.0
        
        self.ground_y = y # Initial Y is ground level
        self.on_ground = True
        
        self.move_speed = 300.0
        
        # Animation state
        self.timer = 0
        self.sprites = []
        self.current_frame = 0
        self.load_sprites()
        
    def load_sprites(self):
        try:
            sheet = pygame.image.load("runner_man/assets/runner.png").convert_alpha()
            
            # Using Strict 3x3 Grid
            sheet_w, sheet_h = sheet.get_size()
            cols = 3
            rows = 3
            cell_w = sheet_w // cols
            cell_h = sheet_h // rows
            
            # Adjust limit to 9 frames for 3x3
            for y in range(rows):
                for x in range(cols):
                    rect = pygame.Rect(x * cell_w, y * cell_h, cell_w, cell_h)
                    frame = sheet.subsurface(rect)
                    
                    # Scale to Player Size
                    scaled_frame = pygame.transform.scale(frame, (60, 80)) 
                    self.sprites.append(scaled_frame)
                    
        except Exception as e:
            print(f"Failed to load sprites: {e}")
            self.sprites = [] # Fallback to stickman

    def update(self, dt, inputs):
        # inputs: {'left': bool, 'right': bool, 'jump': bool}
        
        # Movement X
        dx = 0
        if inputs['right']:
            dx = self.move_speed * dt
        elif inputs['left']:
            dx = -self.move_speed * dt
            
        self.rect.x += dx
        
        # Clamp Screen Bounds
        if self.rect.left < 0: self.rect.left = 0
        if self.rect.right > 800: self.rect.right = 800
            
        # Physics
        if inputs['jump'] and self.on_ground:
            self.velocity_y = self.jump_force
            self.on_ground = False
            
        self.velocity_y += self.gravity * dt
        self.rect.y += self.velocity_y * dt
        
        # Ground Check
        if self.rect.y >= self.ground_y:
            self.rect.y = self.ground_y
            self.velocity_y = 0
            self.on_ground = True
            
        # Animation Timer
        anim_speed = 10
        if inputs['right']: anim_speed = 15
        elif inputs['left']: anim_speed = 5
        self.timer += dt * anim_speed
        
        if self.sprites:
            self.current_frame = int(self.timer) % len(self.sprites)

    def draw(self, surface):
        if self.sprites:
            # Draw Sprite
            img = self.sprites[self.current_frame]
            # Flip if moving left? 
            # Assuming sprite faces Right default.
            # Runner usually runs Right.
            
            # Center sprite on rect
            # Sprite 60x80. Rect 40x60.
            # Center X, Bottom Y aligned.
            dest_rect = img.get_rect(centerx=self.rect.centerx, bottom=self.rect.bottom)
            surface.blit(img, dest_rect)
        else:
            # Simple procedural animation: Stickman
            # Body
            cx, cy = self.rect.center
            
            color = (255, 255, 255)
            
            # Head
            pygame.draw.circle(surface, color, (cx, self.rect.top + 10), 10)
            # Torso
            pygame.draw.line(surface, color, (cx, self.rect.top + 20), (cx, self.rect.bottom - 20), 4)
            
            # Legs (Running cycle)
            import math
            leg_sway = math.sin(self.timer) * 15
            
            if not self.on_ground:
                # Jump pose
                leg_sway = 20
            
            # Left Leg
            pygame.draw.line(surface, color, (cx, self.rect.bottom - 20), (cx - leg_sway, self.rect.bottom), 4)
            # Right Leg
            pygame.draw.line(surface, color, (cx, self.rect.bottom - 20), (cx + leg_sway, self.rect.bottom), 4)
            
            # Arms
            arm_sway = -leg_sway
            pygame.draw.line(surface, color, (cx, self.rect.top + 25), (cx - arm_sway, self.rect.top + 40), 4)
            pygame.draw.line(surface, color, (cx, self.rect.top + 25), (cx + arm_sway, self.rect.top + 40), 4)

    # def get_speed(self):
    #     return self.base_speed * self.speed_multiplier
