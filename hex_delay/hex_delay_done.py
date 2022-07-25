import random
import time
import math

import bpy

################################################################
# helper functions BEGIN
################################################################


def purge_orphans():
    """
    Remove all orphan data blocks

    see this from more info:
    https://youtu.be/3rNqVPtbhzc?t=149
    """
    if bpy.app.version >= (3, 0, 0):
        # run this only for Blender versions 3.0 and higher
        bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
    else:
        # run this only for Blender versions lower than 3.0
        # call purge_orphans() recursively until there are no more orphan data blocks to purge
        result = bpy.ops.outliner.orphans_purge()
        if result.pop() != "CANCELLED":
            purge_orphans()


def clean_scene():
    """
    Removing all of the objects, collection, materials, particles,
    textures, images, curves, meshes, actions, nodes, and worlds from the scene

    Checkout this video explanation with example

    "How to clean the scene with Python in Blender (with examples)"
    https://youtu.be/3rNqVPtbhzc
    """
    # make sure the active object is not in Edit Mode
    if bpy.context.active_object and bpy.context.active_object.mode == "EDIT":
        bpy.ops.object.editmode_toggle()

    # make sure non of the objects are hidden from the viewport, selection, or disabled
    for obj in bpy.data.objects:
        obj.hide_set(False)
        obj.hide_select = False
        obj.hide_viewport = False

    # select all the object and delete them (just like pressing A + X + D in the viewport)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()

    # find all the collections and remove them
    collection_names = [col.name for col in bpy.data.collections]
    for name in collection_names:
        bpy.data.collections.remove(bpy.data.collections[name])

    # in the case when you modify the world shader
    # delete and recreate the world object
    world_names = [world.name for world in bpy.data.worlds]
    for name in world_names:
        bpy.data.worlds.remove(bpy.data.worlds[name])
    # create a new world data block
    bpy.ops.world.new()
    bpy.context.scene.world = bpy.data.worlds["World"]

    purge_orphans()


def hex_color_to_rgb(hex_color):
    """
    Converting from a color in the form of a hex triplet string (en.wikipedia.org/wiki/Web_colors#Hex_triplet)
    to a Linear RGB

    Supports: "#RRGGBB" or "RRGGBB"

    Note: We are converting into Linear RGB since Blender uses a Linear Color Space internally
    https://docs.blender.org/manual/en/latest/render/color_management.html

    Video tutorial: https://www.youtube.com/watch?v=knc1CGBhJeU
    """
    # remove the leading '#' symbol if present
    if hex_color.startswith("#"):
        hex_color = hex_color[1:]

    assert len(hex_color) == 6, f"RRGGBB is the supported hex color format: {hex_color}"

    # extracting the Red color component - RRxxxx
    red = int(hex_color[:2], 16)
    # dividing by 255 to get a number between 0.0 and 1.0
    srgb_red = red / 255
    linear_red = convert_srgb_to_linear_rgb(srgb_red)

    # extracting the Green color component - xxGGxx
    green = int(hex_color[2:4], 16)
    # dividing by 255 to get a number between 0.0 and 1.0
    srgb_green = green / 255
    linear_green = convert_srgb_to_linear_rgb(srgb_green)

    # extracting the Blue color component - xxxxBB
    blue = int(hex_color[4:6], 16)
    # dividing by 255 to get a number between 0.0 and 1.0
    srgb_blue = blue / 255
    linear_blue = convert_srgb_to_linear_rgb(srgb_blue)

    return tuple([linear_red, linear_green, linear_blue])


def hex_color_to_rgba(hex_color, alpha=1.0):
    """
    Converting from a color in the form of a hex triplet string (en.wikipedia.org/wiki/Web_colors#Hex_triplet)
    to a Linear RGB with an Alpha passed as a parameter

    Supports: "#RRGGBB" or "RRGGBB"

    Video tutorial: https://www.youtube.com/watch?v=knc1CGBhJeU
    """
    linear_red, linear_green, linear_blue = hex_color_to_rgb(hex_color)
    return tuple([linear_red, linear_green, linear_blue, alpha])


