"""
Python code to generate this animation
https://www.artstation.com/artwork/0nVn4V

Based on a phyllotaxis pattern created by formula 4.1 from
http://algorithmicbotany.org/papers/abop/abop-ch4.pdf

Inspired by Dan Shiffman's Coding Challenge #30: Phyllotaxis
https://www.youtube.com/watch?v=KWoJgHFYWxY&t=0s

"""

import random
import math

import bpy

from bpybb.color import hex_color_to_rgba
from bpybb.material import create_emission_material
from bpybb.animate import set_fcurve_extrapolation_to_linear
from bpybb.object import track_empty
from bpybb.output import set_1080px_square_render_res
from bpybb.random import time_seed
from bpybb.utils import clean_scene, active_object


################################################################
# helper functions BEGIN
################################################################

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

    bpy.context.object.data.dof.use_dof = True
    bpy.context.object.data.dof.aperture_fstop = 0.1

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
        world.node_tree.nodes["Background"].inputs["Color"].default_value = (0, 0, 0, 1)

    scene.render.fps = fps

    scene.frame_current = 1
    scene.frame_start = 1

    # Use the CPU to render
    scene.cycles.device = "CPU"

    scene.cycles.samples = 1024

    scene.view_settings.look = "Very High Contrast"

    set_1080px_square_render_res()


def scene_setup(i=0):
    fps = 30
    loop_seconds = 12
    frame_count = fps * loop_seconds

    project_name = "floret"
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

    loc = (0, 0, 80)
    rot = (0, 0, 0)
    setup_camera(loc, rot)

    context = {
        "frame_count": frame_count,
        "fps": fps,
    }

    return context


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


################################################################
# helper functions END
################################################################


def calculate_end_frame(context, current_frame):
    # make sure the end frame is divisible by the FPS
    quotient, remainder = divmod(current_frame, context["fps"])

    if remainder != 0:
        bpy.context.scene.frame_end = (quotient + 1) * context["fps"]
    else:
        bpy.context.scene.frame_end = current_frame

    return bpy.context.scene.frame_end


def animate_depth_of_field(frame_end):

    start_focus_distance = 15.0
    mid_focus_distance = bpy.data.objects["Camera"].location.z / 2
    start_frame = 1
    loop_length = frame_end
    create_data_animation_loop(
        bpy.data.objects["Camera"].data.dof,
        "focus_distance",
        start_focus_distance,
        mid_focus_distance,
        start_frame,
        loop_length,
        linear_extrapolation=False,
    )


def calculate_phyllotaxis_coordinates(n, angle, scale_fac):
    """
    calculating a point in a phyllotaxis pattern based on formula 4.1 from
    http://algorithmicbotany.org/papers/abop/abop-ch4.pdf

    See tutorial for detailed description: https://youtu.be/aeDbYuJyXr8
    """
    # calculate "φ" in formula (4.1) http://algorithmicbotany.org/papers/abop/abop-ch4.pdf
    current_angle = n * angle

    # calculate "r" in formula (4.1) http://algorithmicbotany.org/papers/abop/abop-ch4.pdf
    current_radius = scale_fac * math.sqrt(n)

    # convert from Polar Coordinates (r,φ) to Cartesian Coordinates (x,y)
    x = current_radius * math.cos(current_angle)
    y = current_radius * math.sin(current_angle)

    return x, y


def create_centerpiece(context):

    colors = (hex_color_to_rgba("#306998"), hex_color_to_rgba("#FFD43B"))

    ico_sphere_radius = 0.2

    # "c" in formula (4.1) http://algorithmicbotany.org/papers/abop/abop-ch4.pdf
    scale_fac = 1.0

    # "α" angle in radians in formula (4.1) http://algorithmicbotany.org/papers/abop/abop-ch4.pdf
    angle = math.radians(random.uniform(137.0, 138.0))

    # set angle to the Fibonacci angle 137.5 to get the sunflower pattern
    # angle = math.radians(137.5)

    current_frame = 1
    frame_step = 0.5
    start_emission_strength_value = 0
    mid_emission_strength_value = 20
    loop_length = 60

    count = 300
    for n in range(count):

        x, y = calculate_phyllotaxis_coordinates(n, angle, scale_fac)

        # place ico sphere
        bpy.ops.mesh.primitive_ico_sphere_add(radius=ico_sphere_radius, location=(x, y, 0))
        obj = active_object()

        # assign an emission material
        material, nodes = create_emission_material(color=random.choice(colors), name=f"{n}_sphr", energy=30, return_nodes=True)
        obj.data.materials.append(material)

        # animate the Strength value of the emission material
        create_data_animation_loop(
            nodes["Emission"].inputs["Strength"],
            "default_value",
            start_emission_strength_value,
            mid_emission_strength_value,
            current_frame,
            loop_length,
            linear_extrapolation=False,
        )

        current_frame += frame_step

    current_frame = int(current_frame + loop_length)
    end_frame = calculate_end_frame(context, current_frame)

    animate_depth_of_field(end_frame)


def main():
    """
    Python code to generate this animation
    https://www.artstation.com/artwork/0nVn4V
    """
    context = scene_setup()
    create_centerpiece(context)


if __name__ == "__main__":
    main()
