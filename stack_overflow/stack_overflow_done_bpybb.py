import random
import math

import bpy

from bpybb.color import hex_color_to_rgba
from bpybb.object import track_empty, add_empty
from bpybb.output import set_1080px_square_render_res
from bpybb.random import time_seed
from bpybb.addon import enable_extra_meshes, enable_mod_tools
from bpybb.animate import set_fcurve_interpolation_to_linear
from bpybb.utils import clean_scene, active_object, clean_scene_experimental, duplicate_object


################################################################
# helper functions BEGIN
################################################################


def get_random_color():
    hex_color = random.choice(
        [
            "#402217",
            "#515559",
            "#727273",
            "#8C593B",
            "#A64E1B",
            "#A65D05",
            "#A68A80",
            "#A6A6A6",
            "#BF6415",
            "#BF8B2A",
            "#C5992E",
            "#E8BB48",
            "#F2DC6B",
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
    camera.data.lens = 65

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

    project_name = "stack_overflow"
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

    z_coord = 1
    loc = (6.5, -3, z_coord)
    rot = (0, 0, 0)
    empty = setup_camera(loc, rot)
    empty.location.z = 2

    context = {
        "frame_count": frame_count,
        "frame_count_loop": frame_count + 1,
    }

    return context


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


def apply_metallic_material(color, name=None, roughness=0.1):
    material = create_metallic_material(color, name=name, roughness=roughness)

    obj = active_object()
    obj.data.materials.append(material)


def add_lights():
    rig_obj, empty = create_light_rig(light_count=3, light_type="AREA", rig_radius=5.0, energy=150)
    rig_obj.location.z = 3

    bpy.ops.object.light_add(type="AREA", radius=5, location=(0, 0, 5))


def create_light_rig(light_count, light_type="AREA", rig_radius=2.0, light_radius=1.0, energy=100):
    bpy.ops.mesh.primitive_circle_add(vertices=light_count, radius=rig_radius)
    rig_obj = active_object()

    empty = add_empty(name=f"empty.tracker-target.lights")

    for i in range(light_count):
        loc = rig_obj.data.vertices[i].co

        bpy.ops.object.light_add(type=light_type, radius=light_radius, location=loc)
        light = active_object()
        light.data.energy = energy
        light.parent = rig_obj

        bpy.ops.object.constraint_add(type="TRACK_TO")
        light.constraints["Track To"].target = empty

    return rig_obj, empty


################################################################
# helper functions END
################################################################


def make_surface(color):
    # this operator is found in the "Add Mesh Extra Objects" add-on
    bpy.ops.mesh.primitive_z_function_surface(div_x=64, div_y=64, size_x=1, size_y=1)

    surface = active_object()

    bpy.ops.object.shade_smooth()
    surface.data.use_auto_smooth = True

    bpy.ops.object.modifier_add(type="SOLIDIFY")

    bpy.ops.object.modifier_add(type="BEVEL")
    surface.modifiers["Bevel"].width = 0.001
    surface.modifiers["Bevel"].limit_method = "NONE"

    # this operator is found in the "Modifier Tools" add-on
    bpy.ops.object.apply_all_modifiers()

    apply_metallic_material(color, name="metallic", roughness=random.uniform(0.35, 0.65))

    return surface


def update_object(obj):
    obj.scale *= 1.5
    obj.location.z = 2
    obj.rotation_euler.z = math.radians(270)


def animate_object_update(context, obj, current_frame):
    obj.keyframe_insert("scale", frame=current_frame)
    obj.keyframe_insert("location", frame=current_frame)
    obj.keyframe_insert("rotation_euler", frame=current_frame)

    update_object(obj)

    frame = current_frame + context["frame_count_loop"]

    obj.keyframe_insert("scale", frame=frame)
    obj.keyframe_insert("location", frame=frame)
    obj.keyframe_insert("rotation_euler", frame=frame)

    set_fcurve_interpolation_to_linear()


def create_centerpiece(context, color):

    frame_step = 6
    buffer = 1
    count = int((context["frame_count_loop"] * 2) / frame_step) + buffer
    current_frame = -context["frame_count_loop"]

    surface = make_surface(color)

    for _ in range(count):

        duplicate_surface = duplicate_object(surface)

        animate_object_update(context, duplicate_surface, current_frame)

        current_frame += frame_step


def create_background(color):
    bottom_surface = make_surface(color)
    bottom_surface.location.z -= 0.001

    top_surface = make_surface(color)
    update_object(top_surface)
    top_surface.location.z += 0.001

    bpy.ops.mesh.primitive_plane_add(size=100, location=(0, 0, 0.5))


def main():
    """
    Python code to generate this animation
    https://www.artstation.com/artwork/nEw0mK
    """
    context = scene_setup()

    enable_extra_meshes()
    enable_mod_tools()

    color = get_random_color()
    create_centerpiece(context, color)
    create_background(color)
    add_lights()


if __name__ == "__main__":
    main()
