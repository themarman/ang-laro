import pygame
import math

class RadialMenu:
    def __init__(self, screen_center):
        self.center = screen_center
        self.active = False
        self.radius = 150
        self.inner_radius = 50
        
        # Items: List of dicts {'id': str, 'name': str, 'icon': Surface, 'color': tuple}
        self.items = []
        self.selected_index = -1
        
        # Animation State
        self.anim_progress = 0.0 # 0.0 to 1.0
        self.anim_speed = 10.0
        
        # Config
        self.font = pygame.font.SysFont("Arial", 14, bold=True)
        self.large_font = pygame.font.SysFont("Arial", 24, bold=True)
        
        # Colors
        self.col_bg = (20, 20, 30, 220)
        self.col_sector_normal = (40, 40, 50, 200)
        self.col_sector_hover = (60, 60, 80, 230)
        self.col_highlight = (0, 255, 255) # Cyan
        self.col_selected_acc = (255, 100, 0) # Orange
        
    def set_items(self, items_list):
        self.items = items_list
        
    def open(self):
        self.active = True
        self.anim_progress = 0.0
        
    def close(self):
        self.active = False
        self.anim_progress = 0.0
        
    def update(self, dt, input_vec):
        # Animation
        if self.active:
            self.anim_progress = min(1.0, self.anim_progress + dt * self.anim_speed)
        else:
            self.anim_progress = max(0.0, self.anim_progress - dt * self.anim_speed)
            
        if not self.active and self.anim_progress <= 0:
            return

        # Selection Logic
        # Input vec is pygame.Vector2 from stick (x, -y logic usually)
        # Note: Pygame joy axis: y is positive DOWN. 
        # We need generic math. Angle 0 is usually Right. -90 is Up.
        
        self.selected_index = -1
        if len(self.items) > 0 and input_vec.length_squared() > 0.25: # Deadzone
            angle = math.degrees(math.atan2(input_vec.y, input_vec.x))
            # Angle is -180 to 180. 0 is Right. 90 is Down. -90 is Up.
            
            # Divide 360 by N items.
            # We want sector 0 to be at top (-90 degrees) usually?
            # Or radial distribution starting from Right?
            # Let's align 0 to Top (-90).
            # Shift angle so 0 is at -90?
            # Standard math: 0 is Right.
            
            step = 360 / len(self.items)
            
            # Normalize angle to 0-360
            if angle < 0: angle += 360
            
            # Rotate so first sector is centered at TOP (270 degrees or -90)
            # If we want Item 0 at Top:
            # We need standard angle to map to index 0 when angle is around 270.
            
            # Let's just use standard 0 starts at Right and goes Clockwise logic for simplicity?
            # Actually, user expects Up = Top Item.
            
            # Shift angle by +90 so 0 is Up/Top (270 + 90 = 360/0)
            # Original: Right=0, Down=90, Left=180, Up=270
            # Shifted (+90): Right=90, Down=180, Left=270, Up=0 (360) 
            angle_shifted = (angle + 90) % 360
            
            # Index = floor(angle / step)
            # However, we want sector to CENTER on the direction, not start there.
            # So offset by step/2.
            
            angle_offset = (angle_shifted + (step/2)) % 360
            index = int(angle_offset // step)
            self.selected_index = index % len(self.items)

    def draw(self, surface):
        if self.anim_progress <= 0.01:
            return
            
        # Draw Overlay
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, int(150 * self.anim_progress)))
        surface.blit(overlay, (0, 0))
        
        center_x, center_y = self.center
        
        # Scaling
        scale = 0.5 + (0.5 * self.anim_progress) # Pop in
        # We can implement scaling by math or surface transform. Math is cleaner for vectors.
        current_radius = self.radius * scale
        current_inner = self.inner_radius * scale
        
        count = len(self.items)
        if count == 0: return # Nothing to draw
        
        step = 360 / count
        # Start angle needs to align so Item 0 is at Top.
        # Logic update above: Item 0 is Up.
        # So Item 0 center is -90 degrees.
        # Start of Item 0 sector is -90 - (step/2).
        start_angle_deg = -90 - (step / 2)
        
        for i in range(count):
            item = self.items[i]
            is_selected = (i == self.selected_index)
            
            # Calculate Sector Angles
            a1_deg = start_angle_deg + (i * step)
            a2_deg = a1_deg + step
            
            a1 = math.radians(a1_deg)
            a2 = math.radians(a2_deg)
            
            # Draw Sector Poly
            # Points: Center(inner) -> Outer Arc -> Center(inner)
            # To draw arc poly, we need points along the arc.
            points = []
            
            # Inner Arc (Approximated 2 pts or curve? Just 2 corners if simple)
            # Better: Full Polygon
            # Poly Points:
            # 1. Inner Start
            # 2. Outer Start
            # 3. Outer End
            # 4. Inner End
            
            # Inner Start
            p1 = (center_x + math.cos(a1) * current_inner, center_y + math.sin(a1) * current_inner)
            # Outer Start
            p2 = (center_x + math.cos(a1) * current_radius, center_y + math.sin(a1) * current_radius)
            # Outer End
            p3 = (center_x + math.cos(a2) * current_radius, center_y + math.sin(a2) * current_radius)
            # Inner End
            p4 = (center_x + math.cos(a2) * current_inner, center_y + math.sin(a2) * current_inner)
            
            # Colors
            if is_selected:
                color = self.col_sector_hover
                border_col = self.col_selected_acc
                # Expand slightly
                expand = 10 * scale
                p2 = (center_x + math.cos(a1) * (current_radius + expand), center_y + math.sin(a1) * (current_radius + expand))
                p3 = (center_x + math.cos(a2) * (current_radius + expand), center_y + math.sin(a2) * (current_radius + expand))
            else:
                color = self.col_sector_normal
                border_col = self.col_sector_normal
            
            # Draw Sector Body
            pygame.draw.polygon(surface, color, [p1, p2, p3, p4])
            # Draw Border
            pygame.draw.polygon(surface, border_col, [p1, p2, p3, p4], 2)
            
            # Draw Item Icon/Label
            # Center angle
            mid_angle = a1 + (a2 - a1)/2
            mid_dist = (current_inner + current_radius) / 2
            if is_selected: mid_dist += 5
            
            icon_x = center_x + math.cos(mid_angle) * mid_dist
            icon_y = center_y + math.sin(mid_angle) * mid_dist
            
            # Text
            text_col = (255, 255, 255) if is_selected else (200, 200, 200)
            label = self.font.render(item['name'], True, text_col)
            label_rect = label.get_rect(center=(icon_x, icon_y))
            surface.blit(label, label_rect)
            
        # Draw Center Hub
        pygame.draw.circle(surface, self.col_bg, (int(center_x), int(center_y)), int(current_inner - 2))
        pygame.draw.circle(surface, (100, 100, 100), (int(center_x), int(center_y)), int(current_inner - 2), 2)
        
        # Center Text/Icon (Selected Item?)
        if self.selected_index >= 0:
             sel_item = self.items[self.selected_index]
             # Draw Large letter or Icon in center?
             # For now just a circle highlight
             pass

    def get_selection(self):
        if self.selected_index >= 0 and self.selected_index < len(self.items):
            return self.items[self.selected_index]['id']
        return None
