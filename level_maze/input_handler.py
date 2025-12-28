import pygame
import math

class InputHandler:
    def __init__(self):
        # Initialize controller if available
        self.joysticks = []
        for i in range(pygame.joystick.get_count()):
            joy = pygame.joystick.Joystick(i)
            joy.init()
            self.joysticks.append(joy)
        
        self.controller_mode = len(self.joysticks) > 0
        if self.controller_mode:
            print(f"Controller detected: {self.joysticks[0].get_name()}")

    def get_move_vector(self):
        """
        Returns a normalized Vector2 for movement.
        Mapped to RIGHT STICK (GDD 2.2).
        Fallback: WASD.
        """
        vector = pygame.Vector2(0, 0)

        if self.controller_mode:
            # Right Stick (usually axis 2 and 3, or 3 and 4 depending on OS/Driver)
            # Standard XInput: Axis 2 (Horizontal), Axis 3 (Vertical)
            # Need to verify per environment, but using standard mappings for now.
            try:
                x = self.joysticks[0].get_axis(2) # Right Stick X
                y = self.joysticks[0].get_axis(3) # Right Stick Y
                if abs(x) > 0.1 or abs(y) > 0.1: # Deadzone
                    vector.x = x
                    vector.y = y
            except:
                pass 
        else:
            # Keyboard Fallback (WASD)
            keys = pygame.key.get_pressed()
            if keys[pygame.K_w]:
                vector.y -= 1
            if keys[pygame.K_s]:
                vector.y += 1
            if keys[pygame.K_a]:
                vector.x -= 1
            if keys[pygame.K_d]:
                vector.x += 1

        if vector.length_squared() > 0:
            return vector.normalize()
        return vector

    def get_look_vector(self, player_pos):
        """
        Returns a normalized Vector2 for looking direction.
        Mapped to LEFT STICK (GDD 2.2).
        Fallback: Mouse Position relative to player.
        """
        vector = pygame.Vector2(1, 0) # Default Look right

        if self.controller_mode:
            # Left Stick (usually axis 0 and 1)
            try:
                x = self.joysticks[0].get_axis(0)
                y = self.joysticks[0].get_axis(1)
                if abs(x) > 0.1 or abs(y) > 0.1:
                    vector = pygame.Vector2(x, y).normalize()
                    return vector
            except:
                pass
        
        # Mouse Fallback
        # Only use mouse if NO controller input for look was detected (or just always override if moved?)
        # For hybrid testing, we allow mouse to override if controller is idle or not present
        if not self.controller_mode:
            mouse_pos = pygame.Vector2(pygame.mouse.get_pos())
            direction = mouse_pos - player_pos
            if direction.length_squared() > 0:
                return direction.normalize()

        return vector # Return default or previously known vector logic (handled in player)

    def get_abilities_state(self):
        """
        Returns dict of ability states: {'dash': bool, 'roar': bool}
        Dash: Space / Controller Button 0 (A/Cross)
        Roar: Shift / Controller Button 2 (X/Square) or 1 (B/Circle) - GDD says Shift/X (West)
        """
        states = {'dash': False, 'roar': False}
        
        if self.controller_mode:
            try:
                # Dash: A button (0)
                if self.joysticks[0].get_button(0):
                    states['dash'] = True
                
                # Roar: X button (2) - varies by controller, usually West button
                if self.joysticks[0].get_button(2):
                    states['roar'] = True
            except:
                pass

        # Keyboard Fallback
        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE]:
            states['dash'] = True
        if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
            states['roar'] = True
        if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
            states['roar'] = True
            
        return states

    def get_ui_state(self):
        """
        Returns dict of UI inputs: {'select': bool}
        Select: Tab / Controller Button (Back/Select - varies, let's look for common ones)
        """
        states = {'select': False}
        
        # Keyboard
        keys = pygame.key.get_pressed()
        if keys[pygame.K_TAB] or keys[pygame.K_h]:
             states['select'] = True

        # Controller
        if self.controller_mode:
            try:
                 # Usually button 4 (Share/Select/Back) or 6 depending on controller
                 # Checking typical "Back" buttons
                 if self.joysticks[0].get_button(4) or self.joysticks[0].get_button(6):
                     states['select'] = True
                 # PS4 Share is 8, Option is 9. Xbox Back is 6, Start is 7. 
            except:
                pass
        
        return states
