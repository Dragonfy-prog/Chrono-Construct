import pygame as py
from pygame.math import Vector2
import math
import json 
import random

turret_data = [
    {#1
        "range": 150,
        "cooldown": 1500,
    },
    {#2
        "range": 200,
        "cooldown": 1200,
    },
    {#3
        "range": 250,
        "cooldown": 900,
    },
    {#4
        "range": 300,
        "cooldown": 600,
    },
    {#5
        "range": 350,
        "cooldown": 300,
    }
]

ENEMY_DATA = {
        "weak": {
        "health": 100,
        "speed": 2,
        
    },
        "medium": {
        "health": 200,
        "speed": 5,
        
    },
        "strong": {
        "health": 400,
        "speed": 7,
        
    }
}

ENEMY_SPAWN_DATA = [
    {#1
        "weak" : 1,
        "medium" : 0,
        "strong" : 0
    },
    {#2
        "weak" : 30,
        "medium" : 0,
        "strong" : 0
    },
    {#3
        "weak" : 20,
        "medium" : 5,
        "strong" : 0
    },
    {#4
        "weak" : 5,
        "medium" : 15,
        "strong" : 0
    },
    {#5
        "weak" : 5,
        "medium" : 20,
        "strong" : 0
    },
    {#6
        "weak" : 0,
        "medium" : 20,
        "strong" : 5
    },
    {#7
        "weak" : 0,
        "medium" : 15,
        "strong" : 10
    },
    {#8
        "weak" : 0,
        "medium" : 10,
        "strong" : 15
    },
    {#9
        "weak" : 0,
        "medium" : 5,
        "strong" : 20
    },
    {#10
        "weak" : 0,
        "medium" : 0,
        "strong" : 25
    }
    
]

py.init()

#variables:
rows = 15
cols = 15
tile_size = 64
SIDE_PANEL = 300
SC_WIDTH = cols * tile_size
SC_HEIGHT = rows * tile_size
FPS = 120
HEALTH = 1
MONEY = 500
TOTAL_LEVELS = 10

#enemy variables
SPAWN_COOLDOWN = 500

#turret variables
buy_cost = 150
upgrade_cost = 300
kill_reward = 10
level_complete_reward = 200
turret_levels = 4
animation_steps = 8
animation_delay = 15
DAMAGE = 10

#the button class
class Button():
    def __init__(self, x, y, image, single_click):
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.clicked = False
        self.single_click = single_click

    def draw(self, surface):
        action = False
        #mouse position
        pos = py.mouse.get_pos()

        #mouseover and clicked conditions
        if self.rect.collidepoint(pos):
            if py.mouse.get_pressed()[0] == 1 and self.clicked == False:
                action = True
                #if bitton is single click then set to true
                if self.single_click:
                    self.clicked = True

        if py.mouse.get_pressed()[0] == 0:
            self.clicked = False
            
        #draw the button
        surface.blit(self.image, self.rect)

        return action

#the enemy class
class Enemy(py.sprite.Sprite):
    def __init__(self, enemy_type, waypoints, images):
        py.sprite.Sprite.__init__(self)
        self.og_image = images.get(enemy_type)
        self.angle = 0
        self.image = py.transform.rotate(self.og_image, self.angle)
        self.waypoints = waypoints
        self.rect = self.image.get_rect()
        self.rect.center = waypoints[0]
        self.pos = Vector2(self.waypoints[0])
        self.target_waypoint = 1
        self.speed = ENEMY_DATA.get(enemy_type)["speed"]
        self.health = ENEMY_DATA.get(enemy_type)["health"]
        self.killed_enemies = 0
        self.missed_enemies = 0
    
            
    def update(self, world):
        self.move(world)
        self.rotate()
        self.check_alive(world)
               
    def move(self, world):
        if self.target_waypoint >= len(self.waypoints):
            self.kill()
            world.health -= 1
            world.missed_enemies += 1
            return
        
        

        self.target = Vector2(self.waypoints[self.target_waypoint])
        self.movement = self.target - self.pos
        if self.movement.length() < self.speed:
            self.pos = self.target
            self.target_waypoint += 1
        else:
            self.pos += self.movement.normalize() *self.speed        

    def rotate(self):
        dist = self.target - self.pos
        self.angle = math.degrees(math.atan2(-dist[1], dist[0]))

        self.image = py.transform.rotate(self.og_image, self.angle)
        self.rect = self.image.get_rect()
        self.rect.center = self.pos
    def check_alive(self, world):
        if self.health <= 0:
            world.killed_enemies += 1
            world.money += kill_reward
            self.kill()
            
            

