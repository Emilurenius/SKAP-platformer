# Skap platforming game

# importing modules and libraries as needed
import arcade, os, json
from PIL import Image


# More convenient way to find files
def path(file_address):
    return os.path.realpath(f"{__file__}/../../../{file_address}")


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
SPRITE_SIZE = int(GRID_PIXEL_SIZE*0.4)

# Size of grid to show on screen, in number of tiles
SCREEN_GRID_WIDTH = 25
SCREEN_GRID_HEIGHT = 15

# Size of screen to show, in pixels
SCREEN_WIDTH = SPRITE_SIZE * SCREEN_GRID_WIDTH
SCREEN_HEIGHT = SPRITE_SIZE * SCREEN_GRID_HEIGHT

# GUI placements
TIMER_FROM_RIGHT = 38
TIMER_FROM_TOP = 20
SCORE_FROM_LEFT = 20
SCORE_FROM_TOP = 20

# Constants for color
WHITE = arcade.color.WHITE

# --- Physics forces. Higher number, faster accelerating.

# Gravity
GRAVITY = 2500

# Damping - Amount of speed lost per second
DEFAULT_DAMPING = 1.0
PLAYER_DAMPING = 0.3

# Friction between objects
PLAYER_FRICTION = 2.0
WALL_FRICTION = 0.7
DYNAMIC_ITEM_FRICTION = 0.6

# Mass (defaults to 1)
PLAYER_MASS = 2.0

# Player constants
PLAYER_MAX_HORIZONTAL_SPEED = 520
PLAYER_MAX_VERTICAL_SPEED = 1600
PLAYER_MAX_CLIMB_SPEED = 300
PLAYER_MOVE_FORCE_ON_GROUND = 8500
PLAYER_MOVE_FORCE_IN_AIR = 3000
PLAYER_CLIMB_FORCE = 2000
PLAYER_JUMP_FORCE = 1400
PLAYER_JUMP_SODA_BOOST = 250
PLAYER_CLIMB_SPEED = 10

