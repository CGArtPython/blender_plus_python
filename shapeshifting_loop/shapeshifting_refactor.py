import random
import time
import math
import contextlib

import bpy
import mathutils

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


def create_base_material():
    material = bpy.data.materials.new(name=f"material.base")
    material.use_nodes = True

    # get a reference to the Principled BSDF node
    bsdf_node = material.node_tree.nodes.get("Principled BSDF")

    object_info_node = material.node_tree.nodes.new(type="ShaderNodeObjectInfo")
    object_info_node.location = mathutils.Vector((-800, 180))
    object_info_node.name = "Object Info"

    color_ramp_node = material.node_tree.nodes.new(type="ShaderNodeValToRGB")
    color_ramp_node.location = mathutils.Vector((-500, 150))
    color_ramp_node.name = "ColorRamp"
    color_ramp_node.color_ramp.interpolation = "LINEAR"

    # make the links between the nodes
    from_node = material.node_tree.nodes.get("Object Info")
    to_node = material.node_tree.nodes.get("ColorRamp")
    material.node_tree.links.new(from_node.outputs["Random"], to_node.inputs["Fac"])
    from_node = material.node_tree.nodes.get("ColorRamp")
    to_node = bsdf_node
    material.node_tree.links.new(from_node.outputs["Color"], to_node.inputs["Base Color"])
    material.node_tree.links.new(from_node.outputs["Color"], to_node.inputs["Roughness"])

    return material, material.node_tree.nodes


def render_loop():
    bpy.ops.render.render(animation=True)


def setup_camera(loc, rot):
    """
    create and setup the camera
    """
    bpy.ops.object.camera_add(location=loc, rotation=rot)
    camera = active_object()

    # set the camera as the "active camera" in the scene
    bpy.context.scene.camera = camera

    # set the Focal Length of the camera
    camera.data.lens = 14

    camera.data.passepartout_alpha = 0.9

    empty = track_empty(camera)

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
    scene.cycles.device = 'GPU'

    scene.cycles.samples = 300

    scene.view_settings.look = "Very High Contrast"

    set_1080px_square_render_res()


def scene_setup(i=0):
    fps = 30
    loop_seconds = 3
    frame_count = fps * loop_seconds

    project_name = "shapeshifting"
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

    loc = (1.5, -1.5, 1.5)
    rot = (0, 0, 0)
    setup_camera(loc, rot)

    context = {
        "frame_count": frame_count,
    }

    return context


def add_light():
    bpy.ops.object.light_add(type="AREA", radius=6, location=(0, 0, 2))
    bpy.context.object.data.energy = 400
    bpy.context.object.data.color = hex_color_to_rgb("#F2E7DC")
    bpy.context.object.data.shape = "DISK"

    degrees = 180
    bpy.ops.object.light_add(type="AREA", radius=6, location=(0, 0, -2), rotation=(0.0, math.radians(degrees), 0.0))
    bpy.context.object.data.energy = 300
    bpy.context.object.data.color = hex_color_to_rgb("#F29F05")
    bpy.context.object.data.shape = "DISK"


@contextlib.contextmanager
def edit_mode():
    bpy.ops.object.mode_set(mode="EDIT")
    yield
    bpy.ops.object.mode_set(mode="OBJECT")


def subdivide(number_cuts=1, smoothness=0):
    with edit_mode():
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.mesh.subdivide(number_cuts=number_cuts, smoothness=smoothness)


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


def make_color_ramp_stops_from_colors(color_ramp_node, colors):
    """
    Use the provided colors to add apply them to the color ramp stops.
    Add new stops to the color ramp if needed.
    """
    color_count = len(colors)
    assert color_count > 1, "You need to provide at least two colors"

    # calculate the step between the color ramp stops
    step = 1 / color_count
    current_position = step

    # add new stops if necessary
    # we are subtracting 2 here because the color ramp comes with two stops
    for i in range(color_count - 2):
        color_ramp_node.elements.new(current_position)
        current_position += step

    # apply the colors to the stops
    for i, color in enumerate(colors):
        color_ramp_node.elements[i].color = color


################################################################
# helper functions END
################################################################


def set_keyframe_point_interpolation_to_elastic(mesh_obj):
    for fcurve in mesh_obj.animation_data.action.fcurves:
        for keyframe_point in fcurve.keyframe_points:
            keyframe_point.interpolation = "ELASTIC"
            keyframe_point.easing = "AUTO"


def create_cast_to_sphere_animation_loop(context, mesh_obj):
    bpy.ops.object.modifier_add(type="CAST")

    create_data_animation_loop(
        mesh_obj.modifiers["Cast"],
        "factor",
        start_value=0.01,
        mid_value=1,
        start_frame=1,
        loop_length=context["frame_count"],
        linear_extrapolation=False
    )
    
    set_keyframe_point_interpolation_to_elastic(mesh_obj)


def create_base_mesh(context, name, size):

    bpy.ops.mesh.primitive_cube_add(size=size)
    mesh_instance = active_object()
    mesh_instance.name = name

    subdivide(number_cuts=5)

    create_cast_to_sphere_animation_loop(context, mesh_instance)

    return mesh_instance


def create_mesh_instance(context):
    mesh_instance = create_base_mesh(context, name="mesh_instance", size=0.18)

    bpy.ops.object.shade_smooth()

    bpy.ops.object.modifier_add(type='BEVEL')
    bpy.context.object.modifiers["Bevel"].segments = 16
    bpy.context.object.modifiers["Bevel"].width = 0.01

    material, nodes = create_base_material()
    mesh_instance.data.materials.append(material)

    colors = context["colors"]
    make_color_ramp_stops_from_colors(nodes["ColorRamp"].color_ramp, colors)

    return mesh_instance


def create_primary_mesh(context):

    obj = create_base_mesh(context, name="primary_mesh", size=2)

    obj.instance_type = "VERTS"
    obj.show_instancer_for_viewport = False
    obj.show_instancer_for_render = False

    return obj


def create_centerpiece(context):

    mesh_instance = create_mesh_instance(context)
    primary_mesh = create_primary_mesh(context)

    mesh_instance.parent = primary_mesh


def get_colors():
    colors = [
        "#A61B34",
        "#D9B18F",
        "#D9CBBF",
        "#732C02",
        "#A66E4E",
    ]
    return [hex_color_to_rgba(color) for color in colors]


def main():
    """
    Python code to generate this animation
    https://www.artstation.com/artwork/3dYDRg
    """
    context = scene_setup()
    context["colors"] = get_colors()
    create_centerpiece(context)
    add_light()


if __name__ == "__main__":
    main()
