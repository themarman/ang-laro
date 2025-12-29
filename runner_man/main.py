import pygame
import sys
from runner_man.player import Player
from runner_man.obstacle_manager import ObstacleManager

def main():
    pygame.init()
    
    # Constants
    WIDTH, HEIGHT = 800, 600
    FPS = 60
    
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Runner Man")
    clock = pygame.time.Clock()
    
    # Init Entities
    # Ground Y = 460 (Floor)
    # Player spawns at Y=400 (Top-left of 60px height rect)
    player = Player(100, 400)
    
    obstacle_manager = ObstacleManager(WIDTH, HEIGHT)
    
    running = True
    game_over = False
    font = pygame.font.SysFont("Arial", 30)
    
    score = 0.0
    
    inputs = {'left': False, 'right': False, 'jump': False}
    
    SCROLL_SPEED = 300.0

    while running:
        dt = clock.tick(FPS) / 1000.0
        
        # ... (Event Handling remains same) ...
        # Event Handling
        inputs['jump'] = False 
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_a: 
                    inputs['jump'] = True
                if event.key == pygame.K_u:
                    obstacle_manager.toggle()
                    print(f"Obstacles {'Enabled' if obstacle_manager.enabled else 'Disabled'}")
                if event.key == pygame.K_ESCAPE:
                    running = False
                # Restart on game over
                if game_over and event.key == pygame.K_r:
                    # Reset
                    player = Player(100, 400)
                    obstacle_manager = ObstacleManager(WIDTH, HEIGHT)
                    score = 0
                    game_over = False

            if event.type == pygame.JOYBUTTONDOWN:
                if event.button == 0: # A Button
                    inputs['jump'] = True
                    # Restart
                    if game_over:
                         player = Player(100, 400)
                         obstacle_manager = ObstacleManager(WIDTH, HEIGHT)
                         score = 0
                         game_over = False
        
        # Continuous Input (DPAD)
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]: inputs['left'] = True
        else: inputs['left'] = False
        
        if keys[pygame.K_RIGHT]: inputs['right'] = True
        else: inputs['right'] = False
        
        # Gamepad Hat
        if pygame.joystick.get_count() > 0:
            joy = pygame.joystick.Joystick(0)
            joy.init()
            hat = joy.get_hat(0)
            if hat[0] == -1: inputs['left'] = True
            elif hat[0] == 1: inputs['right'] = True
        
        # Update
        if not game_over:
            player.update(dt, inputs)
            
            # Constant Scroll Speed for Environment
            obstacle_manager.update(dt, SCROLL_SPEED)
            
            # Collision / Push Logic
            collided_obs = obstacle_manager.check_collision(player.rect)
            if collided_obs:
                # Push player back to the left of the obstacle
                player.rect.right = collided_obs['rect'].left
                
            # Game Over Check: Pushed off screen (Left)
            if player.rect.right < 0:
                print("Game Over! Pushed off screen.")
                game_over = True
                
            score += SCROLL_SPEED * dt / 100.0
        
        # Draw
        screen.fill((20, 20, 30)) # Dark Blue BG
        
        # Draw Ground Line
        pygame.draw.line(screen, (100, 200, 100), (0, 460), (WIDTH, 460), 5)
        
        player.draw(screen)
        obstacle_manager.draw(screen)
        
        # UI
        score_text = font.render(f"Distance: {int(score)}m", True, (255, 255, 255))
        screen.blit(score_text, (20, 20))
        
        if game_over:
            over_text = font.render("GAME OVER! Press A or R to Restart", True, (255, 50, 50))
            center = over_text.get_rect(center=(WIDTH//2, HEIGHT//2))
            screen.blit(over_text, center)
        
        pygame.display.flip()
        
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
