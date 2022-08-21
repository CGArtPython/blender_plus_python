import random

import bpy

from bpybb.animate import animate_360_rotation
from bpybb.color import hex_color_to_rgba
from bpybb.material import create_reflective_material, apply_emission_material
from bpybb.object import track_empty
from bpybb.output import set_1080px_square_render_res
from bpybb.random import time_seed, apply_random_rotation
from bpybb.utils import clean_scene, active_object, Axis, clean_scene_experimental

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
    # scene.cycles.device = 'GPU'

    # Use the CPU to render
    scene.cycles.device = "CPU"

    scene.cycles.samples = 1024

    scene.view_settings.look = "Very High Contrast"

    set_1080px_square_render_res()


def scene_setup(i=0):
    fps = 30
    loop_seconds = 12
    frame_count = fps * loop_seconds

    project_name = "in_or_out"
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

    loc = (0, 0, 7)
    rot = (0, 0, 0)
    setup_camera(loc, rot)

    context = {
        "frame_count": frame_count,
    }

    return context


def add_light():
    bpy.ops.object.light_add(type="AREA", radius=1, location=(0, 0, 2))
    bpy.context.object.data.energy = 100
    bpy.context.object.data.color = get_random_color()[:3]
    bpy.context.object.data.shape = "DISK"


def apply_glare_composite_effect():
    bpy.context.scene.use_nodes = True

    render_layer_node = bpy.context.scene.node_tree.nodes.get("Render Layers")
    comp_node = bpy.context.scene.node_tree.nodes.get("Composite")

    # remove node_glare from the previous run
    old_node_glare = bpy.context.scene.node_tree.nodes.get("Glare")
    if old_node_glare:
        bpy.context.scene.node_tree.nodes.remove(old_node_glare)

    # create Glare node
    node_glare = bpy.context.scene.node_tree.nodes.new(type="CompositorNodeGlare")
    node_glare.size = 7
    node_glare.glare_type = "FOG_GLOW"
    node_glare.quality = "HIGH"
    node_glare.threshold = 0.2

    # create links
    bpy.context.scene.node_tree.links.new(render_layer_node.outputs["Image"], node_glare.inputs["Image"])
    bpy.context.scene.node_tree.links.new(node_glare.outputs["Image"], comp_node.inputs["Image"])


################################################################
# helper functions END
################################################################


def apply_metaball_material():
    color = get_random_color()
    material = create_reflective_material(color, name="metaball", roughness=0.1, specular=0.5)

    primary_metaball = bpy.data.metaballs[0]
    primary_metaball.materials.append(material)


def create_metaball_path(context):
    bpy.ops.curve.primitive_bezier_circle_add()
    path = active_object()

    path.data.path_duration = context["frame_count"]

    animate_360_rotation(Axis.X, context["frame_count"], path, clockwise=random.randint(0, 1))

    apply_random_rotation()

    if random.randint(0, 1):
        path.scale.x *= random.uniform(0.1, 0.4)
    else:
        path.scale.y *= random.uniform(0.1, 0.4)

    return path


def create_metaball(path):
    bpy.ops.object.metaball_add()
    ball = active_object()
    ball.data.render_resolution = 0.05
    ball.scale *= random.uniform(0.05, 0.5)

    bpy.ops.object.constraint_add(type="FOLLOW_PATH")
    bpy.context.object.constraints["Follow Path"].target = path
    bpy.ops.constraint.followpath_path_animate(constraint="Follow Path", owner="OBJECT")


def create_centerpiece(context):
    metaball_count = 10

    for _ in range(metaball_count):
        path = create_metaball_path(context)
        create_metaball(path)

    apply_metaball_material()


def create_background():
    bpy.ops.curve.primitive_bezier_circle_add(radius=1.5)
    bpy.context.object.data.resolution_u = 64
    bpy.context.object.data.bevel_depth = 0.05

    color = get_random_color()
    apply_emission_material(color, energy=30)


def main():
    """
    Python code to generate this animation
    https://www.artstation.com/artwork/KO66oG
    """
    context = scene_setup()
    create_centerpiece(context)
    create_background()
    add_light()
    apply_glare_composite_effect()


if __name__ == "__main__":
    main()
