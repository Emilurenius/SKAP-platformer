#Skap platforming game

#importing modules and libraries as needed
import arcade
import os


#More convenient way to find files
def path(path):
    return os.path.realpath(f"{__file__}/../../{path}")

# Initialize constant variables
SCREEN_WIDTH = 1800
SCREEN_HEIGHT = 880
SCREEN_TITLE = "Skap plattformer"
GRAVITY = 1

# Player start position
PLAYER_START_Y = 100
PLAYER_START_X = 100

#Pixels per frame
PLAYER_WALK_SPEED = 8
PLAYER_JUMP_SPEED = 15
PLAYER_COMBO_JUMP_BOOST = 2
PLAYER_COMBO_JUMP_TIMER = 7
PLAYER_MAX_JUMP_COMBO = 2

# Pixels per frame per frame
PLAYER_WALK_ACCELERATION = 1
PLAYER_SLOW_DOWN = 1

JUMP_DIFFICULTY = 1

# Placement of GUI
# Scoreboard
SCORE_FROM_TOP = 25
SCORE_FROM_LEFT = 10

# Timer
TIMER_FROM_TOP = 25
TIMER_FROM_RIGHT = 80


# sprite scaling
CHARACTER_SCALING = 1
TILE_SCALING = 0.5
COIN_SCALING = 0.5
SPRITE_PIXEL_SIZE = 256
GRID_PIXEL_SIZE = SPRITE_PIXEL_SIZE * TILE_SCALING

# Constants for colors
BLUE = arcade.csscolor.CORNFLOWER_BLUE
WHITE = arcade.csscolor.WHITE

# Layer names for from tilemap
LAYER_NAME_PLATFORMS = "Platforms"
LAYER_NAME_COINS = "Coins"
LAYER_NAME_FOREGROUND = "Foreground"
LAYER_NAME_BACKGROUND = "Background"
LAYER_NAME_DANGER = "Danger"



