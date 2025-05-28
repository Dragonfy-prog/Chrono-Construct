import pygame as py
from pygame.math import Vector2
import math
import json 

py.init()

#variables:
rows = 15
cols = 15
tile_size = 64
SC_WIDTH = cols * tile_size
SC_HEIGHT = rows * tile_size
FPS = 120

#the turret class
class Turret(py.sprite.Sprite):
    def __init__(self, image, tile_x, tile_y):
        py.sprite.Sprite.__init__(self)
        self.tile_x = tile_x
        self.tile_y = tile_y
        #calculate the coorfinates of the center
        self.x = (self.tile_x + 0.5) * tile_size
        self.y = (self.tile_y + 0.5) * tile_size
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.center = (self.x, self.y)

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
   
#the world class
class World():
    def __init__(self, data, map_image):
        self.waypoints = []
        self.level_data = data 
        self.image = map_image

    def process_data(self):
        for layer in self.level_data["layers"]:
            if layer["name"] == "waypoints":
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
screen = py.display.set_mode((SC_WIDTH, SC_HEIGHT))
py.display.set_caption("Chrono Construct")

#images
#level map
map_image = py.image.load("assets/levels/tile_map_for_Chrono_construct.png").convert_alpha()
#turret
turret_image = py.image.load("assets/turrets/towerDefense_tilesheet - turret.PNG").convert_alpha()
#enemies
enemy_image = py.image.load("assets/enemies/towerDefense_tilesheet - enemy.PNG").convert_alpha()
enemy_image = py.transform.scale(enemy_image, (100, 100))

#load the level data
with open("assets/levels/tile_map_for_Chrono_construct..tmj") as file:
    world_data = json.load(file)

    
def create_turret(mouse_postition):
    mouse_tile_x = mouse_postiton[0]// tile_size
    mouse_tile_y = mouse_postiton[1]// tile_size
    turret = Turret(turret_image, mouse_tile_x, mouse_tile_y)
    turret_group.add(turret)

#Create the world
world = World(world_data, map_image)
world.process_data()

#groups
enemy_group = py.sprite.Group()
turret_group = py.sprite.Group()


#enemy initialization
enemy = Enemy(world.waypoints, enemy_image)
enemy_group.add(enemy)



#event loop
run = True
while run:
    
    #set the frame rate
    clock.tick(FPS)

    #update the enemy
    enemy_group.update() 

    #fill the screen with white
    screen.fill((255, 255, 255))

    #draw the world
    world.draw(screen)

    #draw the enemy
    enemy_group.draw(screen)

    #draw the turret
    turret_group.draw(screen)

    
    
    #event handling
    for event in py.event.get():

        if event.type == py.QUIT:
            run = False
        #mouse click to place turret
        if event.type == py.MOUSEBUTTONDOWN and event.button == 1:
            mouse_postiton = py.mouse.get_pos()
            #to check if the mouse is over the map
            if mouse_postiton[0] < SC_WIDTH and mouse_postiton[1] < SC_HEIGHT:
                create_turret(mouse_postiton)
        
        
    
    py.display.flip()
     

py.quit()