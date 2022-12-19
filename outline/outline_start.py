import math
import pathlib
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


def add_empty(name=None):

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
    empty = add_empty(name=f"empty.tracker-target.{obj.name}")

    make_active(obj)
    bpy.ops.object.constraint_add(type="TRACK_TO")
    bpy.context.object.constraints["Track To"].target = empty

    return empty


def set_1080px_square_render_res():
    """
    Set the resolution of the rendered image to 1080 by 1080
    """
    bpy.context.scene.render.resolution_x = 1080
    bpy.context.scene.render.resolution_y = 1080


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


class Axis:
    X = 0
    Y = 1
    Z = 2


def create_data_animation_loop(obj, data_path, start_value, mid_value, start_frame, loop_length, linear_extrapolation=True):
    """
    To make a data property loop we need to:
    1. set the property to an initial value and add a keyframe in the beginning of the loop
    2. set the property to a middle value and add a keyframe in the middle of the loop
    3. set the property the initial value and add a keyframe at the end of the loop
    """

    # set the start value
    setattr(obj, data_path, start_value)
    # add a keyframe at the start
    obj.keyframe_insert(data_path, frame=start_frame)

    # set the middle value
    setattr(obj, data_path, mid_value)
    # add a keyframe in the middle
    mid_frame = start_frame + (loop_length) / 2
    obj.keyframe_insert(data_path, frame=mid_frame)

    # set the end value
    setattr(obj, data_path, start_value)
    # add a keyframe in the end
    end_frame = start_frame + loop_length
    obj.keyframe_insert(data_path, frame=end_frame)

    if linear_extrapolation:
        set_fcurve_extrapolation_to_linear()


def parent(child_obj, parent_obj, keep_transform=False):
    """
    Parent the child object to the parent object

    Args:
        child_obj: child object that will be parented.
        parent_obj: parent object that will be parented to.
        keep_transform: keep the transform of the child object. Defaults to False.
    """
    make_active(child_obj)
    child_obj.parent = parent_obj
    if keep_transform:
        child_obj.matrix_parent_inverse = parent_obj.matrix_world.inverted()


def apply_material(material):
    obj = active_object()
    obj.data.materials.append(material)


def set_fcurve_extrapolation_to_linear(obj=None):
    """loops over all the fcurves of an action
    and sets the extrapolation to "LINEAR"
    """
    if obj is None:
        obj = active_object()

    for fc in obj.animation_data.action.fcurves:
        fc.extrapolation = "LINEAR"


def apply_hdri(path_to_image, bg_color, hdri_light_strength, bg_strength):
    """
    Based on a technique from a FlippedNormals tutorial
    https://www.youtube.com/watch?v=dbAWTNCJVEs
    """
    world_node_tree = bpy.context.scene.world.node_tree
    world_node_tree.nodes.clear()

    location_x = 0

    texture_coordinate_node = world_node_tree.nodes.new(type="ShaderNodeTexCoord")
    texture_coordinate_node.location.x = location_x
    location_x += 200

    mapping_node = world_node_tree.nodes.new(type="ShaderNodeMapping")
    mapping_node.location.x = location_x
    location_x += 200

    environment_texture_node = world_node_tree.nodes.new(type="ShaderNodeTexEnvironment")
    environment_texture_node.location.x = location_x
    location_x += 300
    environment_texture_node.image = bpy.data.images.load(path_to_image)

    background_node = world_node_tree.nodes.new(type="ShaderNodeBackground")
    background_node.location.x = location_x
    background_node.inputs["Strength"].default_value = hdri_light_strength

    background_node_2 = world_node_tree.nodes.new(type="ShaderNodeBackground")
    background_node_2.location.x = location_x
    background_node_2.location.y = -100
    background_node_2.inputs["Color"].default_value = bg_color
    background_node_2.inputs["Strength"].default_value = bg_strength

    light_path_node = world_node_tree.nodes.new(type="ShaderNodeLightPath")
    light_path_node.location.x = location_x
    light_path_node.location.y = 400
    location_x += 200

    mix_shader_node = world_node_tree.nodes.new(type="ShaderNodeMixShader")
    mix_shader_node.location.x = location_x
    location_x += 200

    world_output_node = world_node_tree.nodes.new(type="ShaderNodeOutputWorld")
    world_output_node.location.x = location_x
    location_x += 200

    # links begin
    from_node = background_node
    to_node = mix_shader_node
    world_node_tree.links.new(from_node.outputs["Background"], to_node.inputs["Shader"])

    from_node = mapping_node
    to_node = environment_texture_node
    world_node_tree.links.new(from_node.outputs["Vector"], to_node.inputs["Vector"])

    from_node = texture_coordinate_node
    to_node = mapping_node
    world_node_tree.links.new(from_node.outputs["Generated"], to_node.inputs["Vector"])

    from_node = environment_texture_node
    to_node = background_node
    world_node_tree.links.new(from_node.outputs["Color"], to_node.inputs["Color"])

    from_node = background_node_2
    to_node = mix_shader_node
    world_node_tree.links.new(from_node.outputs["Background"], to_node.inputs[2])

    from_node = light_path_node
    to_node = mix_shader_node
    world_node_tree.links.new(from_node.outputs["Is Camera Ray"], to_node.inputs["Fac"])

    from_node = mix_shader_node
    to_node = world_output_node
    world_node_tree.links.new(from_node.outputs["Shader"], to_node.inputs["Surface"])

    return world_node_tree


