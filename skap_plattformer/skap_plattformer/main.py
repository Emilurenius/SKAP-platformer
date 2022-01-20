#Skap platforming game

#importing modules and libraries as needed
import arcade
import os

from arcade.key import F

#More convenient way to find files
def path(path):
    return os.path.realpath(f"{__file__}/../../{path}")

# Initialize constant variables
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 500
SCREEN_TITLE = "Skap plattformer"
GRAVITY = 1
PLAYER_WALK_SPEED = 8  #in pixels per frame
PLAYER_JUMP_SPEED = 15
JUMP_DIFFICULTY = 2


# sprite scaling
CHARACTER_SCALING = 1
TILE_SCALING = 0.5

# Constants for colors
BLUE = arcade.csscolor.CORNFLOWER_BLUE

class MyGame(arcade.Window):
    #Main application class.

    def __init__(self):

        #Call the parent class and set up the window
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)

        #Scene object
        self.scene = None

        #separate variable for the player sprite
        self.player_sprite = None

        # Physics physics engine
        self.physics_engine = None
        
        #Variables for control buttons
        self.left_pressed = False
        self.right_pressed = False
        self.up_pressed = False
        self.down_pressed = False

        #Set background color
        arcade.set_background_color(BLUE)

    def setup(self):
        #Game setup happens here, and calling this function should restart the game
        
        #Initialize scene
        self.scene = arcade.Scene()

        #Create spritelists
        self.scene.add_sprite_list("Player")
        self.scene.add_sprite_list("Walls", use_spatial_hash = True) #spatial hash makes collition detection faster at the cost of slower moving.
        
        #Set up player
        

        playerImage = path("assets/images/skapning-export.png")
        self.player_sprite = arcade.Sprite(playerImage, CHARACTER_SCALING)
        
        #Place the player
        self.player_sprite.center_x = 64
        self.player_sprite.center_y = 128
        self.newJump = True
        
        #Add the player to the spritelist
        self.scene.add_sprite("Player", self.player_sprite)

        # Create the ground
        # This shows using a loop to place multiple sprites horizontally
        for x in range(0, 1250, 64):
            wall = arcade.Sprite(":resources:images/tiles/grassMid.png", TILE_SCALING)
            wall.center_x = x
            wall.center_y = 32
            self.scene.add_sprite("Walls", wall)


        # Put some crates on the ground
        # This shows using a coordinate list to place sprites
        coordinate_list = [[512, 96], [256, 96], [768, 96]]

        for coordinate in coordinate_list:
            # Add a crate on the ground
            wall = arcade.Sprite(
                ":resources:images/tiles/boxCrate_double.png", TILE_SCALING
            )
            wall.position = coordinate
            self.scene.add_sprite("Walls", wall)
        
        #Create physics engine
        self.physics_engine = arcade.PhysicsEnginePlatformer(
            player_sprite = self.player_sprite, gravity_constant = GRAVITY, walls = self.scene["Walls"]
        )

    def on_draw(self):
        #Screen rendering (set entire screen to background color)
        arcade.start_render()

        #draw sprites
        self.scene.draw()

    def player_move(self):

        if self.up_pressed and not self.down_pressed:
            
            if self.newJump:

                """
                Jump mechanics:
                If JUMP_DIFFICULTY is 0, you can constantly jump by holding its key

                If its 1 You have to let go and repress, to jump the moment you touch ground

                If its 2 you have to let go and repress WHILE you're on ground, to jump.
                """

                if JUMP_DIFFICULTY == 2:
                    self.newJump = False
                if self.physics_engine.can_jump():
                    if JUMP_DIFFICULTY == 1:
                        self.newJump = False
                    self.physics_engine.jump(PLAYER_JUMP_SPEED)
        
        else:
            self.newJump = True
                

        if self.left_pressed and not self.right_pressed:
            if self.player_sprite.change_x != -PLAYER_WALK_SPEED:
                if self.player_sprite.change_x > -PLAYER_WALK_SPEED+2:
                    self.player_sprite.change_x -= 2
                else:
                    self.player_sprite.change_x = -PLAYER_WALK_SPEED


        elif self.right_pressed and not self.left_pressed:
            if self.player_sprite.change_x != PLAYER_WALK_SPEED:
                if self.player_sprite.change_x < PLAYER_WALK_SPEED-2:
                    self.player_sprite.change_x += 2
                else:
                    self.player_sprite.change_x = PLAYER_WALK_SPEED

        if not self.right_pressed and not self.left_pressed or self.right_pressed and self.left_pressed: 
            if self.player_sprite.change_x != 0:
                if self.player_sprite.change_x > 0:
                    self.player_sprite.change_x -= 1
                    if self.player_sprite.change_x < 0: 
                        self.player_sprite.change_x = 0
                else:
                    self.player_sprite.change_x += 1
                    if self.player_sprite.change_x > 0: 
                        self.player_sprite.change_x = 0


    def on_update(self, delta_time):
        #This should be called 60 times per second

        self.player_move()     
        self.physics_engine.update()
           
        


    def on_key_press(self, key, modifiers):
        #Called when a key is pressed 
        
        if key == arcade.key.UP or key == arcade.key.W:
            self.up_pressed = True
        if key == arcade.key.LEFT or key == arcade.key.A:
            self.left_pressed = True
        if key == arcade.key.DOWN or key == arcade.key.S:
            self.down_pressed = True
        if key == arcade.key.RIGHT or key == arcade.key.D:
            self.right_pressed = True
        if key == arcade.key.ESC:
            self.setup()

    def on_key_release(self, key, modifiers):
        #Called when a key is released

        if key == arcade.key.UP or key == arcade.key.W:
            self.up_pressed = False
        if key == arcade.key.LEFT or key == arcade.key.A:
            self.left_pressed = False
        if key == arcade.key.DOWN or key == arcade.key.S:
            self.down_pressed = False
        if key == arcade.key.RIGHT or key == arcade.key.D:
            self.right_pressed = False
        

def main():
    #Main function
    window = MyGame()
    window.setup()
    arcade.run()

if __name__ == "__main__":
    main()