import random
import math
import contextlib

import bpy
import mathutils

from bpybb.color import hex_color_to_rgba, hex_color_to_rgb
from bpybb.animate import set_fcurve_extrapolation_to_linear
from bpybb.object import track_empty
from bpybb.output import set_1080px_square_render_res
from bpybb.random import time_seed
from bpybb.utils import clean_scene, active_object, clean_scene_experimental

################################################################
# helper functions BEGIN
################################################################

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
