import math
import pathlib
import random

import bpy

from bpybb.addon import enable_extra_curves
from bpybb.animate import animate_360_rotation
from bpybb.animate import create_data_animation_loop
from bpybb.color import hex_color_to_rgba
from bpybb.hdri import apply_hdri
from bpybb.material import apply_material
from bpybb.object import track_empty, add_empty
from bpybb.output import set_1080px_square_render_res
from bpybb.random import time_seed
from bpybb.utils import clean_scene, active_object, clean_scene_experimental, parent, Axis

################################################################
# helper functions BEGIN
################################################################


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


def create_profile_obj():
    bpy.ops.curve.primitive_bezier_circle_add(radius=0.02, enter_editmode=False)
    return active_object()


def add_curve(loop_frame_count, material, profile_obj):

    curve_ctrl = add_empty()
    curve_ctrl.rotation_euler.x = math.radians(90)
    curve_ctrl.rotation_euler.z = math.radians(45)

    bpy.ops.curve.simple(Simple_Type="Arc", Simple_endangle=120, edit_mode=False, use_cyclic_u=False)
    curve = active_object()

    apply_material(material)

    curve.location.y = -0.25

    curve.data.bevel_mode = "OBJECT"
    curve.data.bevel_object = profile_obj
    curve.data.use_fill_caps = True
    curve.data.resolution_u = 32

    animate_360_rotation(Axis.Z, loop_frame_count, obj=curve, clockwise=False, linear=True, start_frame=1)

    parent(curve, curve_ctrl)

    return curve_ctrl


def create_centerpiece(context):

    count = 32
    rotation_step = 360 / count

    current_rotation = 0

    profile_obj = create_profile_obj()

    material = create_metallic_material(get_random_color(), name="material", roughness=0.1)

    for _ in range(count):
        rotation_ctrl = add_empty()
        rotation_ctrl.rotation_euler.y = math.radians(current_rotation)

        curve_ctrl = add_curve(context["loop_frame_count"], material, profile_obj)
        parent(curve_ctrl, rotation_ctrl)

        current_rotation += rotation_step


def main():
    """
    Python code to generate this animation
    https://www.artstation.com/artwork/klEGRy
    """
    enable_extra_curves()

    context = scene_setup()
    create_centerpiece(context)
    add_lights()


if __name__ == "__main__":
    main()
