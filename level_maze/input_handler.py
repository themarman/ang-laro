import pygame
import math

class InputHandler:
    def __init__(self, config_manager=None):
        # Initialize controller if available
        self.joysticks = []
        for i in range(pygame.joystick.get_count()):
            joy = pygame.joystick.Joystick(i)
            joy.init()
            self.joysticks.append(joy)
        
        self.controller_mode = len(self.joysticks) > 0
        if self.controller_mode:
            print(f"Controller detected: {self.joysticks[0].get_name()}")
            
        # Load Controls from Config
        self.controls = {
            'keyboard': {'dash': pygame.K_SPACE, 'roar': pygame.K_LSHIFT},
            'gamepad': {'dash': 0, 'roar': 2}
        }
        
        if config_manager:
            try:
                kb_config = config_manager.get("controls.keyboard")
                gp_config = config_manager.get("controls.gamepad")
                
                # Helper to parse key with aliases
                def parse_key(k_name):
                    k_name = k_name.lower().strip()
                    aliases = {
                        'lshift': 'left shift',
                        'rshift': 'right shift',
                        'lctrl': 'left ctrl',
                        'rctrl': 'right ctrl',
                        'lalt': 'left alt',
                        'ralt': 'right alt',
                        'enter': 'return',
                        'esc': 'escape'
                    }
                    return pygame.key.key_code(aliases.get(k_name, k_name))

                if kb_config:
                    if 'dash' in kb_config:
                        try:
                            self.controls['keyboard']['dash'] = parse_key(kb_config['dash'])
                        except ValueError as ve:
                            print(f"Warning: Invalid keyboard key '{kb_config['dash']}' for dash. Using default.")
                    
                    if 'roar' in kb_config: 
                        try:
                            self.controls['keyboard']['roar'] = parse_key(kb_config['roar'])
                        except ValueError as ve:
                            print(f"Warning: Invalid keyboard key '{kb_config['roar']}' for roar. Using default.")

                if gp_config:
                    if 'dash' in gp_config: self.controls['gamepad']['dash'] = int(gp_config['dash'])
                    if 'roar' in gp_config: self.controls['gamepad']['roar'] = int(gp_config['roar'])
                    
            except Exception as e:
                print(f"Error loading controls from config: {e}. Using defaults.")

    def get_move_vector(self):
        """
        Returns a normalized Vector2 for movement.
        Mapped to RIGHT STICK (GDD 2.2).
        Fallback: WASD.
        """
        vector = pygame.Vector2(0, 0)

        if self.controller_mode:
            # Left Stick (usually axis 0 and 1)
            # Standard XInput: Axis 0 (Horizontal), Axis 1 (Vertical)
            # Need to verify per environment, but using standard mappings for now.
            try:
                x = self.joysticks[0].get_axis(0) # Left Stick X
                y = self.joysticks[0].get_axis(1) # Left Stick Y
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
        """
        vector = pygame.Vector2(0, 0)

        # Right Stick (usually axis 2 and 3)
        if self.controller_mode:
            try:
                x = self.joysticks[0].get_axis(2)
                y = self.joysticks[0].get_axis(3)
                if abs(x) > 0.1 or abs(y) > 0.1:
                    vector = pygame.Vector2(x, y).normalize()
            except:
                pass
            
            if vector.length_squared() > 0:
                return vector
        
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
        Dash: Configured Key / Controller Button
        Roar: Configured Key / Controller Button
        """
        states = {'dash': False, 'roar': False}
        
        dash_btn = self.controls['gamepad']['dash']
        roar_btn = self.controls['gamepad']['roar']
        
        dash_key = self.controls['keyboard']['dash']
        roar_key = self.controls['keyboard']['roar']

        if self.controller_mode:
            try:
                # Dash
                if self.joysticks[0].get_button(dash_btn):
                    states['dash'] = True
                
                # Roar
                if self.joysticks[0].get_button(roar_btn):
                    states['roar'] = True
            except:
                pass

        return states

    def get_secondary_ability_state(self):
        is_secondary = False
        
        # Keyboard
        keys = pygame.key.get_pressed()
        sec_key_name = "e"
        if 'keyboard' in self.controls:
             sec_key_name = self.controls.get('keyboard', {}).get('secondary', 'e')

        sec_key = pygame.key.key_code(sec_key_name)
        if keys[sec_key]:
            is_secondary = True
            
        # Gamepad
        if self.controller_mode and len(self.joysticks) > 0:
            sec_btn = 3
            if 'gamepad' in self.controls:
                 sec_btn = int(self.controls.get('gamepad', {}).get('secondary', 3))

            try:
                if self.joysticks[0].get_button(sec_btn):
                    is_secondary = True
            except:
                pass
                
        return is_secondary

    def get_menu_wheel_state(self):
        is_menu = False
        
        # Keyboard
        keys = pygame.key.get_pressed()
        menu_key_name = "q"
        if 'keyboard' in self.controls:
             menu_key_name = self.controls.get('keyboard', {}).get('menu_wheel', 'q')
             
        menu_key = pygame.key.key_code(menu_key_name)
        if keys[menu_key]:
            is_menu = True
            
        # Gamepad
        if self.controller_mode and len(self.joysticks) > 0:
            menu_btn = 4
            if 'gamepad' in self.controls:
                 menu_btn = int(self.controls.get('gamepad', {}).get('menu_wheel', 4))

            try:
                if self.joysticks[0].get_button(menu_btn):
                    is_menu = True
            except:
                pass
                
        return is_menu

    def get_ui_state(self, events):
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
