import os
import sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import pygame
import random
import math
import numpy as np
pygame.init()

file_base = "./assets/sunhacks_"

screen_width = 1200
screen_height = 700
fullscreen = False
screen = pygame.display.set_mode((screen_width, screen_height), pygame.RESIZABLE | pygame.SCALED)
pygame.display.set_caption("MATCH/DODGE")
center_screen = pygame.Vector2(screen_width/2, screen_height/2)

clock = pygame.time.Clock()
running = True
dt = 0

gridSize = 2
player_radius = 40
enemy_radius = 20
enemy_position = (screen_width/8, screen_height/8)
enemy_hit = False
enemy_can_move = False
square_width = 200
flashing_square_index = -1
flashed_squares_sequence = []
touched_squares_sequence = []
already_touching_square = False
touched_square_index = -1

level_count = 1
score = 0
level_ongoing = False
game_ended = False

current_text = ""
font_file = file_base + "font.ttf"
START_GAME = pygame.USEREVENT
START_LEVEL = pygame.USEREVENT + 1
SQUARE_FLASH_BEGIN = pygame.USEREVENT + 2
SQUARE_FLASH_END = pygame.USEREVENT + 3
SCORE_LEVEL = pygame.USEREVENT + 4
END_LEVEL = pygame.USEREVENT + 5
END_GAME = pygame.USEREVENT + 6
START_GAME_2 = pygame.USEREVENT + 7
START_GAME_3 = pygame.USEREVENT + 8

colors = {"background":(0, 0, 0), "button_text":(255, 255, 255), "text":(255, 255, 255), "text_stroke":(0, 0, 0)}
text_sizes = {"button":40, "main":74}
times = {"game_start":1000, "level_start":800, "flash_length":600}

speed = 500
enemy_speed = 200

class Player(pygame.sprite.Sprite):
    def __init__(self, radius):
        super().__init__()
        self.image = pygame.image.load(file_base + "player.png").convert_alpha()
        self.image = pygame.transform.scale(self.image, (radius * 2, radius * 2))
        self.rect = self.image.get_rect(center=center_screen)
        self.radius = radius
        self.mask = pygame.mask.from_surface(self.image)
    
    def update(self):
        if not game_ended:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_w] or keys[pygame.K_UP]:
                self.rect.y -= speed * dt
            if keys[pygame.K_s] or keys[pygame.K_DOWN]:
                self.rect.y += speed * dt
            if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                self.rect.x -= speed * dt
            if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                self.rect.x += speed * dt

class Square(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, count):
        super().__init__()
        self.image = pygame.image.load(file_base + "square.png").convert_alpha()
        self.image = pygame.transform.scale(self.image, (width, height))

        self.cracked_image = pygame.image.load(file_base + "cracked_square.png").convert_alpha()
        self.cracked_image = pygame.transform.scale(self.cracked_image, (width, height))

        self.rect = self.image.get_rect(topleft=(x, y))
        self.x = x
        self.y = y
        self.count = count
        self.mask = pygame.mask.from_surface(self.image)

        image_array = pygame.surfarray.array3d(self.image).astype(np.float32)
        image_array *= 0.6
        image_array = np.clip(image_array, 0, 255).astype(np.uint8)
        reduced_brightness_image = pygame.surfarray.make_surface(image_array)
        self.touched_image = reduced_brightness_image.convert_alpha()

        image_array = pygame.surfarray.array3d(self.image).astype(np.float32)
        image_array *= 3.0
        image_array = np.clip(image_array, 0, 255).astype(np.uint8)
        reduced_brightness_image = pygame.surfarray.make_surface(image_array)
        self.flashing_image = reduced_brightness_image.convert_alpha()

        image_array = pygame.surfarray.array3d(self.image).astype(np.float32)
        image_array *= 3.0 * 0.6
        image_array = np.clip(image_array, 0, 255).astype(np.uint8)
        reduced_brightness_image = pygame.surfarray.make_surface(image_array)
        self.flashing_touched_image = reduced_brightness_image.convert_alpha()

        self.image = pygame.transform.scale(self.image, (width, height))
        self.touched_image = pygame.transform.scale(self.touched_image, (width, height))

    def update(self):
        if self.count == touched_square_index and game_ended and not enemy_can_move:
            self.image = self.cracked_image
        elif self.count == flashing_square_index and self.count == touched_square_index:
            self.image = self.flashing_touched_image
        elif self.count == flashing_square_index:
            self.image = self.flashing_image
        elif self.count == touched_square_index:
            self.image = self.touched_image
        else:
            self.image = pygame.image.load(file_base + "square.png").convert_alpha()