#the turret class
class Turret(py.sprite.Sprite):
    def __init__(self, sprite_sheets, tile_x, tile_y):
        py.sprite.Sprite.__init__(self)
        self.upgrade_level = 1
        self.range = turret_data[self.upgrade_level - 1].get("range")
        self.cooldown = turret_data[self.upgrade_level - 1].get("cooldown")
        self.last_shot = py.time.get_ticks()
        self.selected = False
        self.target = None

        #pos variables
        self.tile_size = tile_size
        self.tile_x = tile_x
        self.tile_y = tile_y
        #calculate the coorfinates of the center
        self.x = (self.tile_x + 0.5) * tile_size
        self.y = (self.tile_y + 0.5) * tile_size

        #animations
        self.sprite_sheets = sprite_sheets
        self.animation_list = self.load_images(self.sprite_sheets[self.upgrade_level - 1])
        self.frame_index = 0
        self.update_time = py.time.get_ticks()

        #update image
        self.angle = 90
        self.og_image = self.animation_list[self.frame_index]
        self.image = py.transform.rotate(self.og_image, self.angle)
        self.rect = self.image.get_rect()
        self.rect.center = (self.x, self.y)

        #create circle range
        self.range_image = py.Surface((self.range * 2, self.range * 2))
        self.range_image.fill((0, 0, 0,))
        self.range_image.set_colorkey((0, 0, 0))
        py.draw.circle(self.range_image, (255, 0, 0), (self.range, self.range), self.range)
        self.range_image.set_alpha(100)
        self.range_rect = self.range_image.get_rect()
        self.range_rect.center = self.rect.center

    def load_images(self, sprite_sheet):
        #extract images
        size = sprite_sheet.get_height()
        animation_list = []
        for x in range(animation_steps):
            temp_image = sprite_sheet.subsurface(x * size, 0, size, size)
            animation_list.append(temp_image)
        return animation_list
    
    def update(self, enemy_group):
        if self.target:
            x_distance = enemy.pos[0] - self.x
            y_distance = enemy.pos[1] - self.y
            distance = math.sqrt(x_distance ** 2 + y_distance ** 2)
            if distance > self.range or self.target.health <= 0:
                self.target = None
        if not self.target and py.time.get_ticks() - self.last_shot > self.cooldown:
            self.pick_target(enemy_group)
                
        #play animation for target selection
        if self.target:
            self.play_animation()
        else:
            if py.time.get_ticks() - self.last_shot > self.cooldown:         
                self.pick_target(enemy_group)

        if py.time.get_ticks() - self.last_shot > self.cooldown:
            self.play_animation()
            self.pick_target(enemy_group)
    
    def pick_target(self, enemy_group):
        #find an enemy for targeting
        x_distance = 0
        y_distance = 0
        #check distance to each enemey to see if they are in range
        for enemy in enemy_group:
            if enemy.health >= 0:
                x_distance = enemy.pos[0] - self.x
                y_distance = enemy.pos[1] - self.y
                distance = math.sqrt(x_distance ** 2 + y_distance ** 2)
                if distance < self.range:
                    self.target = enemy
                    self.angle = math.degrees(math.atan2(-y_distance, x_distance))
                    self.target.health -= DAMAGE
                    break
                

    def play_animation(self):
        #update image
        self.og_image = self.animation_list[self.frame_index]
        #check for time passed 
        if py.time.get_ticks() - self.update_time > animation_delay:
            self.update_time = py.time.get_ticks()
            self.frame_index += 1
            #check for animation finish
            if self.frame_index >= len(self.animation_list):
                self.frame_index = 0
                #reset the cooldown
                self.last_shot = py.time.get_ticks()
                self.target = None
    
    def upgrade(self):
        self.upgrade_level += 1
        self.range = turret_data[self.upgrade_level - 1].get("range")
        self.cooldown = turret_data[self.upgrade_level - 1].get("cooldown")
        #update the image
        self.animation_list = self.load_images(self.sprite_sheets[self.upgrade_level - 1])
        self.og_image = self.animation_list[self.frame_index]

        #upgrade range
        self.range_image = py.Surface((self.range * 2, self.range * 2))
        self.range_image.fill((0, 0, 0,))
        self.range_image.set_colorkey((0, 0, 0))
        py.draw.circle(self.range_image, (255, 0, 0), (self.range, self.range), self.range)
        self.range_image.set_alpha(100)
        self.range_rect = self.range_image.get_rect()
        self.range_rect.center = self.rect.center

    def draw(self, surface):
        self.image = py.transform.rotate(self.og_image, self.angle - 90)
        self.rect = self.image.get_rect()
        self.rect.center = (self.x, self.y)
        surface.blit(self.image, self.rect)
        if self.selected:
            surface.blit(self.range_image, self.range_rect)

   
