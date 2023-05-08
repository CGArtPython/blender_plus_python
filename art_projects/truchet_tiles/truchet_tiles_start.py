"""
See YouTube tutorial here:
"""
import functools
import logging
import math
import pprint
import random
import time

import bpy

import addon_utils

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


def clean_scene_experimental():
    """
    This might crash Blender!
    Proceed at your own risk!
    But it will clean the scene.
    """
    old_scene_name = "to_delete"
    bpy.context.window.scene.name = old_scene_name
    bpy.ops.scene.new()
    bpy.data.scenes.remove(bpy.data.scenes[old_scene_name])

    # create a new world data block
    bpy.ops.world.new()
    bpy.context.scene.world = bpy.data.worlds["World"]

    purge_orphans()


def active_object():
    """
    returns the currently active object
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

    bpy.ops.object.empty_add(type="PLAIN_AXES")
    empty_ctrl = active_object()

    if name:
        empty_ctrl.name = name
    else:
        empty_ctrl.name = "empty.cntrl"

    return empty_ctrl


def duplicate_object(obj=None, linked=False):
    if obj is None:
        obj = active_object()

    deselect_all_objects()

    obj.select_set(True)

    bpy.context.view_layer.objects.active = obj

    bpy.ops.object.duplicate(linked=linked)
    dup_obj = active_object()

    return dup_obj


def make_active(obj):
    deselect_all_objects()
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


def enable_addon(addon_module_name):
    """
    Checkout this video explanation with example

    "How to enable add-ons with Python in Blender (with examples)"
    https://youtu.be/HnrInoBWT6Q
    """
    loaded_default, loaded_state = addon_utils.check(addon_module_name)
    if not loaded_state:
        addon_utils.enable(addon_module_name)


def enable_extra_curves():
    """
    enable Add Curve Extra Objects addon
    https://docs.blender.org/manual/en/3.0/addons/add_curve/extra_objects.html
    """
    enable_addon(addon_module_name="add_curve_extra_objects")


def join_objects(objects):
    deselect_all_objects()

    for obj in objects:
        obj.select_set(True)

    bpy.ops.object.join()

    new_obj = active_object()

    return new_obj


def set_1080px_square_render_res():
    """
    Set the resolution of the rendered image to 1080 by 1080
    """
    bpy.context.scene.render.resolution_x = 1080
    bpy.context.scene.render.resolution_y = 1080


def set_fcurve_extrapolation_to_linear():
    for fc in bpy.context.active_object.animation_data.action.fcurves:
        fc.extrapolation = "LINEAR"


def hex_color_to_rgb(hex_color):
    """
    Converting from a color in the form of a hex triplet string (en.wikipedia.org/wiki/Web_colors#Hex_triplet)
    to a Linear RGB

    Supports: "#RRGGBB" or "RRGGBB"

    Note: We are converting into Linear RGB since Blender uses a Linear Color Space internally
    https://docs.blender.org/manual/en/latest/render/color_management.html

    Video Tutorial: https://www.youtube.com/watch?v=knc1CGBhJeU
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

    Video Tutorial: https://www.youtube.com/watch?v=knc1CGBhJeU
    """
    linear_red, linear_green, linear_blue = hex_color_to_rgb(hex_color)
    return tuple([linear_red, linear_green, linear_blue, alpha])


def convert_srgb_to_linear_rgb(srgb_color_component):
    """
    Converting from sRGB to Linear RGB
    based on https://en.wikipedia.org/wiki/SRGB#From_sRGB_to_CIE_XYZ

    Video Tutorial: https://www.youtube.com/watch?v=knc1CGBhJeU
    """
    if srgb_color_component <= 0.04045:
        linear_color_component = srgb_color_component / 12.92
    else:
        linear_color_component = math.pow((srgb_color_component + 0.055) / 1.055, 2.4)

    return linear_color_component


def deselect_all_objects():
    """
    Similar to bpy.ops.object.select_all(action="DESELECT")
    """
    for obj in bpy.data.objects:
        obj.select_set(False)


def create_collection(collection_name):
    deselect_all_objects()

    collection = bpy.data.collections.new(name=collection_name)
    bpy.context.scene.collection.children.link(collection)

    return collection


def add_to_collection(collection_name, obj=None, base_collection=None):
    """
    Adds a given object to a collection with collection_name
    """
    if obj is None:
        obj = active_object()

    if base_collection is None:
        base_collection = bpy.context.scene.collection

    collection = bpy.data.collections.get(collection_name)
    if collection is None:
        logging.error("couldn't find a collection with the name '%s' ", collection_name)
        return
    collection.objects.link(obj)

    base_collection.objects.unlink(obj)


def make_instance_of_collection(collection_name, location, rotation_euler=None, base_collection=None):
    source_collection = bpy.data.collections.get(collection_name)
    if source_collection is None:
        logging.error("couldn't find a collection with the name '%s' ", collection_name)
        return

    if base_collection is None:
        base_collection = bpy.context.scene.collection

    new_name = f"{collection_name}.instance.{str(location)}"
    collection_instance = bpy.data.objects.new(name=new_name, object_data=None)
    collection_instance.location = location
    collection_instance.instance_type = "COLLECTION"
    collection_instance.instance_collection = source_collection

    base_collection.objects.link(collection_instance)

    if rotation_euler:
        collection_instance.rotation_euler = rotation_euler

    return collection_instance


class Axis:
    X = 0
    Y = 1
    Z = 2


def rotate_object(axis, degrees):
    bpy.context.active_object.rotation_euler[axis] = math.radians(degrees)


def create_reflective_material(color, name=None, roughness=0.1, specular=0.5, return_nodes=False):
    if name is None:
        name = ""

    material = bpy.data.materials.new(name=f"material.reflective.{name}")
    material.use_nodes = True

    material.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = color
    material.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = roughness
    material.node_tree.nodes["Principled BSDF"].inputs["Specular"].default_value = specular

    if return_nodes:
        return material, material.node_tree.nodes
    else:
        return material


def apply_reflective_material(color, name=None, roughness=0.1, specular=0.5):
    material = create_reflective_material(color, name=name, roughness=roughness, specular=specular)

    obj = active_object()
    obj.data.materials.append(material)


def set_up_world_sun_light(sun_config=None, strength=1.0):
    world_node_tree = bpy.context.scene.world.node_tree
    world_node_tree.nodes.clear()

    node_location_x_step = 300
    node_location_x = 0

    node_sky = world_node_tree.nodes.new(type="ShaderNodeTexSky")
    node_location_x += node_location_x_step

    world_background_node = world_node_tree.nodes.new(type="ShaderNodeBackground")
    world_background_node.inputs["Strength"].default_value = strength
    world_background_node.location.x = node_location_x
    node_location_x += node_location_x_step

    world_output_node = world_node_tree.nodes.new(type="ShaderNodeOutputWorld")
    world_output_node.location.x = node_location_x

    if sun_config:
        logging.info("Updating ShaderNodeTexSky params:")
        for attr, value in sun_config.items():
            if hasattr(node_sky, attr):
                logging.info("\t %s set to %s", attr, str(value))
                setattr(node_sky, attr, value)
            else:
                logging.warning("\t %s is not an attribute of ShaderNodeTexSky node", attr)

    world_node_tree.links.new(node_sky.outputs["Color"], world_background_node.inputs["Color"])
    world_node_tree.links.new(world_background_node.outputs["Background"], world_output_node.inputs["Surface"])

    return node_sky


# bpybb end


def configure_logging(level=logging.INFO):
    logging.basicConfig(level=level)


@functools.cache
def load_color_palettes():
    return [
        ["#69D2E7", "#A7DBD8", "#E0E4CC", "#F38630", "#FA6900"],
        ["#FE4365", "#FC9D9A", "#F9CDAD", "#C8C8A9", "#83AF9B"],
        ["#ECD078", "#D95B43", "#C02942", "#542437", "#53777A"],
        ["#556270", "#4ECDC4", "#C7F464", "#FF6B6B", "#C44D58"],
        ["#1B325F", "#9CC4E4", "#E9F2F9", "#3A89C9", "#F26C4F"],
        ["#E8DDCB", "#CDB380", "#036564", "#033649", "#031634"],
        ["#490A3D", "#BD1550", "#E97F02", "#F8CA00", "#8A9B0F"],
        ["#594F4F", "#547980", "#45ADA8", "#9DE0AD", "#E5FCC2"],
        ["#00A0B0", "#6A4A3C", "#CC333F", "#EB6841", "#EDC951"],
        ["#413D3D", "#040004", "#C8FF00", "#FA023C", "#4B000F"],
        ["#3FB8AF", "#7FC7AF", "#DAD8A7", "#FF9E9D", "#FF3D7F"],
        ["#CCF390", "#E0E05A", "#F7C41F", "#FC930A", "#FF003D"],
        ["#395A4F", "#432330", "#853C43", "#F25C5E", "#FFA566"],
        ["#343838", "#005F6B", "#008C9E", "#00B4CC", "#00DFFC"],
        ["#AAFF00", "#FFAA00", "#FF00AA", "#AA00FF", "#00AAFF"],
        ["#00A8C6", "#40C0CB", "#F9F2E7", "#AEE239", "#8FBE00"],
    ]


def select_random_color_palette():
    random_palette = random.choice(load_color_palettes())
    print("Random palette:")
    pprint.pprint(random_palette)
    return random_palette


@functools.cache
def get_color_palette():
    """Note: we will select a random color palette once.
    With the functools.cache decorator we will return the same palette.
    """
    return select_random_color_palette()


def get_random_color():
    color_palette = get_color_palette()
    hex_color = random.choice(color_palette)
    return hex_color_to_rgba(hex_color)


def select_color_pair():
    first_color = get_random_color()
    second_color = get_random_color()
    while second_color == first_color:
        second_color = get_random_color()
    return first_color, second_color


def setup_camera():
    """
    create and setup the camera
    """
    bpy.ops.object.camera_add()
    camera = active_object()

    # set the camera as the "active camera" in the scene
    bpy.context.scene.camera = camera

    # set the Focal Length of the camera
    camera.data.lens = 70

    camera.data.passepartout_alpha = 0.9

    empty = track_empty(camera)
    camera.parent = empty

    return camera, empty


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

    scene.render.engine = "CYCLES"

    # Use the GPU to render
    scene.cycles.device = "GPU"

    # Use the CPU to render
    # scene.cycles.device = "CPU"

    scene.cycles.samples = 300

    scene.view_settings.look = "Very High Contrast"

    set_1080px_square_render_res()


def scene_setup(i=0):
    fps = 30
    loop_seconds = 12
    frame_count = fps * loop_seconds

    project_name = "truchet_201"
    bpy.context.scene.render.image_settings.file_format = "FFMPEG"
    bpy.context.scene.render.ffmpeg.format = "MPEG4"
    bpy.context.scene.render.filepath = f"/tmp/project_{project_name}/loop_{i}.mp4"

    seed = 0
    if seed:
        random.seed(seed)
    else:
        time_seed()

    # Utility Building Blocks
    use_clean_scene_experimental = False
    if use_clean_scene_experimental:
        clean_scene_experimental()
    else:
        clean_scene()

    set_scene_props(fps, loop_seconds)

    context = {
        "frame_count": frame_count,
        "frame_count_loop": frame_count + 1,
    }

    return context


################################################################
# helper functions END
################################################################


def create_centerpiece(context):
    pass


def main():
    """
    Python code to generate this animation
    https://www.artstation.com/artwork/g2lDPx
    """
    configure_logging()

    enable_extra_curves()

    context = scene_setup()
    context["first_color"], context["second_color"] = select_color_pair()

    create_centerpiece(context)

    sun_config = {"sun_rotation": math.radians(random.uniform(0, 360))}
    set_up_world_sun_light(sun_config, strength=0.1)


if __name__ == "__main__":
    main()
