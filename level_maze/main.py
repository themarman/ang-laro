import pygame
import sys
import math
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
from level_maze.brick_bomb import BrickBomb

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
        {'id': 'brick_bomb', 'name': 'Brick Bomb'},
        {'id': 'cancel', 'name': 'Cancel'}
    ])
    
    enemies = []
    roar_bombs = []
    brick_bombs = []
    
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
        enemies.clear()
        roar_bombs.clear()
        brick_bombs.clear()
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
    
    # Game State: START, PLAYING, PAUSED
    game_state = "START"
    
    # UI State
    # paused = False # Removed in favor of game_state
    
    menu_options = ["Resume", "Restart", "Options", "Exit"]
    menu_selection = 0
    abilities = {'dash': False, 'roar': False}

    show_help = False 
    select_pressed_last_frame = False 
    
    running = True
    # Time Scaling
    time_scale = 1.0
    slowmo_timer = 0.0
    start_screen_timer = 0.0

    # D-Pad State
    dpad_x = 0
    dpad_y = 0

    running = True
    while running:
        # Time management
        real_dt = clock.tick(fps) / 1000.0
        start_screen_timer += real_dt
        
        # Slow Motion logic only if PLAYING
        if game_state == "PLAYING" and not radial_menu.active:
             if slowmo_timer > 0:
                 slowmo_timer -= real_dt
                 time_scale = 0.2
             else:
                 time_scale = 1.0
             game_dt = real_dt * time_scale
             if game_dt > 0.1: game_dt = 0.1
        else:
             game_dt = 0 # Pause physics
             
        # Allow menu Update always? Or only when Playing?
        # Update Menu (Animation always runs)
        # Input Vector for Menu
        menu_input = pygame.Vector2(0,0)
        
        # Event Handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            is_start_btn = False # Explicit Start Button
            is_select_btn = False
            is_nav_up = False
            is_nav_down = False
            is_confirm_btn = False
            is_menu_wheel_btn = False
            
            if event.type == pygame.JOYBUTTONDOWN:
                if event.button == 7: is_start_btn = True # Start (Xbox)
                if event.button == 6: is_select_btn = True # Back
                if event.button == 0: is_confirm_btn = True # A
                if event.button == 4: is_menu_wheel_btn = True # LB
            
            if event.type == pygame.JOYHATMOTION:
                dpad_x = event.value[0]
                dpad_y = event.value[1]
                
                if event.value[1] == 1: is_nav_up = True
                elif event.value[1] == -1: is_nav_down = True
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: is_start_btn = True # Map ESC to Start/Pause toggle for ease?
                if event.key == pygame.K_TAB: is_select_btn = True
                
                if game_state == "PAUSED" or radial_menu.active or game_state == "START":
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

            # STATE: START
            if game_state == "START":
                if is_start_btn or is_confirm_btn:
                    game_state = "PLAYING"
                    # Optional: reset_game() here if we want fresh start on press
                continue # Skip other input logic

            # STATE: PLAYING / PAUSED INPUTS
            
            # PAUSE TOGGLE 
            if is_start_btn or is_select_btn: # Start or Back pauses
                if game_state == "PLAYING":
                    game_state = "PAUSED"
                elif game_state == "PAUSED":
                    game_state = "PLAYING"
            
            # RADIAL MENU TOGGLE
            if is_menu_wheel_btn and game_state == "PLAYING":
                if radial_menu.active:
                    radial_menu.close()
                else:
                    radial_menu.open()
                    pass
                
            # RADIAL MENU INPUT
            if radial_menu.active and game_state == "PLAYING":
                # Use D-Pad State
                # ... (Same Logic) ...
                menu_input = pygame.Vector2(dpad_x, -dpad_y)
                
                if is_confirm_btn:
                    sel_id = radial_menu.get_selection()
                    if sel_id:
                        if sel_id == 'roar_bomb':
                            player.set_active_ability("roar_bomb")
                        elif sel_id == 'brick_bomb':
                            player.set_active_ability("brick_bomb")
                        elif sel_id == 'dash':
                            # Just visual or set something?
                            pass
                        elif sel_id == 'cancel':
                            pass
                        
                    radial_menu.close()
            
            # PAUSE MENU NAVIGATION
            elif game_state == "PAUSED":
                if is_nav_up:
                    menu_selection = (menu_selection - 1) % len(menu_options)
                if is_nav_down:
                    menu_selection = (menu_selection + 1) % len(menu_options)
                
                if is_confirm_btn:
                    option = menu_options[menu_selection]
                    if option == "Resume":
                        game_state = "PLAYING"
                    elif option == "Restart":
                        player = reset_game()
                        game_state = "PLAYING"
                    elif option == "Options":
                        print("Options clicked (Not Implemented)")
                    elif option == "Exit":
                        running = False

        # Update Radial Menu Logic
        radial_menu.update(real_dt, menu_input)

        if game_state == "PLAYING" and not radial_menu.active:
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
                     if isinstance(new_bomb, BrickBomb):
                         brick_bombs.append(new_bomb)
                     else:
                         roar_bombs.append(new_bomb)

             # Check SlowMo Triggers (Flags from Player)
             if player.just_dashed:
                 slowmo_timer = 1.0 # 1 Second SlowMo
             if player.just_roared:
                 slowmo_timer = 1.0

             # Collect Pending Bombs
             if player.pending_bombs:
                 brick_bombs.extend(player.pending_bombs)
                 player.pending_bombs = []

             # Update Entities (Use game_dt)
             # Update Obstacle Manager (Lifespan check)
             obstacle_manager.update(game_dt)
             
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
             
             # Update Brick Bombs
             active_bricks = []
             bombs_obstacles = obstacle_manager.get_obstacles() # Includes previously solidified
             for bb in brick_bombs:
                 # Update against Arena + Obstacles + Enemies
                 bb.update(game_dt, arena, bombs_obstacles, enemies)
                 if bb.is_solidified:
                     # Convert to Obstacle
                     # Lifespan: 1 Minute (60 seconds)
                     obstacle_manager.add_dynamic_obstacle(bb.rect, bb.color, lifespan=60.0)
                     # Remove from active list
                     pass
                 else:
                     active_bricks.append(bb)
             brick_bombs = active_bricks
                 
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
                 game_state = "PAUSED" # Or GAMEOVER
                 
             # Victory Check (All enemies dead)
             if len(enemies) == 0:
                 print("All Enemies Destroyed!")
                 game_state = "PAUSED"
         
        # Draw
        screen.fill((20, 20, 20))
        arena.draw(screen)
        obstacle_manager.draw(screen)
        xtra_manager.draw(screen)
        for enemy in enemies: enemy.draw(screen)
        for bomb in roar_bombs: bomb.draw(screen)
        for bb in brick_bombs: bb.draw(screen)
        
        # Only draw player if not start screen? Or draw everything in BG?
        # User said "when game start... have start overlay". Usually BG is visible.
        player.draw(screen)
        
        # Draw Radial Menu (Always called for animation fade out)
        if radial_menu.active or radial_menu.anim_progress > 0:
            radial_menu.draw(screen)
        
        if game_state == "PAUSED":
            draw_pause_menu(screen, width, height, menu_options, menu_selection, config_manager)
        elif game_state == "START":
            draw_start_screen(screen, width, height, start_screen_timer)
            
        pygame.display.flip()

    pygame.quit()
    sys.exit()

def draw_start_screen(surface, width, height, timer):
    # Dim background
    overlay = pygame.Surface((width, height), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180)) 
    surface.blit(overlay, (0, 0))
    
    title_font = pygame.font.SysFont("Arial", 80, bold=True)
    prompt_font = pygame.font.SysFont("Arial", 40, bold=True)
    
    # Title
    # Shadow
    title_text = "LEVEL MAZE"
    ts = title_font.render(title_text, True, (0, 0, 0))
    tr = ts.get_rect(center=(width//2 + 5, height//2 - 50 + 5))
    surface.blit(ts, tr)
    # Main
    t = title_font.render(title_text, True, (0, 200, 255))
    tr = t.get_rect(center=(width//2, height//2 - 50))
    surface.blit(t, tr)
    
    # Prompt (Blinking)
    alpha = 150 + 105 * math.sin(timer * 5.0)
    prompt_text = "Press START to Begin"
    
    p = prompt_font.render(prompt_text, True, (255, 255, 255))
    p.set_alpha(int(alpha))
    pr = p.get_rect(center=(width//2, height//2 + 50))
    surface.blit(p, pr)

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


