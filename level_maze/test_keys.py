import pygame

pygame.init()

keys_to_test = ["space", "lshift", "return", "a", "left shift", "right shift"]

for k in keys_to_test:
    try:
        code = pygame.key.key_code(k)
        print(f"Key '{k}': {code} (OK)")
    except Exception as e:
        print(f"Key '{k}': FAILED ({e})")