def animate_360_rotation(axis_index, last_frame, obj=None, clockwise=False, linear=True, start_frame=1):
    animate_rotation(360, axis_index, last_frame, obj, clockwise, linear, start_frame)


def animate_rotation(angle, axis_index, last_frame, obj=None, clockwise=False, linear=True, start_frame=1):
    if not obj:
        obj = active_object()
    frame = start_frame
    obj.keyframe_insert("rotation_euler", index=axis_index, frame=frame)

    if clockwise:
        angle_offset = -angle
    else:
        angle_offset = angle
    frame = last_frame
    obj.rotation_euler[axis_index] = math.radians(angle_offset) + obj.rotation_euler[axis_index]
    obj.keyframe_insert("rotation_euler", index=axis_index, frame=frame)

    if linear:
        set_fcurve_extrapolation_to_linear()


def enable_extra_curves():
    """
    Add Curve Extra Objects
    https://docs.blender.org/manual/en/latest/addons/add_curve/extra_objects.html
    """
    loaded_default, loaded_state = addon_utils.check("add_curve_extra_objects")
    if not loaded_state:
        addon_utils.enable("add_curve_extra_objects")


def setup_camera(frame_count):
    """
    create and setup the camera
    """
    bpy.ops.object.camera_add()
    camera = active_object()

    start_location = (-0.5, 7, 0)
    camera.location = start_location
    mid_location = (-0.5, 8.5, 1.5)
    create_data_animation_loop(camera, "location", start_location, mid_location, start_frame=1, loop_length=frame_count, linear_extrapolation=False)

    # set the camera as the "active camera" in the scene
    bpy.context.scene.camera = camera

    # set the Focal Length of the camera
    camera.data.lens = 70
    camera.data.dof.use_dof = True
    camera.data.dof.aperture_fstop = 1.1

    camera.data.passepartout_alpha = 0.9

    empty = track_empty(camera)

    camera.data.dof.focus_object = empty

    return empty


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

    project_name = "outline"
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

    loop_frame_count = frame_count + 1
    setup_camera(loop_frame_count)

    context = {"frame_count": frame_count, "loop_frame_count": loop_frame_count}

    return context


def add_lights():
    """
    I used this HDRI: https://polyhaven.com/a/studio_small_03

    Please consider supporting polyhaven.com @ https://www.patreon.com/polyhaven/overview
    """
    # update the path to where you downloaded the HDRI
    path_to_image = str(pathlib.Path.home() / "tmp" / "studio_small_03_1k.exr")

    color = get_random_color()
    apply_hdri(path_to_image, bg_color=color, hdri_light_strength=1, bg_strength=1)


def render_loop():
    bpy.ops.render.render(animation=True)


def create_metallic_material(color, name=None, roughness=0.1, return_nodes=False):
    if name is None:
        name = ""

    material = bpy.data.materials.new(name=f"material.metallic.{name}")
    material.use_nodes = True

    material.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = color
    material.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = roughness
    material.node_tree.nodes["Principled BSDF"].inputs["Metallic"].default_value = 1.0

    if return_nodes:
        return material, material.node_tree.nodes
    else:
        return material


def get_random_color():
    hex_color = random.choice(
        [
            "#FC766A",
            "#5B84B1",
            "#5F4B8B",
            "#E69A8D",
            "#42EADD",
            "#CDB599",
            "#00A4CC",
            "#F95700",
            "#00203F",
            "#ADEFD1",
            "#606060",
            "#D6ED17",
            "#ED2B33",
            "#D85A7F",
        ]
    )

    return hex_color_to_rgba(hex_color)


################################################################
# helper functions END
################################################################


def create_centerpiece(context):
    pass


def main():
    """
    Python code to generate this animation
    https://www.artstation.com/artwork/klEGRy
    """
    enable_extra_curves()

    context = scene_setup()
    create_centerpiece(context)
    # add_lights()


if __name__ == "__main__":
    main()
