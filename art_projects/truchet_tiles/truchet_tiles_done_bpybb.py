"""
See YouTube tutorial here:
"""
import functools
import logging
import math
import pprint
import random

import bpy

# you need to install the bpybb Python package (https://www.youtube.com/watch?v=_irmuKXjhS0)
from bpybb.addon import enable_extra_curves
from bpybb.animate import set_fcurve_extrapolation_to_linear
from bpybb.collection import create_collection, add_to_collection, make_instance_of_collection
from bpybb.color import hex_color_to_rgba
from bpybb.material import apply_reflective_material
from bpybb.empty import add_ctrl_empty
from bpybb.object import track_empty, join_objects, rotate_object
from bpybb.output import set_1080px_square_render_res
from bpybb.random import time_seed
from bpybb.utils import clean_scene, active_object, clean_scene_experimental, make_active, duplicate_object, Axis
from bpybb.world_shader import set_up_world_sun_light

################################################################
# helper functions BEGIN
################################################################


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


def animate_truchet_tile(context, truchet_tile):
    frame_step = context["frame_count"] / 4

    frame = 1
    truchet_tile.keyframe_insert("rotation_euler", index=Axis.Z, frame=frame)

    truchet_tile.rotation_euler.z += math.radians(90)
    frame += frame_step
    truchet_tile.keyframe_insert("rotation_euler", index=Axis.Z, frame=frame)

    frame += frame_step
    truchet_tile.keyframe_insert("rotation_euler", index=Axis.Z, frame=frame)

    truchet_tile.rotation_euler.z += math.radians(90)
    frame += frame_step
    truchet_tile.keyframe_insert("rotation_euler", index=Axis.Z, frame=frame)


def create_truchet_tile_pattern(context, truchet_tile_size, collection_name):

    # Note: we need to enable the "Add Curve Extra Objects" addon
    tile_pattern_size = truchet_tile_size / 2
    bpy.ops.curve.simple(
        location=(-tile_pattern_size, -tile_pattern_size, 0),
        Simple_Type="Arc",
        Simple_endangle=90,
        Simple_radius=tile_pattern_size,
        use_cyclic_u=False,
        edit_mode=False,
    )

    tile_part_1 = active_object()

    tile_part_1.data.extrude = 0.15
    bpy.ops.object.modifier_add(type="SOLIDIFY")
    tile_part_1.modifiers["Solidify"].thickness = 0.1
    tile_part_1.modifiers["Solidify"].offset = 0

    bpy.ops.object.convert(target="MESH")

    bpy.ops.object.shade_smooth()
    bpy.ops.object.shade_smooth(use_auto_smooth=True)

    bpy.ops.object.origin_set(type="ORIGIN_CURSOR", center="MEDIAN")

    tile_part_2 = duplicate_object()
    rotate_object(Axis.Z, 180)

    join_objects([tile_part_1, tile_part_2])
    add_to_collection(collection_name)

    apply_reflective_material(context["first_color"], roughness=0.5)

    tile = active_object()
    tile.name = "tile_pattern"

    return tile


def create_truchet_tile(context, truchet_tile_size, collection_name):

    truchet_tile = create_truchet_tile_pattern(context, truchet_tile_size, collection_name)

    animate_truchet_tile(context, truchet_tile)

    return truchet_tile


def create_truchet_tile_platform(context, truchet_tile_size):

    collection_name = "truchet_tile_platform"
    create_collection(collection_name=collection_name)

    ctrl_empty = add_ctrl_empty()
    ctrl_empty.name = "platform_ctrl"
    add_to_collection(collection_name)

    bpy.ops.mesh.primitive_plane_add(size=truchet_tile_size)
    add_to_collection(collection_name)
    plane = active_object()
    plane.parent = ctrl_empty

    apply_reflective_material(context["second_color"], roughness=1.0)

    truchet_tile = create_truchet_tile(context, truchet_tile_size, collection_name)
    truchet_tile.parent = ctrl_empty

    return collection_name


def create_truchet_tile_platform_group(step_x, step_y, x_range, y_range, base_truchet_tile_collection):
    current_x = step_x
    start_y = step_y

    platform_group_collection_name = "truchet_tiles_group"
    create_collection(collection_name=platform_group_collection_name)

    for _ in range(x_range):
        current_y = start_y
        for _ in range(y_range):
            loc = (current_x, current_y, 0)
            new_collection_obj = make_instance_of_collection(base_truchet_tile_collection, loc)
            make_active(new_collection_obj)
            add_to_collection(platform_group_collection_name)

            current_deg_rot = random.choice([0, 90])
            new_collection_obj.rotation_euler.z = math.radians(current_deg_rot)

            current_y += step_y

        current_x += step_x

    return platform_group_collection_name


def animate_camera(context, section_step, camera_ctrl_empty):
    frame = 1
    camera_ctrl_empty.keyframe_insert("location", index=Axis.X, frame=frame)
    camera_ctrl_empty.location.x += section_step * 2
    camera_ctrl_empty.keyframe_insert("location", index=Axis.X, frame=context["frame_count_loop"])
    make_active(camera_ctrl_empty)
    set_fcurve_extrapolation_to_linear()


def create_and_animate_camera(context, section_step):
    camera, camera_ctrl_empty = setup_camera()

    camera_ctrl_empty.location = (section_step, (section_step / 3), 0)

    camera.location.x += section_step / 2
    camera.location.y = -section_step / 2 + section_step / 10
    camera.location.z = section_step / 2

    animate_camera(context, section_step, camera_ctrl_empty)


def create_centerpiece(context):

    truchet_tile_size = 2
    base_truchet_tile_collection = create_truchet_tile_platform(context, truchet_tile_size)

    step_x = truchet_tile_size
    step_y = truchet_tile_size
    x_range = 12
    y_range = 12
    platform_group_collection_name = create_truchet_tile_platform_group(step_x, step_y, x_range, y_range, base_truchet_tile_collection)

    section_instance_count = 3
    section_step = step_x * x_range
    for i in range(1, section_instance_count + 1):
        loc = (section_step * i, 0, 0)
        make_instance_of_collection(platform_group_collection_name, loc)

    create_and_animate_camera(context, section_step)


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
