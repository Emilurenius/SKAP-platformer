# Skap platforming game

# importing modules and libraries as needed
import arcade
import os
import math
from typing import Optional


# More convenient way to find files
from skap_plattformer.tests.copypaste import PLAYER_MAX_JUMP_COMBO, PLAYER_COMBO_JUMP_BOOST


def path(file_address):
    return os.path.realpath(f"{__file__}/../../{file_address}")


"""
Example of Pymunk Physics Engine Platformer
"""

SCREEN_TITLE = "PyMunk Platformer"

# How big are our image tiles?
GRID_PIXEL_SIZE = 128

# Scale sprites up or down
SPRITE_SCALING_PLAYER = 0.5
SPRITE_SCALING_TILES = 0.5

# Scaled sprite size for tiles
SPRITE_SIZE = int(GRID_PIXEL_SIZE * SPRITE_SCALING_PLAYER)

# Size of grid to show on screen, in number of tiles
SCREEN_GRID_WIDTH = 25
SCREEN_GRID_HEIGHT = 15

# Size of screen to show, in pixels
SCREEN_WIDTH = SPRITE_SIZE * SCREEN_GRID_WIDTH
SCREEN_HEIGHT = SPRITE_SIZE * SCREEN_GRID_HEIGHT

# GUI placements
TIMER_FROM_RIGHT = 100
TIMER_FROM_TOP = 20
SCORE_FROM_LEFT = 20
SCORE_FROM_TOP = 20

# Constants for color
WHITE = arcade.color.WHITE

# --- Physics forces. Higher number, faster accelerating.

# Gravity
GRAVITY = 1500

# Damping - Amount of speed lost per second
DEFAULT_DAMPING = 1.0
PLAYER_DAMPING = 0.5

# Friction between objects
PLAYER_FRICTION = 1.0
WALL_FRICTION = 0.7
DYNAMIC_ITEM_FRICTION = 0.6

# Mass (defaults to 1)
PLAYER_MASS = 2.0

# Player constants
PLAYER_MAX_HORIZONTAL_SPEED = 450
PLAYER_MAX_VERTICAL_SPEED = 1600
PLAYER_MAX_CLIMB_SPEED = 50
PLAYER_MOVE_FORCE_ON_GROUND = 8000
PLAYER_MOVE_FORCE_IN_AIR = 2000
PLAYER_CLIMB_FORCE = 2000
PLAYER_JUMP_FORCE = 1000
PLAYER_MAX_JUMP_COMBO = 2
PLAYER_COMBO_JUMP_BOOST = 150
PLAYER_COMBO_JUMP_TIMER = 9
PLAYER_CLIMB_SPEED = 10