class MyGame(arcade.Window):
    # Main application class.

    def __init__(self):

        # Call the parent class and set up the window
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        
        # Initialize tile map
        self.tile_map = None
        self.end_of_map = 0

        # Level
        self.level = 1
        
        # Scene object
        self.scene = None

        # Physics engine
        self.physics_engine = None

        # Camera objects
        self.player_camera = None
        self.GUI_camera = None

        # Score
        self.score = 0

        # Timer
        self.total_time = 0.0
        
        # Load sounds
        self.collect_coin_sound = arcade.load_sound(":resources:sounds/coin1.wav")
        self.jump_sound = arcade.load_sound(":resources:sounds/phaseJump1.wav")
        self.big_jump_sound = arcade.load_sound(":resources:sounds/jump3.wav")
        self.land_sound = arcade.load_sound(":resources:sounds/rockHit2.ogg")

        
        # Set background color
        arcade.set_background_color(BLUE)

        # variables relating to the player
        self.player_sprite = None
        self.left_pressed = False
        self.right_pressed = False
        self.up_pressed = False
        self.down_pressed = False

    def setup(self):
        # Game setup happens here, and calling this function should restart the game
        
        # Create the Camera
        self.player_camera = arcade.Camera(self.width, self.height)
        self.GUI_camera = arcade.Camera(self.width, self.height)

        #Name of map file to load
        map_name = path("assets/platform_level_01.tmx")

        # Layer specific options are defined based on Layer names in a dictionary
        # Doing this will make the SpriteList for the platforms layer
        # use spatial hashing for detection.
        layer_options = {
            "Ground": {
                "use_spatial_hash": True,
            },
        }

        # Read in the tiled map
        self.tile_map = arcade.load_tilemap(map_name, TILE_SCALING, layer_options)

        # Initialize Scene with our TileMap, this will automatically add all layers
        # from the map as SpriteLists in the scene in the proper order.
        self.scene = arcade.Scene.from_tilemap(self.tile_map)
        self.end_of_map = self.tile_map.width * GRID_PIXEL_SIZE

        self.score = 0

        # Set up player
        image_source = path("assets/images/skapning-export.png")
        self.player_sprite = arcade.Sprite(image_source, CHARACTER_SCALING)
        self.player_sprite.newJump = True
        self.player_sprite.combo_jump_timer = 0
        self.player_sprite.combo_jumps = 0
        self.player_sprite.inAir = False
        self.player_sprite.onLadder = False
        
        

        # Place the player
        self.player_sprite.center_x = PLAYER_START_X
        self.player_sprite.center_y = PLAYER_START_Y
        
        # Add the player to the spritelist
        self.scene.add_sprite("Player", self.player_sprite)

        # Create physics engine
        self.physics_engine = arcade.PhysicsEnginePlatformer(
            player_sprite = self.player_sprite, gravity_constant = 0, walls = [self.scene["Ground"], self.scene["Ice"]]
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
        #self.scene.draw_hit_boxes()
        # Draw GUI
        self.GUI_camera.use()

        # Draw the score counter
        arcade.draw_text (
            self.score_text,
            SCORE_FROM_LEFT,
            SCREEN_HEIGHT - SCORE_FROM_TOP,
            WHITE,
            18
        )

        # Draw the timer
        arcade.draw_text (
            self.clock_text,
            SCREEN_WIDTH - TIMER_FROM_RIGHT,
            SCREEN_HEIGHT - TIMER_FROM_TOP,
            WHITE,
            18
        )
    
    def player_move(self):
        
        # region Useful variables for movement
        ground = []
        ground.append(arcade.get_sprites_at_point(
            [self.player_sprite.bottom],
        ))


        # region Jump mechanics
        if self.physics_engine.can_jump():
            
            self.player_sprite.inAir = False

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
                            if self.player_sprite.combo_jumps < 2:
                                self.physics_engine.jump(PLAYER_JUMP_SPEED+PLAYER_COMBO_JUMP_BOOST*self.player_sprite.combo_jumps)
                                arcade.play_sound(self.jump_sound)
                            else:
                                arcade.play_sound(self.big_jump_sound)
                                self.physics_engine.jump(PLAYER_JUMP_SPEED+PLAYER_COMBO_JUMP_BOOST*self.player_sprite.combo_jumps+5)
                        else:
                            self.player_sprite.combo_jumps = 0
                            self.physics_engine.jump(PLAYER_JUMP_SPEED)
                            arcade.play_sound(self.jump_sound)

                        self.player_sprite.combo_jumps += 1
                        if self.player_sprite.combo_jumps > PLAYER_MAX_JUMP_COMBO:
                            self.player_sprite.combo_jumps = PLAYER_MAX_JUMP_COMBO

                        self.player_sprite.combo_jump_timer = PLAYER_COMBO_JUMP_TIMER
        else:
            self.player_sprite.inAir = True
        if not self.up_pressed:
            self.player_sprite.newJump = True
        
        elif JUMP_DIFFICULTY == 2: #only gets checked if self.up_pressed is true
            self.player_sprite.newJump = False
        # endregion

        # region Walking mechanics
        if self.left_pressed and not self.right_pressed:
            if self.player_sprite.change_x != -PLAYER_WALK_SPEED:
                if self.player_sprite.change_x > -PLAYER_WALK_SPEED+PLAYER_WALK_ACCELERATION:
                    self.player_sprite.change_x -= PLAYER_WALK_ACCELERATION
                else:
                    self.player_sprite.change_x = -PLAYER_WALK_SPEED

        elif self.right_pressed and not self.left_pressed:
            if self.player_sprite.change_x != PLAYER_WALK_SPEED:
                if self.player_sprite.change_x < PLAYER_WALK_SPEED-PLAYER_WALK_ACCELERATION:
                    self.player_sprite.change_x += PLAYER_WALK_ACCELERATION
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
        # endregion

    def on_update(self, delta_time):
        #This should be called 60 times per second

             
        self.physics_engine.update()
        
        # Check if player fell off the map
        if self.player_sprite.center_y < -100:
            self.player_sprite.center_y = PLAYER_START_Y
            self.player_sprite.center_x = PLAYER_START_X


        # region Check for misc collisions
        
        # Coins
        coin_hit_list = arcade.check_for_collision_with_list(
            self.player_sprite, self.scene["Coins"]
        )

        # Ladder



        # endregion

        # Loop through each coin we hit (if any) and remove it
        for coin in coin_hit_list:
            # Remove the coin
            coin.remove_from_sprite_lists()
            # Play a sound
            arcade.play_sound(self.collect_coin_sound)
            # Add one to the score
            self.score += coin.properties["coin_value"]

        self.score_text = f"Score: {int(self.score)}, there are some remaining"
        
        #Keep track of time
        self.total_time += delta_time
        minutes = int(self.total_time)//60
        seconds = int(self.total_time)%60
        milliseconds = int((self.total_time-seconds)*100)
        self.clock_text = f"{minutes}:{seconds}:{milliseconds}"

        #Move the player
        self.player_move()

        # Move the camera 
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