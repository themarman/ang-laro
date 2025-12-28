import pygame
import sys
import os

# Initialize Pygame
pygame.init()
pygame.joystick.init()

print(f"Pygame Version: {pygame.version.ver}")
print(f"SDL Version: {pygame.get_sdl_version()}")

joystick_count = pygame.joystick.get_count()
print(f"Number of joysticks detected: {joystick_count}")

if joystick_count == 0:
    print("No joysticks found.")
    sys.exit()

# Initialize joysticks
joysticks = []
for i in range(joystick_count):
    joystick = pygame.joystick.Joystick(i)
    joystick.init()
    print(f"Joystick {i}: {joystick.get_name()}")
    print(f"  GUID: {joystick.get_guid()}")
    print(f"  Axes: {joystick.get_numaxes()}")
    print(f"  Buttons: {joystick.get_numbuttons()}")
    print(f"  Hats: {joystick.get_numhats()}")
    joysticks.append(joystick)

print("\nListening for input... Press Ctrl+C to exit.")

# Event Loop
running = True
clock = pygame.time.Clock()

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.JOYAXISMOTION:
            if abs(event.value) > 0.1: # Filter noise
                print(f"Axis Motion: Joy {event.joy}, Axis {event.axis}, Value {event.value:.2f}")
        elif event.type == pygame.JOYBUTTONDOWN:
            print(f"Button Down: Joy {event.joy}, Button {event.button}")
        elif event.type == pygame.JOYBUTTONUP:
            print(f"Button Up: Joy {event.joy}, Button {event.button}")
        elif event.type == pygame.JOYHATMOTION:
            print(f"Hat Motion: Joy {event.joy}, Hat {event.hat}, Value {event.value}")

    clock.tick(60)

pygame.quit()