class MyGame(arcade.Window):
    """ Main Window """

    def __init__(self, width, height, title):
        """ Create the variables """

        # Init the parent class
        super().__init__(width, height, title)

        # Init the tile map
        self.tile_map = None
        self.end_of_map = None
        self.friction = None

        # Level
        self.level = 1

        # Scene object
        self.scene = None

        # Physics engine
        self.physics_engine = None

        # Cameras
        self.player_camera = None
        self.gui_camera = None

        # Score
        self.score = 0
        self.score_text = ""

        # Timer
        self.total_time = 0.0
        self.real_timer_from_right = 60
        self.clock_text = ""
        self.minutes = 0
        self.seconds = 0
        self.milliseconds = 0

        # Load sounds
        self.collect_coin_sound = arcade.load_sound(":resources:sounds/coin1.wav")
        self.jump_sound = arcade.load_sound(":resources:sounds/phaseJump1.wav")
        self.big_jump_sound = arcade.load_sound(":resources:sounds/jump3.wav")
        self.land_sound = arcade.load_sound(":resources:sounds/rockHit2.ogg")

        # Set background color
        arcade.set_background_color(arcade.color.AMAZON)

        # Sprite lists we need
        self.player_list = None
        self.wall_list = None
        self.bullet_list = None
        self.item_list = None
        self.coin_list = None
        self.ice_list = None

        # Track the current state of what key is pressed
        self.left_pressed: bool = False
        self.right_pressed: bool = False
        self.up_pressed: bool = False
        self.down_pressed: bool = False

        self.player = None
        self.damping = 0
        self.gravity = 0

    def setup(self):
        """ Set up everything with the game """

        # Create Camera
        self.player_camera = arcade.Camera(self.width, self.height)
        self.gui_camera = arcade.Camera(self.width, self.height)

        # Map name
        map_name = "assets/levels/secretTestLevel.tmx"

        # Load in TileMap
        self.tile_map = arcade.load_tilemap(path(map_name), SPRITE_SCALING_TILES)

        self.scene = arcade.Scene.from_tilemap(self.tile_map)
        self.end_of_map = self.tile_map.width * GRID_PIXEL_SIZE

        self.score = 0

        # Create the missing sprite lists
        self.player_list = arcade.SpriteList()
        self.bullet_list = arcade.SpriteList()

        layers = ["BackgroundTile", "Ground", "Ice", "Ladder", "DecorationBehindPlayer", "Player", "DynamicItem",
                  "Item", "Coin", "Platform", "DecorationInFrontPlayer"]
        if "BackgroundTile" not in self.scene.name_mapping:
            self.scene.add_sprite_list("BackgroundTile")

        previous_layer = "BackgroundTile"
        for name in layers:
            if name not in self.scene.name_mapping:
                self.scene.add_sprite_list_after(name, previous_layer)
                previous_layer = name

        # region Set up player
        image_source = path("assets/images/skapning-export.png")
        self.player = arcade.Sprite(image_source, 1, hit_box_algorithm='Simple')
        self.scene.add_sprite_list_before("Player", "DecorationInFrontPlayer")
        self.scene.add_sprite("Player", self.player)
        self.player.newJump = True
        self.player.combo_jump_timer = 0
        self.player.combo_jumps = 0
        self.player.on_ladder = False
        self.player.on_ground = False

        grid_x = 3
        grid_y = 3
        self.player.center_x = SPRITE_SIZE * grid_x + SPRITE_SIZE / 2
        self.player.center_y = SPRITE_SIZE * grid_y + SPRITE_SIZE / 2
        # Add to player sprite list
        self.player_list.append(self.player)

        # --- Pymunk Physics Engine Setup ---

        # The default damping for every object controls the percent of velocity
        # the object will keep each second. A value of 1.0 is no speed loss,
        # 0.9 is 10% per second, 0.1 is 90% per second.
        # For top-down games, this is basically the friction for moving objects.
        # For platformers with gravity, this should probably be set to 1.0.
        # Default value is 1.0 if not specified.
        self.damping = DEFAULT_DAMPING

        # Set the gravity. (0, 0) is good for outer space and top-down.
        self.gravity = (0, -GRAVITY)

        # Create the physics engine
        self.physics_engine = arcade.PymunkPhysicsEngine(damping=self.damping,
                                                         gravity=self.gravity)

        # Add the player.
        # For the player, we set the damping to a lower value, which increases
        # the damping rate. This prevents the character from traveling too far
        # after the player lets off the movement keys.
        # Setting the moment to PymunkPhysicsEngine.MOMENT_INF prevents it from
        # rotating.
        # Friction normally goes between 0 (no friction) and 1.0 (high friction)
        # Friction is between two objects in contact. It is important to remember
        # in top-down games that friction moving along the 'floor' is controlled
        # by damping.
        self.physics_engine.add_sprite(self.player,
                                       friction=PLAYER_FRICTION,
                                       mass=PLAYER_MASS,
                                       moment=arcade.PymunkPhysicsEngine.MOMENT_INF,
                                       collision_type="player",
                                       max_horizontal_velocity=PLAYER_MAX_HORIZONTAL_SPEED,
                                       max_vertical_velocity=PLAYER_MAX_VERTICAL_SPEED)

        # Create the walls.
        # By setting the body type to PymunkPhysicsEngine.STATIC the walls can't
        # move.
        # Movable objects that respond to forces are PymunkPhysicsEngine.DYNAMIC
        # PymunkPhysicsEngine.KINEMATIC objects will move, but are assumed to be
        # repositioned by code and don't respond to physics forces.
        # Dynamic is default.
        self.physics_engine.add_sprite_list(self.scene["Ground"],
                                            friction=WALL_FRICTION,
                                            collision_type="wall",
                                            body_type=arcade.PymunkPhysicsEngine.STATIC)

        # Create the items
        self.physics_engine.add_sprite_list(self.scene["Item"],
                                            friction=DYNAMIC_ITEM_FRICTION,
                                            collision_type="item")

    def on_key_press(self, key, modifiers):
        """Called whenever a key is pressed. """

        if key == arcade.key.LEFT or key == arcade.key.A:
            self.left_pressed = True
        elif key == arcade.key.RIGHT or key == arcade.key.D:
            self.right_pressed = True
        elif key == arcade.key.UP or key == arcade.key.W:
            self.up_pressed = True
        elif key == arcade.key.DOWN or key == arcade.key.S:
            self.down_pressed = True

    def on_key_release(self, key, modifiers):
        """Called when the user releases a key. """

        if key == arcade.key.LEFT or key == arcade.key.A:
            self.left_pressed = False
        elif key == arcade.key.RIGHT or key == arcade.key.D:
            self.right_pressed = False
        elif key == arcade.key.UP or key == arcade.key.W:
            self.up_pressed = False
        elif key == arcade.key.DOWN or key == arcade.key.S:
            self.down_pressed = False

    def on_update(self, delta_time):
        """ Movement and game logic """

        # region Player Left/Right
        self.player.on_ground = self.physics_engine.is_on_ground(self.player)
        # Update player forces based on keys pressed
        if self.left_pressed and not self.right_pressed:
            # Create a force to the left. Apply it.
            if self.player.on_ground:
                force = (-PLAYER_MOVE_FORCE_ON_GROUND, 0)
            else:
                force = (-PLAYER_MOVE_FORCE_IN_AIR, 0)
            self.physics_engine.apply_force(self.player, force)
            # Set friction to zero for the player while moving
            self.physics_engine.set_friction(self.player, 0)
        elif self.right_pressed and not self.left_pressed:
            # Create a force to the right. Apply it.
            if self.player.on_ground:
                force = (PLAYER_MOVE_FORCE_ON_GROUND, 0)
            else:
                force = (PLAYER_MOVE_FORCE_IN_AIR, 0)
            self.physics_engine.apply_force(self.player, force)
            # Set friction to zero for the player while moving
            self.physics_engine.set_friction(self.player, 0)
        else:
            # Player's feet are not moving. Therefore, up the friction so we stop.
            self.physics_engine.set_friction(self.player, 1.0)
        # endregion

        # region Jump mechanics
        if self.player.on_ground and not self.player.on_ladder:

            # Decrement combo timer while you're on the ground
            self.player.combo_jump_timer -= 1

            if self.player.newJump:
                if self.up_pressed and not self.down_pressed:
                    """
                    Jump mechanics:
                    If JUMP_DIFFICULTY is 0, you can constantly jump by holding its key

                    If its 1 You have to let go and repress, to jump the moment you touch ground

                    If its 2 you have to let go and repress WHILE you're on ground, to jump.
                    """

                    if self.player.on_ground:
                        self.player.newJump = False

                        if self.player.combo_jump_timer > 0:
                            if self.player.combo_jumps < 2:
                                self.physics_engine.apply_impulse(
                                    self.player, [0, PLAYER_JUMP_FORCE + PLAYER_COMBO_JUMP_BOOST * self.player.combo_jumps])
                                arcade.play_sound(self.jump_sound)
                            else:
                                arcade.play_sound(self.big_jump_sound)
                                self.physics_engine.apply_impulse(
                                    self.player, [0, PLAYER_JUMP_FORCE + PLAYER_COMBO_JUMP_BOOST * self.player.combo_jumps + 500])
                        else:
                            self.player.combo_jumps = 0
                            self.physics_engine.apply_impulse(
                                self.player,
                                [0, PLAYER_JUMP_FORCE])
                            arcade.play_sound(self.jump_sound)

                        self.player.combo_jumps += 1
                        if self.player.combo_jumps > PLAYER_MAX_JUMP_COMBO:
                            self.player.combo_jumps = PLAYER_MAX_JUMP_COMBO

                        self.player.combo_jump_timer = PLAYER_COMBO_JUMP_TIMER

        if not self.up_pressed:
            self.player.newJump = True
        # endregion

        # region Climbing
        ladder_hit_list = arcade.check_for_collision_with_list(
            self.player, self.scene["Ladder"]
        )

        if ladder_hit_list:
            self.player.on_ladder = True
        else:
            self.player.on_ladder = False

        if self.player.on_ladder:
            self.physics_engine.gravity = (0, 0)
            self.physics_engine.damping = 0.01
            self.physics_engine.max_vertical_velocity = PLAYER_MAX_CLIMB_SPEED

            if self.up_pressed and not self.down_pressed:
                force = (0, PLAYER_CLIMB_FORCE)
                self.physics_engine.apply_force(self.player, force)
                # Set friction to zero for the player while moving
                self.physics_engine.set_friction(self.player, 0)

            elif self.down_pressed and not self.up_pressed:
                force = (0, -PLAYER_CLIMB_FORCE)
                self.physics_engine.apply_force(self.player, force)
                # Set friction to zero for the player while moving
                self.physics_engine.set_friction(self.player, 0)

            else:
                self.physics_engine.set_friction(self.player, PLAYER_FRICTION)

        else:
            self.physics_engine.damping = 1.0
            self.physics_engine.max_vertical_velocity = PLAYER_MAX_VERTICAL_SPEED
            self.physics_engine.gravity = GRAVITY
        # endregion


        self.score_text = f"Score: {int(self.score)}, there are {len(self.scene['Coin'])} remaining"

        # region Keep track of time
        self.real_timer_from_right = TIMER_FROM_RIGHT
        self.total_time += delta_time
        minutes = int(self.total_time) // 60
        seconds = int(self.total_time) % 60
        self.milliseconds = int((self.total_time - seconds) * 100 // 1)
        self.clock_text = f"{minutes}:{seconds}"
        x = 1
        self.real_timer_from_right += 7
        while x < len(self.clock_text):
            self.real_timer_from_right += 14
            x += 1
        # endregion

        # Move the camera
        self.center_camera_on_player()

        # Move items in the physics engine
        self.physics_engine.step()

    def on_draw(self):
        """ Draw everything """
        arcade.start_render()

        # Make the camera follow the player
        self.player_camera.use()

        # Draw the game
        self.scene.draw()
        # self.scene.draw_hit_boxes()

        # Draw the gui
        self.gui_camera.use()
        # Draw the score counter
        arcade.draw_text(
            self.score_text,
            SCORE_FROM_LEFT,
            SCREEN_HEIGHT - SCORE_FROM_TOP,
            WHITE,
            18
        )

        # Draw the timer
        arcade.draw_text(
            self.clock_text,
            SCREEN_WIDTH - self.real_timer_from_right,
            SCREEN_HEIGHT - TIMER_FROM_TOP,
            WHITE,
            18
        )

        arcade.draw_text(
            f":{self.milliseconds}",
            SCREEN_WIDTH - TIMER_FROM_RIGHT,
            SCREEN_HEIGHT - TIMER_FROM_TOP,
            WHITE,
            18
        )

    def center_camera_on_player(self):
        screen_center_x = self.player.center_x - (self.player_camera.viewport_width / 2)
        screen_center_y = self.player.center_y - (self.player_camera.viewport_height / 2)

        # Stop it from scrolling past 0
        if screen_center_x < 0:
            screen_center_x = 0
        if screen_center_y < 0:
            screen_center_y = 0

        player_centered = screen_center_x, screen_center_y

        self.player_camera.move_to(player_centered)


def main():
    """ Main function """
    window = MyGame(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    window.setup()
    arcade.run()


if __name__ == "__main__":
    main()