class MyGame(arcade.Window):
    """ Main Window """

    def __init__(self, width, height, title):
        """ Create the variables """

        # Init the parent class
        super().__init__(width, height, title, resizable=True)

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

        self.player = {}
        self.damping = 0
        self.gravity = 0


        self.screen_width = SCREEN_WIDTH
        self.screen_height = SCREEN_HEIGHT

        # region animations.

        # endregion

    def setup(self):
        """ Set up everything with the game """

        # region Camera
        self.player_camera = arcade.Camera(self.screen_width, self.screen_height)
        self.gui_camera = arcade.Camera(self.screen_width, self.screen_height)
        # endregion

        # region Map
        # Map name
        map_name = "skap_plattformer/assets/levels/secretTestLevel.tmx"

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

        for layer in self.tile_map.tiled_map.layers:
            if layer.properties:
                if not self.scene[layer.name]:
                    self.scene.add_sprite_list(layer.name)
                self.scene[layer.name].properties = layer.properties
                print(f"Added {layer.properties} to {layer.name}")

        print(self.scene["Ground"].properties)
        # endregion

        # region Player
        image_source = path("skap_plattformer/assets/images/skapning-export.png")
        self.player = arcade.Sprite(image_source, 1, hit_box_algorithm='Simple')

        if "Player" not in self.scene.name_mapping:
            self.scene.add_sprite_list_before("Player", "DecorationInFrontPlayer")

        self.scene.add_sprite("Player", self.player)
        self.player.newJump = True
        self.player.jump_boost_soda = 0
        self.player.on_ladder = False
        self.player.on_ground = False
        self.player.air_time = 0
        self.player.animation_frame = 0
        self.player.jump_right_sprites = self.load_animation_sprite_sheet("jump_right", path("skap_plattformer/assets/player/jump_right_sprite_sheet.png"), 35)
        print(len(self.player.jump_right_sprites))
        self.player.texture = self.player.jump_right_sprites[7]

        grid_x = 3
        grid_y = 3
        self.player.center_x = SPRITE_SIZE * grid_x + SPRITE_SIZE / 2
        self.player.center_y = SPRITE_SIZE * grid_y + SPRITE_SIZE / 2

        # endregion

        # Damping means the fraction of speed that you still have after 1 second.
        self.damping = DEFAULT_DAMPING

        # Set the gravity. (0, 0) is good for outer space and top-down.
        self.gravity = (0, -GRAVITY)

        # region The physics engine
        self.physics_engine = arcade.PymunkPhysicsEngine(damping=self.damping,
                                                         gravity=self.gravity)

        # Add the player.
        self.physics_engine.add_sprite(self.player,
                                       damping=PLAYER_DAMPING,
                                       friction=PLAYER_FRICTION,
                                       mass=PLAYER_MASS,
                                       moment=arcade.PymunkPhysicsEngine.MOMENT_INF,
                                       collision_type="player",
                                       max_horizontal_velocity=PLAYER_MAX_HORIZONTAL_SPEED,
                                       max_vertical_velocity=PLAYER_MAX_VERTICAL_SPEED),

        # STATIC means cant move, DYNAMIC can move, KINEMATIC means can move, but has to be coded in.
        print(self.scene["Ground"].properties)

        # Add the ground spritelists
        for name in self.scene.name_mapping:
            hit_sprite_list = self.scene.get_sprite_list(name)
            if hit_sprite_list.properties['collision_type'] == "wall":
                self.physics_engine.add_sprite_list(self.scene[name],
                                                    friction=self.scene[name].properties["friction"],
                                                    collision_type="wall",
                                                    body_type=arcade.PymunkPhysicsEngine.STATIC)

        # Add the items
        self.physics_engine.add_sprite_list(self.scene["Item"],
                                            friction=DYNAMIC_ITEM_FRICTION,
                                            mass = 0.75,
                                            collision_type="item")
        # endregion

    def load_level(self):
        pass

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
                self.player.animation_frame += 1
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

        # Do the jump
        if self.player.on_ground and not self.player.on_ladder:
            if self.player.newJump:
                if self.up_pressed and not self.down_pressed:
                    if self.player.on_ground:
                        self.player.newJump = False

                        self.physics_engine.apply_impulse(
                            self.player, [0, PLAYER_JUMP_FORCE + PLAYER_JUMP_SODA_BOOST * self.player.jump_boost_soda])
                        arcade.play_sound(self.jump_sound)

        # Extending the jump
        if not self.player.on_ground and not self.player.on_ladder:
            self.player.air_time += 1

            if self.up_pressed and not self.down_pressed and self.player.air_time < 11 and not self.player.newJump:
                self.physics_engine.apply_force(self.player, (0, 3500+self.player.jump_boost_soda * PLAYER_JUMP_SODA_BOOST))
            if self.up_pressed and not self.down_pressed and self.player.air_time < 17 and not self.player.newJump:
                self.physics_engine.apply_force(self.player, (0, 2500+self.player.jump_boost_soda * PLAYER_JUMP_SODA_BOOST))

            else:
                self.player.air_time = 1000


            if self.down_pressed and not self.up_pressed:
                self.physics_engine.apply_force(self.player, (0, -5000))



        else:
            self.player.air_time = 0


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
                self.physics_engine.apply_force(self.player, [0, PLAYER_CLIMB_FORCE*100])
                # self.physics_engine.set_velocity(self.player, [self.physics_engine.get_physics_object(self.player).body.velocity.x, 300])
                # Set friction to zero for the player while moving
                self.physics_engine.set_friction(self.player, 0)

            elif self.down_pressed and not self.up_pressed:
                force = (0, -PLAYER_CLIMB_FORCE)
                self.physics_engine.apply_force(self.player, [0, -PLAYER_CLIMB_FORCE])

                self.physics_engine.set_friction(self.player, 0)

            else:
                self.physics_engine.set_velocity(self.player, [self.physics_engine.get_physics_object(self.player).body.velocity.x, 0])

        else:
            self.physics_engine.damping = 0.3
            self.physics_engine.max_vertical_velocity = PLAYER_MAX_VERTICAL_SPEED
            self.physics_engine.gravity = GRAVITY
        # endregion

        # region Collision Detection
        for name in self.scene.name_mapping:
            hit_sprite_list = self.scene.get_sprite_list(name)
            if hit_sprite_list.properties['collision_type'] == "pick_up":
                hit_list = arcade.check_for_collision_with_list(self.player, self.scene[name])

                for item in hit_list:
                    item.remove_from_sprite_lists()
                    #arcade.play_sound()
                    run_pick_up = getattr(self, item.properties['on_pick_up'])
                    run_pick_up(item)

        # region Ladders
        ladder_hit_list = arcade.check_for_collision_with_list(self.player, self.scene["Ladder"])
        if ladder_hit_list:
            self.player.on_ladder = True
        else:
            self.player.on_ladder = False
        # endregion

        self.score_text = f"Score: {int(self.score)}, there are {len(self.scene['Coin'])} remaining"

        # region Keep track of time
        self.real_timer_from_right = TIMER_FROM_RIGHT
        self.total_time += delta_time
        self.minutes = int(self.total_time) // 60
        self.seconds = int(self.total_time) % 60
        self.milliseconds = int((self.total_time - self.seconds - self.minutes*60) * 100 // 1)
        self.clock_text = f"{self.minutes}:{self.seconds}"
        x = 1
        self.real_timer_from_right += 7
        while x < len(self.clock_text):
            self.real_timer_from_right += 14
            x += 1
        # endregion

        # endregion

        # Move the camera
        self.center_camera_on_player()

        # region Animation

        if not self.player.on_ground and not self.player.on_ladder:

            print(self.physics_engine.get_physics_object(self.player).body.velocity.y)
            if self.physics_engine.get_physics_object(self.player).body.velocity.y > 500:
                self.player.texture = self.player.jump_right_sprites[0]

            elif self.physics_engine.get_physics_object(self.player).body.velocity.y > 400:
                self.player.texture = self.player.jump_right_sprites[1]

            elif self.physics_engine.get_physics_object(self.player).body.velocity.y > 200:
                self.player.texture = self.player.jump_right_sprites[2]

            elif self.physics_engine.get_physics_object(self.player).body.velocity.y > 50:
                self.player.texture = self.player.jump_right_sprites[3]

            elif self.physics_engine.get_physics_object(self.player).body.velocity.y > -100:
                self.player.texture = self.player.jump_right_sprites[4]

            elif self.physics_engine.get_physics_object(self.player).body.velocity.y > -300:
                self.player.texture = self.player.jump_right_sprites[5]

            elif self.physics_engine.get_physics_object(self.player).body.velocity.y > -400:
                self.player.texture = self.player.jump_right_sprites[6]

            elif self.physics_engine.get_physics_object(self.player).body.velocity.y > -500:
                self.player.texture = self.player.jump_right_sprites[7]

            elif self.physics_engine.get_physics_object(self.player).body.velocity.y > -600:
                self.player.texture = self.player.jump_right_sprites[8]

            elif self.physics_engine.get_physics_object(self.player).body.velocity.y > -700:
                self.player.texture = self.player.jump_right_sprites[9]

            elif self.physics_engine.get_physics_object(self.player).body.velocity.y > -800:
                self.player.texture = self.player.jump_right_sprites[10]

            else:
                self.player.texture = self.player.jump_right_sprites[11]



        if self.right_pressed and self.left_pressed:
            self.player.texture = arcade.load_texture(
                path("skap_plattformer/assets/player/jump_right_sprite_sheet.png"), 35 * self.player.animation_frame, 0, 35, 51, hit_box_algorithm='Detailed')
            print("Setting texture")

        if False:
            if self.player.animation_frame > 8:
                self.player.animation_frame = 0
            self.player.texture = arcade.load_texture(path("skap_plattformer/assets/player/jump_right_sprite_sheet.png"),
                                                      35 * self.player.animation_frame, 0, 35, 51,
                                                      hit_box_algorithm='Detailed')

        # endregion

        # Move items in the physics engine
        self.physics_engine.step()



    def on_draw(self):
        """ Draw everything """
        arcade.start_render()

        # Make the camera follow the player
        self.player_camera.use()

        # Draw the level
        self.scene.draw()
        #self.scene.draw_hit_boxes()

        # Draw the gui
        self.gui_camera.use()
        # Draw the score counter
        arcade.draw_text(
            self.score_text,
            SCORE_FROM_LEFT,
            self.screen_height - SCORE_FROM_TOP,
            WHITE,
            18
        )

        # Draw the timer
        arcade.draw_text(
            self.clock_text,
            self.screen_width - self.real_timer_from_right,
            self.screen_height - TIMER_FROM_TOP,
            WHITE,
            18
        )

        arcade.draw_text(
            f":{self.milliseconds}",
            self.screen_width - TIMER_FROM_RIGHT,
            self.screen_height - TIMER_FROM_TOP,
            WHITE,
            18
        )

    # region Misc specific functions
    def center_camera_on_player(self):
        screen_center_x = self.player.center_x - (self.screen_width / 2)
        screen_center_y = self.player.center_y - (self.screen_height / 2)

        # Stop it from scrolling past 0
        if screen_center_x < 0:
            screen_center_x = 0
        if screen_center_y < 0:
            screen_center_y = 0

        player_centered = screen_center_x, screen_center_y

        self.player_camera.move_to(player_centered)

    # region functions for items that can be picked up
    def mushroom(self, item):
        print("IT WOOOOOOOOOOOOOOOOOOOOORKS")
        print("A mushroom was picked up")

    def coin(self, coin):
        print(f"A coin worth {int(coin.properties['coin_value'])} was picked up")
        arcade.play_sound(self.collect_coin_sound)
        self.score += coin.properties['coin_value']

    def leapy_lime(self, item):
        print("A Leapy Lime was picked up")
        print("*energy-drink-noises*")
        self.player.jump_boost_soda += 1
    # endregion

    def on_resize(self, width, height):
        """ This method is automatically called when the window is resized. """

        # Call the parent. Failing to do this will mess up the coordinates,
        # and default to 0,0 at the center and the edges being -1 to 1.
        super().on_resize(width, height)
        self.screen_width = width
        self.screen_height = height
        self.player_camera.resize(width, height)
        self.gui_camera.resize(width, height)
        print(f"Window resized to: {width}, {height}")

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
        elif key == arcade.key.ESCAPE:
            self.setup()

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

    def load_animation_sprite_sheet(self, name, file_path, split_width):
        img = Image.open(file_path)
        width, height = img.size
        x = 0
        print(f"{width}, {split_width}")
        image_list = []

        while x * split_width < width:

            left = x * split_width  # 0 * 9
            top = 0
            sprite_width = split_width # 8

            image_list.insert(x, arcade.load_texture(file_path, left, top, sprite_width, height))

            x += 1

        return image_list
    # endregion


def main():
    """ Main function """
    window = MyGame(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    window.setup()
    arcade.run()


if __name__ == "__main__":
    main()