#the world class
class World():
    def __init__(self, data, map_image):
        self.level = 1
        self.health = HEALTH
        self.money = MONEY
        self.tile_map = []
        self.waypoints = []
        self.level_data = data 
        self.image = map_image
        self.enemy_list = []
        self.spawned_enemies = 0
        self.killed_enemies = 0
        self.missed_enemies = 0


    def process_data(self):
        for layer in self.level_data["layers"]:
            if layer["name"] == "Tile Layer 1":
                self.tile_map = layer["data"]
            elif layer["name"] == "waypoints":
                for obj in layer["objects"]:
                    waypoints_data = obj["polyline"]
                    self.process_waypoints(waypoints_data, (obj["x"], obj["y"]))
    
    def process_waypoints(self, data, offset):
        for point in data:
            temp_x = point.get("x") + offset[0]
            temp_y = point.get("y") + offset[1]
            self.waypoints.append((temp_x, temp_y))
    
    def process_eneimes(self):
        enemies = ENEMY_SPAWN_DATA[self.level - 1]
        for enemy_type in enemies:
            eneimes_to_spawn = enemies[enemy_type]
            for enemy in range(eneimes_to_spawn):
                self.enemy_list.append(enemy_type)
        #randomize the enemy list
        random.shuffle(self.enemy_list)

    def check_level_complete(self):
        if (self.killed_enemies + self.missed_enemies) == len(self.enemy_list):
            return True

    def reset_level(self):
        #reset the enemy variables
        self.enemy_list = []
        self.killed_enemies = 0
        self.missed_enemies = 0
        self.spawned_enemies = 0
    
    def draw(self, surface):
        surface.blit(self.image, (0, 0))
    
        

#initialize the clock
clock = py.time.Clock()


#screen setup
screen = py.display.set_mode((SC_WIDTH + SIDE_PANEL, SC_HEIGHT))
py.display.set_caption("Chrono Construct")

#game variables
game_over = False
game_outcome = 0
level_started = False
last_enemy_spawn = py.time.get_ticks()
placing_turret = False
selected_turret = None

#images

#level map
map_image = py.image.load("assets/levels/tile_map_for_Chrono_construct.png").convert_alpha()
#turret spritesheet
turret_spritesheets = []
for x in range(1, turret_levels + 1):
    turret_sheet = py.image.load(f"assets/turrets/turret_{x}.png").convert_alpha()
    turret_spritesheets.append(turret_sheet)
#turret
turret_image = py.image.load("assets/turrets/turret.png").convert_alpha()
#enemies

enemy_image = py.image.load("assets/enemies/towerDefense_tilesheet - enemy.PNG").convert_alpha()
enemy_image = py.transform.scale(enemy_image, (100, 100))
enemy_image_2 = py.image.load("assets/enemies/enemy_2.png").convert_alpha()
enemy_image_2 = py.transform.scale(enemy_image_2, (100, 100))
enemy_image_3 = py.image.load("assets/enemies/enemy_3.png").convert_alpha()
enemy_image_3 = py.transform.scale(enemy_image_3, (100, 100))

enemy_images = { 
    "weak" : enemy_image,
    "medium" : enemy_image_2,
    "strong":  enemy_image_3,
}

#buttons
turret_buy_button = py.image.load("assets/buttons/buy_turret.png").convert_alpha()
cancel_button = py.image.load("assets/buttons/cancel.png").convert_alpha()
upgrade_button = py.image.load("assets/buttons/upgrade_turret.png").convert_alpha()
begin_button = py.image.load("assets/buttons/begin.png").convert_alpha()
restart_button = py.image.load("assets/buttons/restart.png").convert_alpha()

#load the level data
with open("assets/levels/tile_map_for_Chrono_construct..tmj") as file:
    world_data = json.load(file)

#fonts
text_font = py.font.SysFont("Times New Roman", 24, bold = True)
large_font = py.font.SysFont("Times New Roman", 36)
    
# output text on screen
def draw_text(text, font, text_col, x, y):
    img = font.render(text, True, text_col)
    screen.blit(img, (x, y))


def create_turret(mouse_postiton):
    mouse_tile_x = mouse_postiton[0]// tile_size
    mouse_tile_y = mouse_postiton[1]// tile_size
    #calculate the tile number
    mouse_tile_number = (mouse_tile_y * cols) + mouse_tile_x
    #to check if the tile is grass
    if world.tile_map[mouse_tile_number] == 232:
        #to check if there is not turret overlapping
        space_free = True
        for turret in turret_group:
            if (mouse_tile_x, mouse_tile_y) == (turret.tile_x, turret.tile_y):
                space_free = False
        #if there is free space, create a turret
        if space_free == True:

            turret = Turret(turret_spritesheets, mouse_tile_x, mouse_tile_y)
            turret_group.add(turret)
            #subtract the money
            world.money -= buy_cost

