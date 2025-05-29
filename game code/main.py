import pygame as py
from pygame.math import Vector2
import math
import json 

py.init()

#variables:
rows = 15
cols = 15
tile_size = 64
SIDE_PANEL = 300
SC_WIDTH = cols * tile_size
SC_HEIGHT = rows * tile_size
FPS = 120

#turret variables
animation_steps = 8
animation_delay = 15

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
    def __init__(self, waypoints, image):
        py.sprite.Sprite.__init__(self)
        self.og_image = image
        self.angle = 0
        self.image = py.transform.rotate(self.og_image, self.angle)
        self.waypoints = waypoints
        self.rect = self.image.get_rect()
        self.rect.center = waypoints[0]
        self.pos = Vector2(self.waypoints[0])
        self.target_waypoint = 1
        self.speed = 2
            
    def update(self):
        self.move()
        self.rotate()
               
    def move(self):
        if self.target_waypoint >= len(self.waypoints):
            self.kill()
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

#the turret class
class Turret(py.sprite.Sprite):
    def __init__(self, sprite_sheet, tile_x, tile_y):
        py.sprite.Sprite.__init__(self)
        self.range = 100
        self.cooldown = 1500
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
        self.sprite_sheet = sprite_sheet
        self.animation_list = self.load_images()
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

    def load_images(self):
        #extract images
        size = self.sprite_sheet.get_height()
        animation_list = []
        for x in range(animation_steps):
            temp_image = self.sprite_sheet.subsurface(x * size, 0, size, size)
            animation_list.append(temp_image)
        return animation_list
    
    def update(self, enemy_group):
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
            x_distance = enemy.pos[0] - self.x
            y_distance = enemy.pos[1] - self.y
            distance = math.sqrt(x_distance ** 2 + y_distance ** 2)
            if distance > self.range:
                self.target = enemy
                self.angle = math.degrees(math.atan2(-y_distance, x_distance))
                

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
        self.tile_map = []
        self.waypoints = []
        self.level_data = data 
        self.image = map_image

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


    
    def draw(self, surface):
        surface.blit(self.image, (0, 0))
    
        

#initialize the clock
clock = py.time.Clock()


#screen setup
screen = py.display.set_mode((SC_WIDTH + SIDE_PANEL, SC_HEIGHT))
py.display.set_caption("Chrono Construct")

#game variables
placing_turret = False
selected_turret = None

#images

#level map
map_image = py.image.load("assets/levels/tile_map_for_Chrono_construct.png").convert_alpha()
#turret spritesheet
turret_sheet = py.image.load("assets/turrets/turret_1.png").convert_alpha()
#turret
turret_image = py.image.load("assets/turrets/turret.png").convert_alpha()
#enemies
enemy_image = py.image.load("assets/enemies/towerDefense_tilesheet - enemy.PNG").convert_alpha()
enemy_image = py.transform.scale(enemy_image, (100, 100))
#buttons
turret_buy_button = py.image.load("assets/buttons/buy_turret.png").convert_alpha()
cancel_button = py.image.load("assets/buttons/cancel.png").convert_alpha()
#load the level data
with open("assets/levels/tile_map_for_Chrono_construct..tmj") as file:
    world_data = json.load(file)

    
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

            turret = Turret(turret_sheet, mouse_tile_x, mouse_tile_y)
            turret_group.add(turret)
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

#groups
enemy_group = py.sprite.Group()
turret_group = py.sprite.Group()


#enemy initialization
enemy = Enemy(world.waypoints, enemy_image)
enemy_group.add(enemy)

#creating the buttons
turret_button = Button(SC_WIDTH + 30, 120, turret_buy_button, True)
cancel_button = Button(SC_WIDTH + 50, 180, cancel_button, True)
#event loop
run = True
while run:
    
    #set the frame rate
    clock.tick(FPS)

    #update the groups
    enemy_group.update() 
    turret_group.update(enemy_group)

    #hilight the selcted turret
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
                    create_turret(mouse_postiton)
                else:
                    selected_turret = select_turret(mouse_postiton)
        
        
    
    py.display.flip()
     

py.quit()