class Button(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, text, text_color):
        self.image = pygame.image.load(file_base + "button.png").convert_alpha()
        
        image_array = pygame.surfarray.array3d(self.image).astype(np.float32)
        image_array *= 0.6
        image_array = np.clip(image_array, 0, 255).astype(np.uint8)
        reduced_brightness_image = pygame.surfarray.make_surface(image_array)
        self.hover_image = reduced_brightness_image.convert_alpha()

        self.image = pygame.transform.scale(self.image, (width, height))
        self.hover_image = pygame.transform.scale(self.hover_image, (width, height))

        self.rect = self.image.get_rect(topleft=(x, y))

        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.text_color = text_color
        self.visible = True
    
    def draw(self, screen):
        if self.visible:
            mouse_pos = pygame.mouse.get_pos()
            if self.rect.collidepoint(mouse_pos):
                screen.blit(self.hover_image, self.rect)
            else:
                 screen.blit(self.image, self.rect)
            
            text_surface = pygame.font.Font(font_file, text_sizes["button"]).render(self.text, True, self.text_color)
            text_rect = text_surface.get_rect(center=self.rect.center)
            

            text_stroke_surface = pygame.font.Font(font_file, text_sizes["button"]).render(self.text, True, colors["text_stroke"])
            text_stroke_rect = text_stroke_surface.get_rect(center=tuple(a + b for a, b in zip(self.rect.center, (2, 2))))
            screen.blit(text_stroke_surface, text_stroke_rect)
            screen.blit(text_surface, text_rect)
    
    def is_clicked(self):
        if self.visible:
            mouse_pos = pygame.mouse.get_pos()
            mouse_click = pygame.mouse.get_pressed()
            if self.rect.collidepoint(mouse_pos) and mouse_click[0]:
                return True
            return False

class Enemy(pygame.sprite.Sprite):
    def __init__(self, radius):
        super().__init__()
        self.image = pygame.image.load(file_base + "enemy.png").convert_alpha()
        self.image = pygame.transform.scale(self.image, (radius * 2, radius * 2))
        self.rect = self.image.get_rect(center=enemy_position)
        self.radius = radius
        self.mask = pygame.mask.from_surface(self.image)
    
    def update(self):
            x_distance = ((player_sprite.rect.x+player_radius) - (self.rect.x+self.radius)) 
            y_distance = ((player_sprite.rect.y+player_radius) - (self.rect.y+self.radius)) 
            distance_norm = math.sqrt(x_distance**2 + y_distance**2)
            if distance_norm and (level_ongoing or enemy_can_move):
                self.rect.x += (x_distance/distance_norm) * (enemy_speed + level_count * 5) * dt 
                self.rect.y += (y_distance/distance_norm) * (enemy_speed + level_count * 5) * dt

all_sprites = pygame.sprite.Group()