def select_turret(mouse_postiton):
    mouse_tile_x = mouse_postiton[0]// tile_size
    mouse_tile_y = mouse_postiton[1]// tile_size
    for turret in turret_group:
        if (mouse_tile_x, mouse_tile_y) == (turret.tile_x, turret.tile_y):
            return turret
        
def clear_selection():
    for turret in turret_group:
        turret.selected = False

#Create the world
world = World(world_data, map_image)
world.process_data()
world.process_eneimes()

#groups
enemy_group = py.sprite.Group()
turret_group = py.sprite.Group()



#creating the buttons
turret_button = Button(SC_WIDTH + 30, 120, turret_buy_button, True)
cancel_button = Button(SC_WIDTH + 50, 180, cancel_button, True)
upgrade_button = Button(SC_WIDTH + 5, 180, upgrade_button, True)
begin_button = Button(SC_WIDTH + 60, 300, begin_button, True)
restart_button = Button(310, 300, restart_button, True)

#event loop
run = True
while run:
    
    #set the frame rate
    clock.tick(FPS)

    if game_over == False:
        #check to see if the game is over
    
        if world.health <= 0:
            game_over = True
            game_outcome = -1
        #check if game is won
        if world.level > TOTAL_LEVELS:
            game_over = True
            game_outcome = 1

            
        #update the groups

        enemy_group.update(world) 
        turret_group.update(enemy_group)

        #highlight the selcted turret
        if selected_turret:
            selected_turret.selected = True
    

        #fill the screen with white
        screen.fill((255, 255, 255))

        #draw the world
        world.draw(screen)

        #draw the enemy
        enemy_group.draw(screen)

        #draw the turret
        for turret in turret_group:
            turret.draw(screen)

        #draw the text
        draw_text(str(world.health), text_font, (255, 255, 255), 0, 0)
        draw_text(str(world.money), text_font, (255, 255, 255), 0, 30)
        draw_text(str(world.level), text_font, (255, 255, 255), 0, 60)


     
        
        #check for begining of level
        if level_started == False:
            if begin_button.draw(screen):
                level_started = True
        else:
        #spawn enemies
            if py.time.get_ticks() - last_enemy_spawn > SPAWN_COOLDOWN:
                if world.spawned_enemies < len(world.enemy_list):
                    enemy_type = world.enemy_list[world.spawned_enemies]
                    enemy = Enemy(enemy_type, world.waypoints, enemy_images)
                    enemy_group.add(enemy)
                    world.spawned_enemies += 1
                    last_enemy_spawn = py.time.get_ticks()
        #check if wave is complete            
        if world.check_level_complete() == True:
            world.money += level_complete_reward
            world.level += 1
            level_started = False
            last_enemy_spawn = py.time.get_ticks()
            world.reset_level()
            world.process_eneimes()
        

        #draw the buttons
        #button for placing turret
        if turret_button.draw(screen):
            placing_turret = True
        #if placing turret then show cancel button
        if placing_turret == True:
            #show turret
            cursor_rect = turret_image.get_rect()
            cursor_postition = py.mouse.get_pos()
            cursor_rect.center = cursor_postition
            if cursor_postition[0] < SC_WIDTH:
                screen.blit(turret_image, cursor_rect)

            if cancel_button.draw(screen):
                placing_turret = False
        # upgrade button for turret
        if selected_turret:
            if selected_turret.upgrade_level < turret_levels:
                if upgrade_button.draw(screen):
                    if world.money >= upgrade_cost:
                        selected_turret.upgrade()
                        world.money -= upgrade_cost
    else:
        py.draw.rect(screen, (0, 0, 0), (200, 200, 400,200), border_radius = 30 )
        if game_outcome == -1:
            draw_text("GAME OVER", large_font, (255, 0, 0), 310, 230)
        elif game_outcome == 1:
            draw_text("YOU WON", large_font, (0, 255, 0), 315, 230)
            #restart level button
        if restart_button.draw(screen):
            game_over = False
            level_started = False
            placing_turret = False
            selected_turret = None
            last_enemy_spawn = py.time.get_ticks()
            world = World(world_data, map_image)
            world.process_data()
            world.process_eneimes()
            #empty the groups
            enemy_group.empty()
            turret_group.empty()

    



    
    #event handling
    for event in py.event.get():

        if event.type == py.QUIT:
            run = False
        #mouse click to place turret
        if event.type == py.MOUSEBUTTONDOWN and event.button == 1:
            mouse_postiton = py.mouse.get_pos()
            #to check if the mouse is over the map
            if mouse_postiton[0] < SC_WIDTH and mouse_postiton[1] < SC_HEIGHT:
                #clear the selection of turret
                selected_turret = None
                clear_selection()
                if placing_turret == True:
                    if world.money >= buy_cost:
                        create_turret(mouse_postiton)
                else:
                    selected_turret = select_turret(mouse_postiton)
        
        
    
    py.display.flip()
     

py.quit()