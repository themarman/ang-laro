import pygame
import sys

def inspect_and_fix():
    pygame.init()
    pygame.display.set_mode((1, 1))
    
    path = "d:/Github/ang-laro/runner_man/assets/runner.png"
    
    try:
        # Load image (preserve existing alpha if any, though likely opaque)
        image = pygame.image.load(path).convert()
        width, height = image.get_size()
        
        # Sample 4 corners to find consensus on background color
        corners = [
            image.get_at((0, 0)),
            image.get_at((width-1, 0)),
            image.get_at((0, height-1)),
            image.get_at((width-1, height-1))
        ]
        
        print(f"Corner colors: {corners}")
        
        # Force White Background Assumption based on User feedback and likely grid lines at (0,0)
        bg_color = pygame.Color(255, 255, 255, 255)
        print(f"Forcing Background Color: {bg_color}")

        # Create new RGBA surface
        new_image = pygame.Surface((width, height), pygame.SRCALPHA)
        new_image.fill((0,0,0,0)) # Transparent start
        
        # Manual pixel iteration to handle tolerance (artifacts)
        # Lock surfaces for speed
        # This is slower but deterministic for artifacts
        # Tolerance for JPEG/Compression artifacts: +/- 40 (Aggressive)
        tol = 60 # Increased tolerance for 'white-ish' pixels
        
        for y in range(height):
            for x in range(width):
                c = image.get_at((x, y))
                # Check distance to bg_color
                dist = abs(c.r - bg_color.r) + abs(c.g - bg_color.g) + abs(c.b - bg_color.b)
                
                if dist < tol:
                    # Transparent
                    new_image.set_at((x, y), (0, 0, 0, 0))
                else:
                    # Keep Pixel (Solid)
                    new_image.set_at((x, y), (c.r, c.g, c.b, 255))
        
        # Save fixed image
        pygame.image.save(new_image, path)
        print(f"Fixed image saved to {path} with background removed.")
        
    except Exception as e:
        print(f"Error: {e}")
        
    pygame.quit()

if __name__ == "__main__":
    inspect_and_fix()
