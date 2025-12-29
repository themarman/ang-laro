import pygame
import os

def fix_transparency():
    pygame.init()
    pygame.display.set_mode((1, 1)) # Init display for convert()
    
    path = "d:/Github/ang-laro/runner_man/assets/runner.png"
    
    try:
        # Load image
        image = pygame.image.load(path).convert()
        
        # Get background color from top-left
        bg_color = image.get_at((0, 0))
        print(f"Background Color detected: {bg_color}")
        
        # Create a new RGBA surface
        new_image = pygame.Surface(image.get_size(), pygame.SRCALPHA)
        
        # Set colorkey on original to hide background
        image.set_colorkey(bg_color)
        
        # Blit original (with colorkey applied) onto transparent surface
        new_image.blit(image, (0, 0))
        
        # Save back
        pygame.image.save(new_image, path)
        print("Successfully saved transparent image.")
        
    except Exception as e:
        print(f"Error: {e}")
        
    pygame.quit()

if __name__ == "__main__":
    fix_transparency()
