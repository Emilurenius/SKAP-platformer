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
GRAVITY = 1.5

# Player start position
PLAYER_START_Y = 100
PLAYER_START_X = 100

#Pixels per frame
PLAYER_WALK_SPEED = 8
PLAYER_CLIMB_SPEED = 6
PLAYER_JUMP_SPEED = 15
PLAYER_FLOATY_JUMP_TIME = 15
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
TIMER_FROM_RIGHT = 41


# region sprite scaling
CHARACTER_SCALING = 1
TILE_SCALING = 0.5
COIN_SCALING = 0.5
SPRITE_PIXEL_SIZE = 256
GRID_PIXEL_SIZE = SPRITE_PIXEL_SIZE * TILE_SCALING
# endregion

# Constants for colors
BLUE = arcade.csscolor.CORNFLOWER_BLUE
WHITE = arcade.csscolor.WHITE

class MyGame(arcade.Window):
    # Main application class.

    def __init__(self):

        # Call the parent class and set up the window
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        
        # Initialize tile map
        self.tile_map = None
        self.end_of_map = 0
        self.friction = 0

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
        self.real_timer_from_right = 60
        
        # Load sounds
        self.collect_coin_sound = arcade.load_sound(":resources:sounds/coin1.wav")
        self.jump_sound = arcade.load_sound(":resources:sounds/phaseJump1.wav")
        self.big_jump_sound = arcade.load_sound(":resources:sounds/jump3.wav")
        self.land_sound = arcade.load_sound(":resources:sounds/rockHit2.ogg")

        # Set background color
        arcade.set_background_color(BLUE)

        # variables relating to the player
        self.player = None
        self.left_pressed = False
        self.right_pressed = False
        self.up_pressed = False
        self.down_pressed = False
        self.followPlayer = True

    def setup(self):
        # Game setup happens here, and calling this function should restart the game
        
        # Create the Camera
        self.player_camera = arcade.Camera(self.width, self.height)
        self.GUI_camera = arcade.Camera(self.width, self.height)

        #Name of map file to load
        map_name = path("assets/levels/secretTestLevel.tmx")

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

        # region Set up player
        image_source = path("assets/images/Players/stand_still.png")
        self.player = arcade.Sprite(image_source, CHARACTER_SCALING, hit_box_algorithm='Simple')
        self.player.newJump = True

        self.player.floating = False
        self.player.floaty_jump_timer = 0
        self.player.on_ladder = False
        self.player.on_ground = False
        self.followPlayer = True
        
        # Place the player
        self.player.center_x = PLAYER_START_X
        self.player.center_y = PLAYER_START_Y
        
        # Add the player to the spritelist
        self.scene.add_sprite("Player", self.player)
        # endregion

        #region enemy
        self.enemy = arcade.Sprite(image_source, CHARACTER_SCALING, hit_box_algorithm='Simple')
        self.scene.add_sprite('Enemy', self.player)
        #endregion

        # Create physics engine
        self.physics_engine = arcade.PhysicsEnginePlatformer(
            player_sprite = self.player, gravity_constant = 0, walls = [self.scene["Ground"], self.scene["Ice"]]
        )
        self.friction = 1

        # Clock
        self.total_time = 0

    def on_draw(self):
        # Screen rendering (set entire screen to background color)
        arcade.start_render()

        # tell the game to use camera
        self.player_camera.use()

        # draw sprites
        self.scene.draw()
        # self.scene.draw_hit_boxes()
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
            SCREEN_WIDTH - self.real_timer_from_right,
            SCREEN_HEIGHT - TIMER_FROM_TOP,
            WHITE,
            18
        )

        arcade.draw_text (
            f":{self.milliseconds}",
            SCREEN_WIDTH - TIMER_FROM_RIGHT,
            SCREEN_HEIGHT - TIMER_FROM_TOP,
            WHITE,
            18
        )
    
    def player_move(self):
        
        # region Useful variables for movement
        self.player.on_ground = self.physics_engine.can_jump()

        # endregion

        # region Jump mechanics
        if self.player.on_ground and not self.player.on_ladder:

            
            if self.player.newJump:
                if self.up_pressed and not self.down_pressed:
                    self.player.floaty_jump_timer = 0
                    self.player.floating = True
                    """
                    Jump mechanics:
                    If JUMP_DIFFICULTY is 0, you can constantly jump by holding its key

                    If its 1 You have to let go and repress, to jump the moment you touch ground

                    If its 2 you have to let go and repress WHILE you're on ground, to jump.
                    """

                    if self.physics_engine.can_jump():
                        if JUMP_DIFFICULTY == 1:
                            self.player.newJump = False
                    
                        self.physics_engine.jump(PLAYER_JUMP_SPEED)
                        arcade.play_sound(self.jump_sound)
        
        if self.player.on_ladder:
            if self.up_pressed and not self.down_pressed:
                self.player.change_y = PLAYER_CLIMB_SPEED
            elif self.down_pressed and not self.up_pressed:
                self.player.change_y = -PLAYER_CLIMB_SPEED


        # Gravity
        if not self.player.on_ground:
            if self.player.floating:
                if self.player.floaty_jump_timer > PLAYER_FLOATY_JUMP_TIME or not self.up_pressed:
                    self.player.floating = False
                    if self.player.on_ladder:
                        if self.player.change_y != 0:
                            if self.player.change_y > 0:
                                self.player.change_y -= 2
                                if self.player.change_y < 0: 
                                    self.player.change_y = 0
                            else:
                                self.player.change_y += 2
                                if self.player.change_y > 0: 
                                    self.player.change_y = 0
                    else:
                        self.player.change_y -= GRAVITY
                        self.friction = 1
                else:
                    self.player.floaty_jump_timer += 1
            
            else:
                self.player.change_y -= GRAVITY

        if not self.up_pressed:
            self.player.newJump = True
        
        elif JUMP_DIFFICULTY == 2: #only gets checked if self.up_pressed is true
            self.player.newJump = False
        # endregion

        # region Walking mechanics
        # Walk Left
        if self.left_pressed and not self.right_pressed:
            if self.player.change_x != -PLAYER_WALK_SPEED:
                if self.player.change_x > -PLAYER_WALK_SPEED+PLAYER_WALK_ACCELERATION:
                    self.player.change_x -= PLAYER_WALK_ACCELERATION
                else:
                    self.player.change_x = -PLAYER_WALK_SPEED

        # Walk Right
        elif self.right_pressed and not self.left_pressed:
            if self.player.change_x != PLAYER_WALK_SPEED:
                if self.player.change_x < PLAYER_WALK_SPEED-PLAYER_WALK_ACCELERATION:
                    self.player.change_x += PLAYER_WALK_ACCELERATION
                else:
                    self.player.change_x = PLAYER_WALK_SPEED

        # No walk
        if not self.right_pressed and not self.left_pressed or self.right_pressed and self.left_pressed:
            
            ground_hit_list = arcade.get_sprites_at_point(
                [self.player.center_x, self.player.bottom-5], self.scene["Ground"]
            )

            ice_hit_list = arcade.get_sprites_at_point(
                [self.player.center_x, self.player.bottom-5], self.scene["Ice"]
            )

            if ground_hit_list:
                self.friction = 1

            elif ice_hit_list:
                self.friction = 0.1

            if self.player.change_x != 0:
                if self.player.change_x > 0:
                    self.player.change_x -= self.friction
                    if self.player.change_x < 0: 
                        self.player.change_x = 0
                else:
                    self.player.change_x += self.friction
                    if self.player.change_x > 0: 
                        self.player.change_x = 0
        # endregion

    def on_update(self, delta_time):
        #This should be called 60 times per second
        
        self.physics_engine.update()
        
        # Check if player fell off the map
        if self.player.center_y < -100:
            self.player.center_y = PLAYER_START_Y
            self.player.center_x = PLAYER_START_X
            self.followPlayer = True

        # region Check for misc collisions
        
        # Coins
        coin_hit_list = arcade.check_for_collision_with_list(
            self.player, self.scene["Coins"]
        )

        # Ladder
        ladder_hit_list = arcade.check_for_collision_with_list(
            self.player, self.scene["Ladder"]
        )

        # Coins
        goal_hit_list = arcade.check_for_collision_with_list(
            self.player, self.scene["Goal"]
        )

        if ladder_hit_list:
            self.player.on_ladder = True
        else:
            self.player.on_ladder = False

        if goal_hit_list:
            print('Player touching goal!')
            self.followPlayer = False

        # endregion

        # Loop through each coin we hit (if any) and remove it
        for coin in coin_hit_list:
            # Remove the coin
            coin.remove_from_sprite_lists()
            # Play a sound
            #arcade.play_sound(self.collect_coin_sound)
            arcade.play_sound(self.land_sound)
            # Add one to the score
            self.score += coin.properties["coin_value"]

        self.score_text = f"Score: {int(self.score)}, there are {len(self.scene['Coins'])} remaining"
        
        #Keep track of time
        self.real_timer_from_right = TIMER_FROM_RIGHT
        self.total_time += delta_time
        minutes = int(self.total_time)//60
        seconds = int(self.total_time)%60
        self.milliseconds = int((self.total_time - seconds - minutes*60)*100//1)
        self.clock_text = f"{minutes}:{seconds}"
        x = 1
        self.real_timer_from_right += 7
        while x < len(self.clock_text):
            self.real_timer_from_right += 14
            x += 1
        #Move the player
        self.player_move()


        # Move the camera 
        if self.followPlayer:
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
        screen_center_x = self.player.center_x - (self.player_camera.viewport_width / 2)
        screen_center_y = self.player.center_y - (self.player_camera.viewport_height / 2)

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