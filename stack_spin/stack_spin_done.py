import random
import time
import math

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


def setup_camera(loc, rot, frame_count):
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
    camera.data.dof.aperture_fstop = 0.35

    start_value = camera.data.lens
    mid_value = camera.data.lens - 10
    loop_param(camera.data, "lens", start_value, mid_value, frame_count)

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

    if bpy.app.version < (4, 0, 0):
        scene.view_settings.look = "Very High Contrast"
    else:
        scene.view_settings.look = "AgX - Very High Contrast"

    set_1080px_square_render_res()


def setup_scene(i=0):
    fps = 30
    loop_seconds = 12
    frame_count = fps * loop_seconds

    project_name = "stack_spin"
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
    setup_camera(loc, rot, frame_count)

    context = {
        "frame_count": frame_count,
    }

    return context


def make_fcurves_linear():
    for fc in bpy.context.active_object.animation_data.action.fcurves:
        fc.extrapolation = "LINEAR"


def get_random_color():
    return random.choice(
        [
            [0.92578125, 1, 0.0, 1],
            [0.203125, 0.19140625, 0.28125, 1],
            [0.8359375, 0.92578125, 0.08984375, 1],
            [0.16796875, 0.6796875, 0.3984375, 1],
            [0.6875, 0.71875, 0.703125, 1],
            [0.9609375, 0.9140625, 0.48046875, 1],
            [0.79296875, 0.8046875, 0.56640625, 1],
            [0.96484375, 0.8046875, 0.83984375, 1],
            [0.91015625, 0.359375, 0.125, 1],
            [0.984375, 0.4609375, 0.4140625, 1],
            [0.0625, 0.09375, 0.125, 1],
            [0.2578125, 0.9140625, 0.86328125, 1],
            [0.97265625, 0.21875, 0.1328125, 1],
            [0.87109375, 0.39453125, 0.53515625, 1],
            [0.8359375, 0.92578125, 0.08984375, 1],
            [0.37109375, 0.29296875, 0.54296875, 1],
            [0.984375, 0.4609375, 0.4140625, 1],
            [0.92578125, 0.16796875, 0.19921875, 1],
            [0.9375, 0.9609375, 0.96484375, 1],
            [0.3359375, 0.45703125, 0.4453125, 1],
        ]
    )


def render_loop():
    bpy.ops.render.render(animation=True)


def apply_random_color_material(obj):
    color = get_random_color()
    mat = bpy.data.materials.new(name="Material")
    mat.use_nodes = True
    mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = color

    if bpy.app.version < (4, 0, 0):
        mat.node_tree.nodes["Principled BSDF"].inputs["Specular"].default_value = 0
    else:
        mat.node_tree.nodes["Principled BSDF"].inputs["Specular IOR Level"].default_value = 0

    obj.data.materials.append(mat)


def add_lights():
    rotation = (math.radians(60), 0.0, math.radians(180))
    bpy.ops.object.light_add(type="SUN", rotation=rotation)
    bpy.context.object.data.energy = 100
    bpy.context.object.data.diffuse_factor = 0.05
    bpy.context.object.data.angle = math.radians(45)


def loop_param(obj, param_name, start_value, mid_value, frame_count):
    frame = 1

    setattr(obj, param_name, start_value)
    obj.keyframe_insert(param_name, frame=frame)

    frame = frame_count / 2
    setattr(obj, param_name, mid_value)
    obj.keyframe_insert(param_name, frame=frame)

    frame = frame_count
    setattr(obj, param_name, start_value)
    obj.keyframe_insert(param_name, frame=frame)


def set_keyframe_to_ease_in_out(obj):
    for fcurve in obj.animation_data.action.fcurves:
        for kf in fcurve.keyframe_points:
            kf.interpolation = "BACK"
            kf.easing = "EASE_IN_OUT"


################################################################
# helper functions END
################################################################


def animate_shape(obj, vertices, start_frame, end_frame):
    obj.keyframe_insert("rotation_euler", frame=start_frame)

    one_turn = 360 / vertices
    obj.rotation_euler.z += math.radians(one_turn * 2)

    obj.keyframe_insert("rotation_euler", frame=end_frame)

    set_keyframe_to_ease_in_out(obj)


def create_shape(vertices, radius, rotation, location):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=0.1)

    obj = active_object()
    obj.rotation_euler = rotation
    obj.location = location

    apply_random_color_material(obj)

    bpy.ops.object.modifier_add(type="BEVEL")
    obj.modifiers["Bevel"].width = 0.02

    return obj


def gen_centerpiece(context):
    radius_step = 0.1
    radius = 1

    vertices = 5

    shape_count = 100

    z_location_step = -0.1
    current_location = mathutils.Vector((0, 0, 0))

    z_rotation_step = math.radians(5)
    current_rotation = mathutils.Euler((0.0, 0.0, 0.0))

    start_frame_step = 5
    end_frame = context["frame_count"] - 10

    for i in range(shape_count):
        start_frame = start_frame_step * i

        current_rotation.z = z_rotation_step * i
        current_location.z = z_location_step * i

        shape_obj = create_shape(vertices, radius, current_rotation, current_location)
        animate_shape(shape_obj, vertices, start_frame, end_frame)

        radius += radius_step


def main():
    """
    Python code to generate an animation loop
    """
    context = setup_scene()
    gen_centerpiece(context)
    add_lights()


if __name__ == "__main__":
    main()
