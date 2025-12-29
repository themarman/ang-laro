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
from level_maze.xtra_manager import XtraManager

def main():
    # Initialize Config
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
    # Center the arena
    arena_width = width - 100
    arena_height = height - 100
    arena_x = 50
    arena_y = 50
    arena = Arena(arena_x, arena_y, arena_width, arena_height)

    input_handler = InputHandler()
    player = Player(width // 2, height // 2, config_manager)

    # Initialize Obstacles
    obstacle_manager = ObstacleManager()
    # Define a safe zone around player for spawning
    player_safe_zone = pygame.Rect(player.position.x - 100, player.position.y - 100, 200, 200)
    obstacle_manager.generate_obstacles(arena, player_safe_zone)

    # Initialize Enemy (Safe Spawn)
    enemies = []
    
    def spawn_enemies(count):
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
                player_rect = pygame.Rect(player.position.x - 50, player.position.y - 50, 100, 100)
                if not enemy_rect.colliderect(player_rect):
                    enemies.append(Enemy(ex, ey))
                    spawned_count += 1
                    
        print(f"Spawned {spawned_count} enemies after {attempts} attempts.")

    # Spawn enemies from config
    enemy_count = config_manager.get("enemies.count", 5)
    spawn_enemies(enemy_count)

    combat_system = CombatSystem()
    xtra_manager = XtraManager()
    
    # UI State
    paused = False
    menu_options = ["Resume", "Options", "Exit"]
    menu_selection = 0
    abilities = {'dash': False, 'roar': False} # Initialize defaults

    show_help = False # Deprecated but kept if referenced elsewhere (replaced by paused)
    select_pressed_last_frame = False 

    running = True
    # Time Scaling
    time_scale = 1.0
    slowmo_timer = 0.0

    running = True
    while running:
        # Time management
        real_dt = clock.tick(fps) / 1000.0 # Delta time in seconds (Real time)
        
        # Slow Motion Logic
        if slowmo_timer > 0:
            slowmo_timer -= real_dt
            target_scale = 0.2 # 20% speed
            # Smooth transition? Or instant? Instant is punchier.
            time_scale = target_scale
        else:
            time_scale = 1.0
            
        game_dt = real_dt * time_scale
        # Cap dt to avoid large jumps if lag?
        if game_dt > 0.1: game_dt = 0.1

        # Event Handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            is_select_btn = False
            is_nav_up = False
            is_nav_down = False
            is_confirm_btn = False
            
            if event.type == pygame.JOYBUTTONDOWN:
                if event.button == 6 or event.button == 4: is_select_btn = True # Back/Select
                if event.button == 0: is_confirm_btn = True # A
            
            if event.type == pygame.JOYHATMOTION:
                # Hat 0 is usually the D-Pad
                # event.value is a tuple (x, y). y: 1=UP, -1=DOWN
                if event.value[1] == 1: is_nav_up = True
                elif event.value[1] == -1: is_nav_down = True
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_TAB or event.key == pygame.K_ESCAPE:
                    is_select_btn = True
                if paused:
                    if event.key == pygame.K_w or event.key == pygame.K_UP: is_nav_up = True
                    if event.key == pygame.K_s or event.key == pygame.K_DOWN: is_nav_down = True
                    if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE: is_confirm_btn = True

            # PAUSE TOGGLE
            if is_select_btn:
                paused = not paused
            
            # MENU NAVIGATION
            if paused:
                if is_nav_up:
                    menu_selection = (menu_selection - 1) % len(menu_options)
                if is_nav_down:
                    menu_selection = (menu_selection + 1) % len(menu_options)
                
                if is_confirm_btn:
                    option = menu_options[menu_selection]
                    if option == "Resume":
                        paused = False
                    elif option == "Options":
                        print("Options clicked (Not Implemented)")
                    elif option == "Exit":
                        running = False

        if not paused:
             # Regular Input
             # InputHandler polled in update() (passed below)
             # But abilities check needs to pass Input to player OR check state here.
             
             # Note: logic was checking abilities here and calling player methods.
             # We need to respect that flow.
             input_state = input_handler.get_abilities_state()
             abilities['dash'] = input_state['dash']
             abilities['roar'] = input_state['roar']
             
             # Pass generic input state to player.update? 
             # Currently player.update calls input_handler internal get methods.
             # Dashes/Roars were handled here explicitly before update?
             # Wait, previous code:
             # if abilities['dash']: player.attempt_dash()
             # if abilities['roar']: player.attempt_roar()...
             
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
                 
             combat_system.resolve_collisions(player, enemies, game_dt)
             combat_system.resolve_enemy_collisions(enemies)
             
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
             
             # Death Check
             if player.health <= 0:
                 print("Player Died!")
                 player.health = 100
                 player.position = pygame.Vector2(width // 2, height // 2)

        # Draw
        screen.fill((20, 20, 20))
        arena.draw(screen)
        obstacle_manager.draw(screen)
        xtra_manager.draw(screen)
        for enemy in enemies: enemy.draw(screen)
        player.draw(screen)
        
        if paused:
            draw_pause_menu(screen, width, height, menu_options, menu_selection)

        pygame.display.flip()

    pygame.quit()
    sys.exit()

def draw_pause_menu(surface, width, height, options, selection):
    # Dim background
    overlay = pygame.Surface((width, height), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 200)) # Darker fade
    surface.blit(overlay, (0, 0))
    
    font = pygame.font.SysFont("Arial", 24)
    title_font = pygame.font.SysFont("Arial", 40, bold=True)
    option_font = pygame.font.SysFont("Arial", 32, bold=True)
    
    # 1. Info Text Block
    info_lines = [
        ("LEVEL MAZE", title_font),
        ("Controls:", font),
        ("Left Stick / WASD : Move", font),
        ("Right Stick / Mouse : Look", font),
        ("A / Space : Dash", font),
        ("X / Shift : Roar", font),
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
