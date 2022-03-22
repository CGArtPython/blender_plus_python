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
        bpy.ops.outliner.orphans_purge(
            do_local_ids=True, do_linked_ids=True, do_recursive=True
        )
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

    bpy.ops.object.empty_add()
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
    bpy.context.preferences.edit.use_negative_frames = True

    set_1080px_square_render_res()


def setup_scene(i=0):
    fps = 30
    loop_seconds = 6
    frame_count = fps * loop_seconds

    project_name = "outgoing_circles"
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

    loc = (0, 0, 7)
    rot = (0, 0, 0)
    setup_camera(loc, rot)

    context = {
        "frame_count": frame_count,
    }

    return context


def make_fcurves_linear():
    for fcurve in bpy.context.active_object.animation_data.action.fcurves:
        for points in fcurve.keyframe_points:
            points.interpolation = "LINEAR"


def get_random_color():
    return random.choice(
        [
            [0.48046875, 0.171875, 0.5, 0.99609375],
            [0.3515625, 0.13671875, 0.39453125, 0.99609375],
            [0.2734375, 0.21484375, 0.08984375, 0.99609375],
            [0.5625, 0.45703125, 0.234375, 0.99609375],
            [0.92578125, 0.8828125, 0.77734375, 0.99609375],
            [0.1640625, 0.4921875, 0.13671875, 0.99609375],
            [0.453125, 0.74609375, 0.328125, 0.99609375],
            [0.2734375, 0.21484375, 0.08984375, 0.99609375],
            [0.5625, 0.45703125, 0.234375, 0.99609375],
            [0.92578125, 0.8828125, 0.77734375, 0.99609375],
            [0.1640625, 0.4921875, 0.13671875, 0.99609375],
            [0.453125, 0.74609375, 0.328125, 0.99609375],
            [0.00390625, 0.11328125, 0.15625, 0.99609375],
            [0.0234375, 0.49609375, 0.46875, 0.99609375],
            [0.01953125, 0.51953125, 0.6953125, 0.99609375],
            [0, 0.66796875, 0.78515625, 0.99609375],
            [0, 0.15234375, 0.171875, 0.99609375],
            [0.3203125, 0, 0.12890625, 0.99609375],
            [0.56640625, 0, 0.2265625, 0.99609375],
            [0.99609375, 0, 0.3984375, 0.99609375],
            [0.9453125, 0.640625, 0.33203125, 0.99609375],
            [0.51953125, 0.453125, 0.38671875, 0.99609375],
            [0.84765625, 0.94140625, 0.63671875, 0.99609375],
            [0.30859375, 0.91796875, 0.59375, 0.99609375],
            [0.46484375, 0.76171875, 0.47265625, 0.99609375],
            [0.71875, 0.5390625, 0.546875, 0.99609375],
            [0.40234375, 0.3671875, 0.30859375, 0.99609375],
        ]
    )


def apply_material(obj):
    color = get_random_color()
    mat = bpy.data.materials.new(name="Material")
    mat.use_nodes = True
    mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = color
    mat.node_tree.nodes["Principled BSDF"].inputs["Specular"].default_value = 0

    obj.data.materials.append(mat)


def add_lights():
    bpy.ops.object.light_add(type="SUN")
    bpy.context.object.data.energy = 10


################################################################
# helper functions END
################################################################


def create_circle_control_empty():
    empty = add_ctrl_empty(name=f"empty.circle.cntrl")
    empty.rotation_euler.z = math.radians(random.uniform(0, 360))
    empty.location.z = random.uniform(-3, 1)
    return empty


def animate_object_translation(context, obj):
    frame = random.randint(-context["frame_count"], 0)
    obj.location.x = 0
    obj.keyframe_insert("location", frame=frame)

    frame += context["frame_count"]

    obj.location.x = random.uniform(5, 5.5)
    obj.keyframe_insert("location", frame=frame)

    fcurves = obj.animation_data.action.fcurves
    location_fcurve = fcurves.find("location")
    location_fcurve.modifiers.new(type="CYCLES")

    make_fcurves_linear()


def gen_centerpiece(context):

    for _ in range(500):
        empty = create_circle_control_empty()

        bpy.ops.mesh.primitive_circle_add(radius=0.1, fill_type="TRIFAN")
        circle = active_object()
        circle.parent = empty

        apply_material(circle)

        animate_object_translation(context, circle)


def main():
    """
    Python code to generate an animation loop with circles
    moving from the origin outward
    """
    context = setup_scene()
    gen_centerpiece(context)
    add_lights()


if __name__ == "__main__":
    main()
