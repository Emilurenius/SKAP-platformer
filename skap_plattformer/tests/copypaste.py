"""
Platformer Game
"""
import arcade
import os

#More convenient way to find files
def path(path):
    return os.path.realpath(f"{__file__}/../../{path}")

# Constants
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 650
SCREEN_TITLE = "Platformer"

# Constants used to scale our sprites from their original size
CHARACTER_SCALING = 1
TILE_SCALING = 0.5
COIN_SCALING = 0.5
SPRITE_PIXEL_SIZE = 128
GRID_PIXEL_SIZE = SPRITE_PIXEL_SIZE * TILE_SCALING



GRAVITY = 1

# Movement speed of player, in pixels per frame
#Pixels per frame
PLAYER_WALK_SPEED = 8
PLAYER_JUMP_SPEED = 15
PLAYER_COMBO_JUMP_BOOST = 4
PLAYER_COMBO_JUMP_TIMER = 7
PLAYER_MAX_JUMP_COMBO = 2
JUMP_DIFFICULTY = 2

# Pixels per frame per frame
PLAYER_WALK_ACCELERATION = 1
PLAYER_SLOW_DOWN = 1

class MyGame(arcade.Window):
    """
    Main application class.
    """

    def __init__(self):

        # Call the parent class and set up the window
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)

        # Our TileMap Object
        self.tile_map = None

        # Our Scene Object
        self.scene = None

        # Separate variable that holds the player sprite
        self.player_sprite = None

        # Our physics engine
        self.physics_engine = None

        # A Camera that can be used for scrolling the screen
        self.camera = None

        # A Camera that can be used to draw GUI elements
        self.gui_camera = None

        # Keep track of the score
        self.score = 0

        # Load sounds
        self.collect_coin_sound = arcade.load_sound(":resources:sounds/coin1.wav")
        self.jump_sound = arcade.load_sound(":resources:sounds/jump1.wav")

        # Variables for control buttons
        self.left_pressed = False
        self.right_pressed = False
        self.up_pressed = False
        self.down_pressed = False

        arcade.set_background_color(arcade.csscolor.CORNFLOWER_BLUE)

    def setup(self):
        """Set up the game here. Call this function to restart the game."""

        # Setup the Cameras
        self.camera = arcade.Camera(self.width, self.height)
        self.gui_camera = arcade.Camera(self.width, self.height)

        # Name of map file to load
        map_name = "E:/Documents/GitHub/SKAP-platformer/skap_plattformer/assets/platform_level_01.tmx"

        # Layer specific options are defined based on Layer names in a dictionary
        # Doing this will make the SpriteList for the platforms layer
        # use spatial hashing for detection.
        layer_options = {
            "Platforms": {
                "use_spatial_hash": True,
            },
        }

        # Read in the tiled map
        self.tile_map = arcade.load_tilemap(map_name, TILE_SCALING, layer_options)

        # Initialize Scene with our TileMap, this will automatically add all layers
        # from the map as SpriteLists in the scene in the proper order.
        self.scene = arcade.Scene.from_tilemap(self.tile_map)

        # Keep track of the score
        self.score = 0

        # Set up the player, specifically placing it at these coordinates.
        image_source = path("assets/images/skapning-export.png")
        self.player_sprite = arcade.Sprite(image_source, CHARACTER_SCALING)
        self.player_sprite.center_x = 128
        self.player_sprite.center_y = 128
        self.player_sprite.newJump = True
        self.player_sprite.combo_jump_timer = 0
        self.player_sprite.combo_jumps = 0
        self.scene.add_sprite("Player", self.player_sprite)

        # --- Other stuff
        # Set the background color
        if self.tile_map.background_color:
            arcade.set_background_color(self.tile_map.background_color)

        # Create the 'physics engine'
        self.physics_engine = arcade.PhysicsEnginePlatformer(
            self.player_sprite, gravity_constant=GRAVITY, walls=self.scene["Ground"]
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


    def on_draw(self):
        """Render the screen."""

        # Clear the screen to the background color
        arcade.start_render()

        # Activate the game camera
        self.camera.use()

        # Draw our Scene
        self.scene.draw()
        #self.scene.draw_hit_boxes()

        # Activate the GUI camera before drawing GUI elements
        self.gui_camera.use()

        # Draw our score on the screen, scrolling it with the viewport
        score_text = f"Score: {self.score}"
        arcade.draw_text(
            score_text,
            10,
            10,
            arcade.csscolor.WHITE,
            18,
        )

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

    def center_camera_to_player(self):
        screen_center_x = self.player_sprite.center_x - (self.camera.viewport_width / 2)
        screen_center_y = self.player_sprite.center_y - (
            self.camera.viewport_height / 2
        )
        if screen_center_x < 0:
            screen_center_x = 0
        if screen_center_y < 0:
            screen_center_y = 0
        player_centered = screen_center_x, screen_center_y

        self.camera.move_to(player_centered)

    def on_update(self, delta_time):
        """Movement and game logic"""

        # Move the player with the physics engine
        self.player_move()
        self.physics_engine.update()

        # See if we hit any coins
        coin_hit_list = arcade.check_for_collision_with_list(
            self.player_sprite, self.scene["Coins"]
        )

        # Loop through each coin we hit (if any) and remove it
        for coin in coin_hit_list:
            # Remove the coin
            coin.remove_from_sprite_lists()
            # Play a sound
            arcade.play_sound(self.collect_coin_sound)
            # Add one to the score
            self.score += 1

        # Position the camera
        self.center_camera_to_player()


def main():
    """Main function"""
    window = MyGame()
    window.setup()
    arcade.run()


if __name__ == "__main__":
    main()