square_sprites = pygame.sprite.Group()
count = 0
for i in range(gridSize):
    for j in range(gridSize):  
        horizontal_position = (((screen_width - (gridSize * square_width)) // (gridSize + 1)) + square_width) * i + ((screen_width - (gridSize * square_width)) // (gridSize + 1))
        vertical_position = (((screen_height - (gridSize * square_width)) // (gridSize + 1)) + square_width) * j + ((screen_height - (gridSize * square_width)) // (gridSize + 1))
        rectangle_sprite = Square(horizontal_position, vertical_position, square_width, square_width, count)
        square_sprites.add(rectangle_sprite)
        all_sprites.add(rectangle_sprite)
        count += 1

player_sprite = Player(player_radius)
all_sprites.add(player_sprite)

enemy_sprite = Enemy(enemy_radius)
all_sprites.add(enemy_sprite)

button_size = [200, 60]
button_position = center_screen + (-1 * button_size[0]/2, 80)
button = Button(button_position[0], button_position[1], button_size[0], button_size[1], "BEGIN", colors["button_text"])

def render_text(text, color, size):
    font = pygame.font.Font(font_file, size)
    text_surface = font.render(text, True, color)
    return text_surface

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == START_GAME:
            pygame.time.set_timer(START_GAME, 0)
            pygame.time.set_timer(START_GAME_2, times["game_start"])
            flashed_squares_sequence = []
            game_ended = False
            enemy_can_move = False
            enemy_hit = False
            current_text = "MATCH"
        if event.type == START_GAME_2:
            pygame.time.set_timer(START_GAME_2, 0)
            pygame.time.set_timer(START_GAME_3, times["game_start"])
            current_text = "DODGE"
        if event.type == START_GAME_3:
            pygame.time.set_timer(START_GAME_3, 0)
            pygame.time.set_timer(START_LEVEL, times["game_start"])
            current_text = "START"
        if event.type == START_LEVEL:
            current_text = str(level_count)
            pygame.time.set_timer(START_LEVEL, 0)
            pygame.time.set_timer(SQUARE_FLASH_BEGIN, times["level_start"])
            flashed_squares_count = 0
            touched_squares_sequence = []
            level_ongoing = True
            random_square_index = random.randint(0, gridSize**2-1)
            flashed_squares_sequence.append(random_square_index)
        if event.type == SQUARE_FLASH_BEGIN:
            flashed_squares_count += 1
            if level_count == flashed_squares_count:
                flashing_square_index = random_square_index
            else:
                flashing_square_index = flashed_squares_sequence[flashed_squares_count-1]
            pygame.time.set_timer(SQUARE_FLASH_END, times["flash_length"])
            if flashed_squares_count == level_count:
                pygame.time.set_timer(SQUARE_FLASH_BEGIN, 0)
        if event.type == SQUARE_FLASH_END:
            flashing_square_index = -1
            pygame.time.set_timer(SQUARE_FLASH_END, 0)
        if event.type == SCORE_LEVEL:
            if touched_squares_sequence == flashed_squares_sequence and len(touched_squares_sequence) > 0:
                score += level_count
                pygame.event.post(pygame.event.Event(END_LEVEL))
            else:
                game_ended = True
                if flashed_squares_sequence and touched_squares_sequence:
                    for i in range(min(len(touched_squares_sequence), len(flashed_squares_sequence))):
                        if touched_squares_sequence[i] == flashed_squares_sequence[i]:
                            score += 1
                pygame.time.set_timer(SQUARE_FLASH_BEGIN, 0)
                pygame.event.clear()
                pygame.event.post(pygame.event.Event(END_GAME))
        if event.type == END_LEVEL:
            level_count +=1
            pygame.event.post(pygame.event.Event(START_LEVEL))
        if event.type == END_GAME:
            current_text = "SCORE " + str(score)
            button.text = "TRY AGAIN?"
            button.visible = True
            level_count = 1
            score = 0     
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_f:
                fullscreen = not fullscreen
                if fullscreen:
                    screen = pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN | pygame.SCALED)
                else:
                     screen = pygame.display.set_mode((screen_width, screen_height), pygame.SCALED)   
            if event.key == pygame.K_r and level_ongoing:
                pygame.event.post(pygame.event.Event(SCORE_LEVEL))
            if event.key == pygame.K_q or event.key == pygame.K_ESCAPE:
                pygame.event.post(pygame.event.Event(pygame.QUIT))
                      
            
    all_sprites.update()
    screen.fill(colors["background"])
    all_sprites.draw(screen)

    button.draw(screen)
    if button.is_clicked():
        pygame.event.post(pygame.event.Event(START_GAME))
        button.visible = False
        player_sprite.rect = player_sprite.image.get_rect(center=center_screen)
        enemy_sprite.rect = enemy_sprite.image.get_rect(center=enemy_position)
    
    touching_a_square = False
    for square_sprite in square_sprites:
        touching_current_square = pygame.sprite.collide_mask(player_sprite, square_sprite)
        if touching_current_square:
            touching_a_square = True
            if not already_touching_square:
                touched_square_index = square_sprite.count     
                touched_squares_sequence.append(square_sprite.count)
                if not game_ended and level_ongoing:
                    if touched_square_index != flashed_squares_sequence[len(touched_squares_sequence)-1]:
                        game_ended = True
                        level_ongoing = False
                        pygame.event.post(pygame.event.Event(SCORE_LEVEL))
            already_touching_square = True
    if not touching_a_square:
        already_touching_square = False
        touched_square_index = -1
    if len(touched_squares_sequence) == level_count and level_ongoing and not game_ended:
        level_ongoing = False
        pygame.event.post(pygame.event.Event(SCORE_LEVEL))
    if pygame.sprite.collide_mask(player_sprite, enemy_sprite) and not enemy_hit:
        enemy_hit = True
        level_ongoing = False
        game_ended = True
        enemy_can_move = True
        pygame.event.post(pygame.event.Event(SCORE_LEVEL))

    text_surface = render_text(current_text, colors["text"], text_sizes["main"])
    text_stroke_surface = render_text(current_text, colors["text_stroke"], text_sizes["main"]) 
    text_rect = text_surface.get_rect(center=center_screen + (0, -100))
    text_stroke_rect = text_stroke_surface.get_rect(center=center_screen + (0, -100) + (3, 3))
    screen.blit(text_stroke_surface, text_stroke_rect)
    screen.blit(text_surface, text_rect)

    pygame.display.flip()

    dt = clock.tick(60) / 1000

pygame.quit()
