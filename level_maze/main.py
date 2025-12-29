import pygame
import sys
from level_maze.config_manager import ConfigManager
from level_maze.arena import Arena
from level_maze.player import Player
from level_maze.obstacle_manager import ObstacleManager
from level_maze.obstacle_manager import ObstacleManager
from level_maze.enemy import Enemy
import random
from level_maze.input_handler import InputHandler
from level_maze.combat_system import CombatSystem
from level_maze.radial_menu import RadialMenu
from level_maze.xtra_manager import XtraManager

def main():
    # ... (Config loading) ...
    try:
        config_manager = ConfigManager()
        window_config = config_manager.get_window_config()
    except Exception as e:
        print(f"Failed to load configuration: {e}")
        return

    # Initialize Pygame
    pygame.init()
    
    width = window_config.get("width", 800)
    height = window_config.get("height", 600)
    title = window_config.get("title", "Level Maze")
    fps = window_config.get("fps", 60)

    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption(title)
    clock = pygame.time.Clock()
    
    # Initialize Game Objects
    arena_width = width - 100
    arena_height = height - 100
    arena_x = 50
    arena_y = 50
    arena = Arena(arena_x, arena_y, arena_width, arena_height)
    
    # Placeholder for game objects
    player = None
    input_handler = InputHandler(config_manager)
    obstacle_manager = ObstacleManager()
    combat_system = CombatSystem()
    xtra_manager = XtraManager()
    
    # UI Components
    radial_menu = RadialMenu((width // 2, height // 2))
    # Define Abilities for Menu
    radial_menu.set_items([
        {'id': 'roar_bomb', 'name': 'Roar Bomb'},
        {'id': 'cancel', 'name': 'Cancel'}
    ])
    
    enemies = []
    roar_bombs = []
    
    def reset_game():
        # Create new player
        new_player = Player(width // 2, height // 2, config_manager)
        
        # Reset Obstacles
        obstacle_manager.reset()
        xtra_manager.reset()
        # Define a safe zone around player for spawning
        player_safe_zone = pygame.Rect(new_player.position.x - 100, new_player.position.y - 100, 200, 200)
        obstacle_manager.generate_obstacles(arena, player_safe_zone)
        
        # Reset Enemies
        enemies.clear()
        roar_bombs.clear()
        enemy_count = config_manager.get("enemies.count", 5)
        spawn_enemies(enemy_count, new_player)
        
        print("Game Reset!")
        return new_player

    def spawn_enemies(count, player_ref):
        spawned_count = 0
        attempts = 0
        max_attempts = 1000
        
        while spawned_count < count and attempts < max_attempts:
            attempts += 1
            # Random position in arena (padding for wall)
            # Enemy radius is 15. Padding 20.
            ex = random.randint(arena.rect.left + 20, arena.rect.right - 20)
            ey = random.randint(arena.rect.top + 20, arena.rect.bottom - 20)
            
            enemy_rect = pygame.Rect(ex - 15, ey - 15, 30, 30)
            
            # Check Obstacles
            collides = False
            for obs in obstacle_manager.get_obstacles():
                # Inflate obstacle slightly to ensure gap
                if enemy_rect.colliderect(obs.rect.inflate(10, 10)):
                    collides = True
                    break
            
            if not collides:
                # Also check player safe zone (don't spawn ON TOP of player)
                player_rect = pygame.Rect(player_ref.position.x - 50, player_ref.position.y - 50, 100, 100)
                if not enemy_rect.colliderect(player_rect):
                    enemies.append(Enemy(ex, ey))
                    spawned_count += 1
                    
        print(f"Spawned {spawned_count} enemies after {attempts} attempts.")

    # Initial Game Start
    player = reset_game()
    
    # UI State
    paused = False
    # radial_menu_active is now managed via radial_menu.active
    
    menu_options = ["Resume", "Restart", "Options", "Exit"]
    menu_selection = 0
    abilities = {'dash': False, 'roar': False}

    show_help = False 
    select_pressed_last_frame = False 
    
    running = True
    # Time Scaling
    time_scale = 1.0
    slowmo_timer = 0.0

    # D-Pad State
    dpad_x = 0
    dpad_y = 0

    running = True
    while running:
        # Time management
        real_dt = clock.tick(fps) / 1000.0
        
        # Slow Motion logic only if not in a menu
        if not paused and not radial_menu.active:
             if slowmo_timer > 0:
                 slowmo_timer -= real_dt
                 time_scale = 0.2
             else:
                 time_scale = 1.0
             game_dt = real_dt * time_scale
             if game_dt > 0.1: game_dt = 0.1
        else:
             game_dt = 0 # Pause physics

        # Update Menu (Animation always runs)
        # Input Vector for Menu
        menu_input = pygame.Vector2(0,0)
        
        # Event Handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            is_select_btn = False
            is_nav_up = False
            is_nav_down = False
            is_confirm_btn = False
            is_menu_wheel_btn = False
            
            if event.type == pygame.JOYBUTTONDOWN:
                if event.button == 6 or event.button == 7: is_select_btn = True # Back/Start
                if event.button == 0: is_confirm_btn = True # A
                if event.button == 4: is_menu_wheel_btn = True # LB
            
            if event.type == pygame.JOYHATMOTION:
                # Hat 0 is usually the D-Pad
                # event.value is a tuple (x, y). 
                # x: -1 Left, 1 Right
                # y: -1 Down, 1 Up (Note: Standard Pygame hat Y is usually Up=1, Down=-1, logic check below)
                dpad_x = event.value[0]
                dpad_y = event.value[1]
                
                if event.value[1] == 1: is_nav_up = True
                elif event.value[1] == -1: is_nav_down = True
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_TAB or event.key == pygame.K_ESCAPE:
                    is_select_btn = True
                if paused or radial_menu.active:
                    if event.key == pygame.K_w or event.key == pygame.K_UP: 
                        is_nav_up = True
                        dpad_y = 1
                        dpad_x = 0
                    if event.key == pygame.K_s or event.key == pygame.K_DOWN: 
                        is_nav_down = True
                        dpad_y = -1
                        dpad_x = 0
                    if event.key == pygame.K_a or event.key == pygame.K_LEFT:
                        dpad_x = -1
                        dpad_y = 0
                    if event.key == pygame.K_d or event.key == pygame.K_RIGHT:
                        dpad_x = 1
                        dpad_y = 0
                    
                    if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE: is_confirm_btn = True
                # Keyboard mapping for menu wheel?
                if event.key == pygame.K_q: is_menu_wheel_btn = True

            # PAUSE TOGGLE (Standard Menu)
            if is_select_btn and not radial_menu.active:
                paused = not paused
            
            # RADIAL MENU TOGGLE
            if is_menu_wheel_btn and not paused:
                if radial_menu.active:
                    radial_menu.close()
                else:
                    radial_menu.open()
                    pass
                
            # RADIAL MENU INPUT
            if radial_menu.active:
                # Use D-Pad State
                # Pygame hat: Y is Up=1.
                # Radial Menu Math expects:
                # Vector(0, 1) -> Up?
                # atan2(y, x). 
                # If we pass (0, 1): atan2(1, 0) = 90 deg.
                # My logic: 90 is Down.
                # Wait, screen Y is Down positive.
                # If stick Up (-1), vector is (0, -1). atan2(-1, 0) = -90.
                # My logic: -90 is Top.
                # So for Hat Up=1, we should flip Y to match screen coords (-1) if we want standard behavior?
                # Hat: Up=1. Screen: Up=-1.
                # So pass -dpad_y to Y component.
                
                menu_input = pygame.Vector2(dpad_x, -dpad_y)
                
                if is_confirm_btn:
                    sel_id = radial_menu.get_selection()
                    if sel_id:
                        if sel_id == 'roar_bomb':
                            player.set_active_ability("roar_bomb")
                        elif sel_id == 'dash':
                            # Just visual or set something?
                            pass
                        elif sel_id == 'cancel':
                            pass
                        
                    radial_menu.close()
            
            # PAUSE MENU NAVIGATION
            elif paused:
                if is_nav_up:
                    menu_selection = (menu_selection - 1) % len(menu_options)
                if is_nav_down:
                    menu_selection = (menu_selection + 1) % len(menu_options)
                
                if is_confirm_btn:
                    option = menu_options[menu_selection]
                    if option == "Resume":
                        paused = False
                    elif option == "Restart":
                        player = reset_game()
                        paused = False
                    elif option == "Options":
                        print("Options clicked (Not Implemented)")
                    elif option == "Exit":
                        running = False

        # Update Radial Menu Logic
        # Time calc for animation: use real_dt
        radial_menu.update(real_dt, menu_input)

        if not paused and not radial_menu.active:
             # Regular Input
             input_state = input_handler.get_abilities_state()
             abilities['dash'] = input_state['dash']
             abilities['roar'] = input_state['roar']
             
             if abilities['dash']:
                player.attempt_dash()
            
             if abilities['roar']:
                if player.attempt_roar():
                    # Apply Roar Effect (AoE Push)
                    roar_radius = player.get_roar_radius()
                    for enemy in enemies:
                        diff = enemy.position - player.position
                        dist = diff.length()
                        if dist < roar_radius:
                            push_dir = diff.normalize() if dist > 0 else pygame.Vector2(1,0)
                            roar_force = 500 # Strong impulse
                            enemy.apply_knockback(push_dir * roar_force)

             # Secondary Ability (Roar Bomb)
             if input_handler.get_secondary_ability_state():
                 new_bomb = player.attempt_secondary_ability()
                 if new_bomb:
                     roar_bombs.append(new_bomb)

             # Check SlowMo Triggers (Flags from Player)
             if player.just_dashed:
                 slowmo_timer = 1.0 # 1 Second SlowMo
             if player.just_roared:
                 slowmo_timer = 1.0

             # Update Entities (Use game_dt)
             obstacles = obstacle_manager.get_obstacles()
             player.update(game_dt, input_handler, arena, obstacles)
             xtra_manager.update(game_dt, arena, obstacles)
             for enemy in enemies:
                 enemy.update(game_dt, player, arena, obstacles)
             
             # Update Bombs
             active_bombs = []
             for bomb in roar_bombs:
                 bomb.update(game_dt, arena)
                 if bomb.is_active:
                     active_bombs.append(bomb)
             roar_bombs = active_bombs
                 
             combat_system.resolve_collisions(player, enemies, game_dt)
             combat_system.resolve_enemy_collisions(enemies)
             combat_system.resolve_bomb_collisions(roar_bombs, enemies)
             
             # Xtra Collection
             for xtra in xtra_manager.get_xtras():
                 if xtra.active:
                     if player.rect.colliderect(xtra.rect):
                         xtra.on_collect(player)
                         xtra.active = False
                     else:
                         for enemy in enemies:
                             if enemy.rect.colliderect(xtra.rect):
                                 xtra.on_collect(enemy)
                                 xtra.active = False
                                 break
             
            # Remove dead enemies and Award XP
             alive_enemies = []
             for e in enemies:
                 if e.health > 0:
                     alive_enemies.append(e)
                 else:
                     player.gain_xp(50) # XP Value for Kill
             
             enemies = alive_enemies
             
             # Death Check (Trigger Menu)
             if player.health <= 0:
                 print("Player Died!")
                 paused = True
                 
             # Victory Check (All enemies dead)
             if len(enemies) == 0:
                 print("All Enemies Destroyed!")
                 paused = True


        # Draw
        screen.fill((20, 20, 20))
        arena.draw(screen)
        obstacle_manager.draw(screen)
        xtra_manager.draw(screen)
        for enemy in enemies: enemy.draw(screen)
        for bomb in roar_bombs: bomb.draw(screen)
        player.draw(screen)
        
        # Draw Radial Menu (Always called for animation fade out)
        if radial_menu.active or radial_menu.anim_progress > 0:
            radial_menu.draw(screen)
        
        if paused:
            draw_pause_menu(screen, width, height, menu_options, menu_selection, config_manager)

        pygame.display.flip()

    pygame.quit()
    sys.exit()

def draw_pause_menu(surface, width, height, options, selection, config_manager):
    # ... (Keep existing implementation) ...

    # Dim background
    overlay = pygame.Surface((width, height), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 200)) # Darker fade
    surface.blit(overlay, (0, 0))
    
    font = pygame.font.SysFont("Arial", 24)
    title_font = pygame.font.SysFont("Arial", 40, bold=True)
    option_font = pygame.font.SysFont("Arial", 32, bold=True)
    
    # Resolve Control Names
    kb_dash = "N/A"
    kb_roar = "N/A"
    gp_dash = "N/A"
    gp_roar = "N/A"
    
    if config_manager:
        # Keyboard
        kb_config = config_manager.get("controls.keyboard")
        if kb_config:
            if 'dash' in kb_config: kb_dash = kb_config['dash'].upper()
            if 'roar' in kb_config: kb_roar = kb_config['roar'].upper()
            
        # Gamepad Map
        gp_map = {
            0: "A / Cross", 1: "B / Circle", 2: "X / Square", 3: "Y / Triangle",
            4: "LB / L1", 5: "RB / R1", 6: "Back / Select", 7: "Start",
            8: "L3", 9: "R3", 10: "Guide"
        }
        gp_config = config_manager.get("controls.gamepad")
        if gp_config:
            if 'dash' in gp_config: gp_dash = gp_map.get(int(gp_config['dash']), f"Btn {gp_config['dash']}")
            if 'roar' in gp_config: gp_roar = gp_map.get(int(gp_config['roar']), f"Btn {gp_config['roar']}")

    # 1. Info Text Block
    info_lines = [
        ("LEVEL MAZE", title_font),
        ("Controls:", font),
        ("Left Stick / WASD : Move", font),
        ("Right Stick / Mouse : Look", font),
        (f"{gp_dash} / {kb_dash} : Dash", font),
        (f"{gp_roar} / {kb_roar} : Roar", font),
        ("Start / Select : Resume", font)
    ]
    
    # Calculate Info Block Height
    total_height = 0
    line_spacing = 30
    for text, fnt in info_lines:
        total_height += fnt.get_height() + 10
    
    total_height += 60 # Gap before menu
    
    # Add Menu Options Height
    for opt in options:
        total_height += option_font.get_height() + 20
        
    # Start Y to Center Vertically
    current_y = (height - total_height) // 2
    
    # Draw Info
    for text, fnt in info_lines:
        surf = fnt.render(text, True, (200, 200, 200))
        rect = surf.get_rect(center=(width // 2, current_y + surf.get_height()//2))
        surface.blit(surf, rect)
        current_y += surf.get_height() + 10
    
    current_y += 40 # Gap
    
    # Draw Options
    for i, opt in enumerate(options):
        color = (255, 255, 255) if i == selection else (100, 100, 100)
        prefix = "> " if i == selection else "  "
        
        text = prefix + opt
        surf = option_font.render(text, True, color)
        rect = surf.get_rect(center=(width // 2, current_y + surf.get_height()//2))
        surface.blit(surf, rect)
        current_y += surf.get_height() + 20

if __name__ == "__main__":
    main()


