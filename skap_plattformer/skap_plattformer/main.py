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
SCREEN_HEIGHT = 800
SCREEN_TITLE = "Skap plattformer"
GRAVITY = 1

#Pixels per frame
PLAYER_WALK_SPEED = 8
PLAYER_JUMP_SPEED = 15
PLAYER_COMBO_JUMP_BOOST = 4
PLAYER_COMBO_JUMP_TIMER = 7
PLAYER_MAX_JUMP_COMBO = 2

# Pixels per frame per frame
PLAYER_WALK_ACCELERATION = 1
PLAYER_SLOW_DOWN = 1


JUMP_DIFFICULTY = 1


# sprite scaling
CHARACTER_SCALING = 1
TILE_SCALING = 1
COIN_SCALING = 0.5

# Constants for colors
BLUE = arcade.csscolor.CORNFLOWER_BLUE
WHITE = arcade.csscolor.WHITE


class MyGame(arcade.Window):
    # Main application class.

    def __init__(self):

        # Call the parent class and set up the window
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)

        # Scene object
        self.scene = None

        # Camera objects
        self.player_camera = None
        self.GUI_camera = None

        # separate variable for the player sprite
        self.player_sprite = None

        # Physics physics engine
        self.physics_engine = None
        
        # Timer
        self.total_time = 0.0

        # Score
        self.score = 0

        # Variables for control buttons
        self.left_pressed = False
        self.right_pressed = False
        self.up_pressed = False
        self.down_pressed = False

        # Set background color
        arcade.set_background_color(BLUE)

        # Load sounds
        self.collect_coin_sound = arcade.load_sound(":resources:sounds/coin1.wav")
        self.jump_sound = arcade.load_sound(":resources:sounds/jump1.wav")

        # Initialize tile map
        self.tile_map = None

    def setup(self):
        # Game setup happens here, and calling this function should restart the game
        
        # Initialize scene
        self.scene = arcade.Scene()

        # Create spritelists
        self.scene.add_sprite_list("Player")
        self.scene.add_sprite_list("Walls", use_spatial_hash = True)  # spatial hash makes collision detection faster at the cost of slower moving.
        self.scene.add_sprite_list("Coins", use_spatial_hash = True)
        self.collisionLists = "Walls"
        self.scene.add_sprite_list("Collision")

        # Set up player
        player_image = path("assets/images/skapning-export.png")
        self.player_sprite = arcade.Sprite(player_image, CHARACTER_SCALING)
        self.player_sprite.newJump = True
        self.player_sprite.combo_jump_timer = 0
        self.player_sprite.combo_jumps = 0
        self.score = 0
        
        # Place the player
        self.player_sprite.center_x = 96
        self.player_sprite.center_y = 128
        
        # Add the player to the spritelist
        self.scene.add_sprite("Player", self.player_sprite)

        # Create the Camera
        self.player_camera = arcade.Camera(self.width, self.height)
        self.GUI_camera = arcade.Camera(self.width, self.height)

        # Template for adding things to the level
        # CORRECTLIST should be wall if its stationary
        """
        objectName = arcade.Sprite(imageFile.png, ScalingFactor)
        objectName.center_x = horizontal coordinate
        objectName.center_y = vertical coordinate
        self.scene.add_sprite("CORRECTLIST", objectName)
        """

        # Name of map file to load
        map_name = path("assets/tiles/map.tmx")

        # Layer specific options are defined based on Layer names in a dictionary
        # Doing this will make the SpriteList for the platforms layer
        # use spatial hashing for detection.
        layer_options = {
            "Walls": {
                "use_spatial_hash": True,
            },
        }

        # Read in the tiled map
        self.tile_map = arcade.load_tilemap(map_name, TILE_SCALING, layer_options)

        # Initialize Scene with our TileMap, this will automatically add all layers
        # from the map as SpriteLists in the scene in the proper order.
        self.scene = arcade.Scene.from_tilemap(self.tile_map)

        # # Create the ground
        # # This shows using a loop to place multiple sprites horizontally
        # for x in range(0, 2500, 64):
        #     wall = arcade.Sprite(":resources:images/tiles/grassMid.png", TILE_SCALING)
        #     wall.center_x = x
        #     wall.center_y = 32
        #     self.scene.add_sprite("Walls", wall)

        # for y in range(0, 1250, 64):
        #     wall = arcade.Sprite(":resources:images/tiles/stoneCenter.png", TILE_SCALING)
        #     wall.center_y = y
        #     wall.center_x = 32
        #     self.scene.add_sprite("Walls", wall)

        # # Put some crates on the ground
        # # This shows using a coordinate list to place sprites
        # coordinate_list = [[512, 96], [256, 96], [768, 96]]

        # for coordinate in coordinate_list:
        #     # Add a crate on the ground
        #     wall = arcade.Sprite(
        #         ":resources:images/tiles/boxCrate_double.png", TILE_SCALING
        #     )
        #     wall.position = coordinate
        #     self.scene.add_sprite("Walls", wall)
        
        # # Add some coins
        # for x in range(128, 1250, 256):
        #     coin = arcade.Sprite(":resources:images/items/coinGold.png", COIN_SCALING)
        #     coin.center_x = x
        #     coin.center_y = 96
        #     self.scene.add_sprite("Coins", coin)

        # coin = arcade.Sprite(":resources:images/items/coinGold.png", COIN_SCALING)
        # coin.center_x = -128
        # coin.center_y = 32
        # self.scene.add_sprite("Coins", coin)

        # Create physics engine
        self.physics_engine = arcade.PhysicsEnginePlatformer(
            player_sprite = self.player_sprite, gravity_constant = GRAVITY, walls = self.scene["Walls"]
        )

        # Clock
        self.total_time = 0

    def on_draw(self):
        # Screen rendering (set entire screen to background color)
        arcade.start_render()

        # tell the game to use camera
        self.player_camera.use()

        # draw sprites
        self.scene.draw()

        # Draw GUI
        self.GUI_camera.use()

        # Draw the score counter
        arcade.draw_text (
            self.score_text,
            10,
            SCREEN_HEIGHT - 50,
            WHITE,
            18
        )

        # Draw the timer
        arcade.draw_text (
            self.clock_text,
            SCREEN_WIDTH - 100,
            SCREEN_HEIGHT - 50,
            WHITE,
            18
        )
    
    def player_move(self):

        #Jump mechanics
        if self.physics_engine.can_jump():

            #Decrement combo timer while you're on the ground
            self.player_sprite.combo_jump_timer -= 1
            
            if self.player_sprite.newJump:
                if self.up_pressed and not self.down_pressed:
                    """
                    Jump mechanics:
                    If JUMP_DIFFICULTY is 0, you can constantly jump by holding its key

                    If its 1 You have to let go and repress, to jump the moment you touch ground

                    If its 2 you have to let go and repress WHILE you're on ground, to jump.
                    """

                    if self.physics_engine.can_jump():
                        if JUMP_DIFFICULTY == 1:
                            self.player_sprite.newJump = False

                        if self.player_sprite.combo_jump_timer > 0:
                            self.physics_engine.jump(PLAYER_JUMP_SPEED+PLAYER_COMBO_JUMP_BOOST*self.player_sprite.combo_jumps)
                            arcade.play_sound(self.jump_sound)
                        else:
                            self.player_sprite.combo_jumps = 0
                            self.physics_engine.jump(PLAYER_JUMP_SPEED)
                            arcade.play_sound(self.jump_sound)

                        self.player_sprite.combo_jumps += 1
                        if self.player_sprite.combo_jumps > PLAYER_MAX_JUMP_COMBO:
                            self.player_sprite.combo_jumps = PLAYER_MAX_JUMP_COMBO

                        self.player_sprite.combo_jump_timer = PLAYER_COMBO_JUMP_TIMER

        if not self.up_pressed:
            self.player_sprite.newJump = True
        
        elif JUMP_DIFFICULTY == 2: #only gets checked if self.up_pressed is true
            self.player_sprite.newJump = False

        #Walking mechanics
        if self.left_pressed and not self.right_pressed:
            if self.player_sprite.change_x != -PLAYER_WALK_SPEED:
                if self.player_sprite.change_x > -PLAYER_WALK_SPEED+PLAYER_WALK_ACCELERATION:
                    self.player_sprite.change_x -= PLAYER_WALK_ACCELERATION
                else:
                    self.player_sprite.change_x = -PLAYER_WALK_SPEED


        elif self.right_pressed and not self.left_pressed:
            if self.player_sprite.change_x != PLAYER_WALK_SPEED:
                if self.player_sprite.change_x < PLAYER_WALK_SPEED-PLAYER_WALK_ACCELERATION:
                    self.player_sprite.change_x += 2
                else:
                    self.player_sprite.change_x = PLAYER_WALK_SPEED

        if not self.right_pressed and not self.left_pressed or self.right_pressed and self.left_pressed: 
            if self.player_sprite.change_x != 0:
                if self.player_sprite.change_x > 0:
                    self.player_sprite.change_x -= PLAYER_SLOW_DOWN
                    if self.player_sprite.change_x < 0: 
                        self.player_sprite.change_x = 0
                else:
                    self.player_sprite.change_x += PLAYER_SLOW_DOWN
                    if self.player_sprite.change_x > 0: 
                        self.player_sprite.change_x = 0

    def on_update(self, delta_time):
        #This should be called 60 times per second

        #Handle picking up coins
        if True:
            coin_hit_list = arcade.check_for_collision_with_list(self.player_sprite, self.scene["Coins"])
            for coin in coin_hit_list:
                # Remove the coin, play a sound, increase score by 1.
                coin.remove_from_sprite_lists()
                arcade.play_sound(self.collect_coin_sound)
                self.score += 1

        self.score_text = f"Score: {self.score}, there are {self.scene['Coins'].index(self.scene['Coins'][-1])} remaining"
        
        #Keep track of time
        self.total_time += delta_time
        minutes = int(self.total_time)//60
        seconds = int(self.total_time)%60
        milliseconds = int((self.total_time-seconds)*100)
        self.clock_text = f"{minutes}:{seconds}:{milliseconds}"
        
        
        
        
        self.player_move()     
        self.physics_engine.update()
        self.center_camera_on_player()

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
        if key == arcade.key.ESCAPE:
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
        
    def center_camera_on_player(self):
        screen_center_x = self.player_sprite.center_x - (self.player_camera.viewport_width / 2)
        screen_center_y = self.player_sprite.center_y - (self.player_camera.viewport_height / 2)

        #Stop it from scrolling past 0
        if screen_center_x < 0:
            screen_center_x = 0
        if screen_center_y < 0:
           screen_center_y = 0

        player_centered = screen_center_x, screen_center_y

        self.player_camera.move_to(player_centered)

def main():
    #Main function
    window = MyGame()
    window.setup()
    arcade.run()

if __name__ == "__main__":
    main()