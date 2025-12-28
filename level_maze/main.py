import pygame
import sys
from level_maze.config_manager import ConfigManager
from level_maze.arena import Arena
from level_maze.player import Player
from level_maze.obstacle_manager import ObstacleManager
from level_maze.enemy import Enemy
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

    # Initialize Enemy (Test Spawn)
    enemies = []
    # Spawn a few enemies for testing
    enemies.append(Enemy(100, 100))
    enemies.append(Enemy(width - 100, height - 100))

    combat_system = CombatSystem()
    xtra_manager = XtraManager()
    
    # UI State
    show_help = False
    select_pressed_last_frame = False # Debounce

    running = True
    while running:
        # Time management
        dt = clock.tick(fps) / 1000.0 # Delta time in seconds

        # Event Handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r:
                    # Debug: Reset
                    obstacle_manager.generate_obstacles(arena, pygame.Rect(player.position.x - 50, player.position.y - 50, 100, 100))
                    player.health = 100
                    enemies = [Enemy(100, 100), Enemy(width - 100, height - 100)]
                    player.xp = 0
                    player.level = 1
        
        # UI Input (Global)
        ui_input = input_handler.get_ui_state()
        if ui_input['select']:
            if not select_pressed_last_frame:
                show_help = not show_help # Toggle
            select_pressed_last_frame = True
        else:
            select_pressed_last_frame = False

        if not show_help:
            # Game Logic Updates (Only run if not paused by help)
            
            # Handle Abilities Input
            abilities = input_handler.get_abilities_state()
            
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
                            # Push away
                            push_dir = diff.normalize() if dist > 0 else pygame.Vector2(1,0)
                            roar_force = 500 # Strong impulse
                            enemy.apply_knockback(push_dir * roar_force)

            # Update
            obstacles = obstacle_manager.get_obstacles()
            
            player.update(dt, input_handler, arena)
            
            xtra_manager.update(dt, arena, obstacles)
            
            for enemy in enemies:
                enemy.update(dt, player, arena, obstacles)

            # Combat Resolution
            combat_system.resolve_collisions(player, enemies, dt)

            # Xtra Collection Check
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
            
            # Check Player Death (Restart?)
            if player.health <= 0:
                print("Player Died!")
                player.health = 100
                player.position = pygame.Vector2(width // 2, height // 2)

        # Draw
        screen.fill((20, 20, 20)) # Dark background
        
        arena.draw(screen)
        obstacle_manager.draw(screen)
        xtra_manager.draw(screen)
        
        for enemy in enemies:
            enemy.draw(screen)
            
        player.draw(screen)
        
        if show_help:
            draw_help_overlay(screen, width, height)

        pygame.display.flip()

    pygame.quit()
    sys.exit()

def draw_help_overlay(surface, width, height):
    # Dim background
    overlay = pygame.Surface((width, height), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180)) # Semi-transparent black
    surface.blit(overlay, (0, 0))
    
    # Text (Need default font)
    font = pygame.font.SysFont("Arial", 24)
    title_font = pygame.font.SysFont("Arial", 40, bold=True)
    
    lines = [
        ("LEVEL MAZE", title_font),
        ("Controls:", font),
        ("Movement: Left Stick / WASD", font),
        ("Look: Right Stick / Mouse", font),
        ("Dash: A Button / Space (Cooldown: 10s)", font),
        ("Roar: X Button / Shift (Cooldown: 30s)", font),
        ("", font),
        ("Rules:", font),
        ("Avoid Enemy contact (You take Damage!)", font),
        ("Collect Health Packs (+) to heal.", font),
        ("Kill Enemies for XP.", font),
        ("Find the Exit (Not Implemented Yet!)", font),
        ("", font),
        ("Press SELECT / TAB to Close", font)
    ]
    
    y = height // 3
    for text, fnt in lines:
        text_surf = fnt.render(text, True, (255, 255, 255))
        rect = text_surf.get_rect(center=(width // 2, y))
        surface.blit(text_surf, rect)
        y += 40

if __name__ == "__main__":
    main()