def convert_srgb_to_linear_rgb(srgb_color_component):
    """
    Converting from sRGB to Linear RGB
    based on https://en.wikipedia.org/wiki/SRGB#From_sRGB_to_CIE_XYZ

    Video tutorial: https://www.youtube.com/watch?v=knc1CGBhJeU
    """
    if srgb_color_component <= 0.04045:
        linear_color_component = srgb_color_component / 12.92
    else:
        linear_color_component = math.pow((srgb_color_component + 0.055) / 1.055, 2.4)

    return linear_color_component


def active_object():
    """
    returns the active object
    """
    return bpy.context.active_object


def time_seed():
    """
    Sets the random seed based on the time
    and copies the seed into the clipboard
    """
    seed = time.time()
    print(f"seed: {seed}")
    random.seed(seed)

    # add the seed value to your clipboard
    bpy.context.window_manager.clipboard = str(seed)

    return seed


def add_ctrl_empty(name=None):

    bpy.ops.object.empty_add(type="PLAIN_AXES", align="WORLD")
    empty_ctrl = active_object()

    if name:
        empty_ctrl.name = name
    else:
        empty_ctrl.name = "empty.cntrl"

    return empty_ctrl


def make_active(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def track_empty(obj):
    """
    create an empty and add a 'Track To' constraint
    """
    empty = add_ctrl_empty(name=f"empty.tracker-target.{obj.name}")

    make_active(obj)
    bpy.ops.object.constraint_add(type="TRACK_TO")
    bpy.context.object.constraints["Track To"].target = empty

    return empty


def setup_camera(loc, rot):
    """
    create and setup the camera
    """
    bpy.ops.object.camera_add(location=loc, rotation=rot)
    camera = active_object()

    # set the camera as the "active camera" in the scene
    bpy.context.scene.camera = camera

    # set the Focal Length of the camera
    camera.data.lens = 70

    camera.data.passepartout_alpha = 0.9

    empty = track_empty(camera)

    camera.data.dof.use_dof = True
    camera.data.dof.focus_object = empty
    camera.data.dof.aperture_fstop = 0.1

    return empty


def set_1080px_square_render_res():
    """
    Set the resolution of the rendered image to 1080 by 1080
    """
    bpy.context.scene.render.resolution_x = 1080
    bpy.context.scene.render.resolution_y = 1080


def set_scene_props(fps, loop_seconds):
    """
    Set scene properties
    """
    frame_count = fps * loop_seconds

    scene = bpy.context.scene
    scene.frame_end = frame_count

    # set the world background to black
    world = bpy.data.worlds["World"]
    if "Background" in world.node_tree.nodes:
        world.node_tree.nodes["Background"].inputs[0].default_value = (0, 0, 0, 1)

    scene.render.fps = fps

    scene.frame_current = 1
    scene.frame_start = 1

    scene.eevee.use_bloom = True
    scene.eevee.bloom_intensity = 0.005

    # set Ambient Occlusion properties
    scene.eevee.use_gtao = True
    scene.eevee.gtao_distance = 4
    scene.eevee.gtao_factor = 5

    scene.eevee.taa_render_samples = 64

    scene.view_settings.look = "Very High Contrast"

    set_1080px_square_render_res()


def scene_setup(i=0):
    fps = 30
    loop_seconds = 6
    frame_count = fps * loop_seconds

    project_name = "hex_delay_spin"
    bpy.context.scene.render.image_settings.file_format = "FFMPEG"
    bpy.context.scene.render.ffmpeg.format = "MPEG4"
    bpy.context.scene.render.filepath = f"/tmp/project_{project_name}/loop_{i}.mp4"

    seed = 0
    if seed:
        random.seed(seed)
    else:
        time_seed()

    # Utility Building Blocks
    clean_scene()
    set_scene_props(fps, loop_seconds)

    loc = (0, 15, 0)
    rot = (0, 0, 0)
    setup_camera(loc, rot)

    context = {
        "frame_count": frame_count,
        "material": create_metallic_material(get_random_color()),
    }

    return context


def make_fcurves_bounce():
    for fcurve in bpy.context.active_object.animation_data.action.fcurves:
        for kf in fcurve.keyframe_points:
            kf.interpolation = "BOUNCE"


def render_loop():
    bpy.ops.render.render(animation=True)


def get_random_color():
    hex_color = random.choice(
        [
            "#846295",
            "#B369AC",
            "#BFB3CB",
            "#E3E0E7",
            "#F3F0E5",
            "#557E5F",
            "#739D87",
            "#C3CDB1",
            "#7F8BC3",
            "#0D2277",
            "#72ED72",
            "#40D4BC",
            "#7EADF0",
            "#EAEC71",
            "#C4C55D",
            "#EDE1D4",
            "#DBCBBD",
            "#A98E8E",
            "#676F84",
            "#4F5D6B",
            "#990065",
            "#C60083",
            "#FF00A9",
            "#F9D19C",
            "#BFB3A7",
            "#B3A598",
            "#998995",
            "#99A1A3",
            "#74817F",
            "#815D6D",
        ]
    )
    return hex_color_to_rgba(hex_color)


def get_random_highlight_color():
    hex_color = random.choice(
        [
            "#CB5A0C",
            "#DBF227",
            "#22BABB",
            "#FFEC5C",
        ]
    )
    return hex_color_to_rgb(hex_color)


def add_lights():
    rotation = (math.radians(-60), math.radians(-15), math.radians(-45))

    bpy.ops.object.light_add(type="SUN", rotation=rotation)
    sun_light = active_object()
    sun_light.data.energy = 1.5

    if random.randint(0, 1):
        bpy.ops.object.light_add(type="AREA")
        area_light = active_object()
        area_light.scale *= 5
        area_light.data.color = get_random_highlight_color()
        area_light.data.energy = 200

        euler_x_rotation = math.radians(180)
        z_location = -4
        if random.randint(0, 1):
            euler_x_rotation = 0
            z_location = 4

        area_light.rotation_euler.x = euler_x_rotation
        area_light.location.z = z_location


def create_metallic_material(color):
    material = bpy.data.materials.new(name="metallic.material")
    material.use_nodes = True

    bsdf_node = material.node_tree.nodes["Principled BSDF"]
    bsdf_node.inputs["Base Color"].default_value = color
    bsdf_node.inputs["Metallic"].default_value = 1.0

    return material


def apply_material(obj, material):
    obj.data.materials.append(material)


################################################################
# helper functions END
################################################################


def animate_rotation(context, obj, i, frame_offset):
    start_frame = 10 + i * frame_offset
    obj.keyframe_insert("rotation_euler", frame=start_frame)

    # rotate mesh about the z-axis
    degrees = 180
    radians = math.radians(degrees)
    obj.rotation_euler.z = radians

    # rotate mesh about the y-axis
    degrees = 120
    radians = math.radians(degrees)
    obj.rotation_euler.y = radians

    end_frame = context["frame_count"] - 10
    obj.keyframe_insert("rotation_euler", frame=end_frame)

    make_fcurves_bounce()


def create_bevel(obj):
    # convert mesh into a curve
    bpy.ops.object.convert(target="CURVE")

    # add bevel to curve
    obj.data.bevel_depth = 0.025
    obj.data.bevel_resolution = 16

    # shade smooth
    bpy.ops.object.shade_smooth()


def create_centerpiece(context):
    radius_step = 0.2

    number_of_shapes = 16

    frame_offset = 5

    # repeat number_of_shapes times
    for i in range(1, number_of_shapes):

        # add a mesh into the scene
        current_radius = i * radius_step
        bpy.ops.mesh.primitive_circle_add(vertices=6, radius=current_radius)

        # get a reference to the currently active object
        shape_obj = active_object()

        # rotate mesh about the x-axis
        degrees = -90
        radians = math.radians(degrees)
        shape_obj.rotation_euler.x = radians

        animate_rotation(context, shape_obj, i, frame_offset)

        create_bevel(shape_obj)

        apply_material(shape_obj, context["material"])


def main():
    """
    Python code to generate an abstract delayed rotation animation
    with hexagonal rings
    """
    context = scene_setup()
    create_centerpiece(context)
    add_lights()


if __name__ == "__main__":
    main()
