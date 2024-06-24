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


def apply_material(material):
    obj = active_object()
    obj.data.materials.append(material)


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

    return empty


def set_1080px_square_render_res():
    """
    Set the resolution of the rendered image to 1080 by 1080
    """
    bpy.context.scene.render.resolution_x = 1080
    bpy.context.scene.render.resolution_y = 1080


def make_fcurves_linear():
    for fcurve in bpy.context.active_object.animation_data.action.fcurves:
        for points in fcurve.keyframe_points:
            points.interpolation = "LINEAR"


def get_random_color():
    return random.choice(
        [
            [0.984375, 0.4609375, 0.4140625, 1.0],
            [0.35546875, 0.515625, 0.69140625, 1.0],
            [0.37109375, 0.29296875, 0.54296875, 1.0],
            [0.8984375, 0.6015625, 0.55078125, 1.0],
            [0.2578125, 0.9140625, 0.86328125, 1.0],
            [0.80078125, 0.70703125, 0.59765625, 1.0],
            [0.0, 0.640625, 0.796875, 1.0],
            [0.97265625, 0.33984375, 0.0, 1.0],
            [0.0, 0.125, 0.24609375, 1.0],
            [0.67578125, 0.93359375, 0.81640625, 1.0],
            [0.375, 0.375, 0.375, 1.0],
            [0.8359375, 0.92578125, 0.08984375, 1.0],
            [0.92578125, 0.16796875, 0.19921875, 1.0],
            [0.84375, 0.3515625, 0.49609375, 1.0],
            [0.58984375, 0.734375, 0.3828125, 1.0],
            [0.0, 0.32421875, 0.609375, 1.0],
            [0.9296875, 0.640625, 0.49609375, 1.0],
            [0.0, 0.38671875, 0.6953125, 1.0],
            [0.609375, 0.76171875, 0.83203125, 1.0],
            [0.0625, 0.09375, 0.125, 1.0],
        ]
    )


def render_loop():
    bpy.ops.render.render(animation=True)


def create_background():
    create_floor()
    create_emissive_ring()


def create_emissive_ring():
    # add a circle mesh into the scene
    bpy.ops.mesh.primitive_circle_add(vertices=128, radius=5.5)

    # get a reference to the currently active object
    ring_obj = bpy.context.active_object
    ring_obj.name = "ring.emissive"

    # rotate ring by 90 degrees
    ring_obj.rotation_euler.x = math.radians(90)

    # convert mesh into a curve
    bpy.ops.object.convert(target="CURVE")

    # add bevel to curve
    ring_obj.data.bevel_depth = 0.05
    ring_obj.data.bevel_resolution = 16

    # create and assign an emissive material
    ring_material = create_emissive_ring_material()
    ring_obj.data.materials.append(ring_material)


def create_emissive_ring_material():
    color = get_random_color()
    material = bpy.data.materials.new(name="emissive_ring_material")
    material.use_nodes = True
    if bpy.app.version < (4, 0, 0):
        material.node_tree.nodes["Principled BSDF"].inputs["Emission"].default_value = color
    else:
        material.node_tree.nodes["Principled BSDF"].inputs["Emission Color"].default_value = color
    material.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 30.0
    return material


def create_metal_ring_material():
    color = get_random_color()
    material = bpy.data.materials.new(name="metal_ring_material")
    material.use_nodes = True
    material.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = color
    material.node_tree.nodes["Principled BSDF"].inputs["Metallic"].default_value = 1.0
    return material


def create_floor_material():
    color = get_random_color()
    material = bpy.data.materials.new(name="floor_material")
    material.use_nodes = True
    material.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = color
    if bpy.app.version < (4, 0, 0):
        material.node_tree.nodes["Principled BSDF"].inputs["Specular"].default_value = 0
    else:
        material.node_tree.nodes["Principled BSDF"].inputs["Specular IOR Level"].default_value = 0
    return material


def create_floor():
    # add a plain into the scene
    bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, -6.0))
    floor_obj = active_object()
    floor_obj.name = "plane.floor"

    # create and assign an emissive material
    floor_material = create_floor_material()
    floor_obj.data.materials.append(floor_material)


def add_light():
    # add area light
    bpy.ops.object.light_add(type="AREA")
    area_light = active_object()

    # update scale and location
    area_light.location.z = 6
    area_light.scale *= 10

    # set the light's energy
    area_light.data.energy = 1000


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
    # scene.cycles.samples = 1024

    # Use the CPU to render
    scene.cycles.device = "CPU"
    scene.cycles.samples = 200

    if bpy.app.version < (4, 0, 0):
        scene.view_settings.look = "Very High Contrast"
    else:
        scene.view_settings.look = "AgX - Very High Contrast"

    set_1080px_square_render_res()


def setup_scene(i=0):
    fps = 30
    loop_seconds = 12
    frame_count = fps * loop_seconds

    project_name = "ring_loop"
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

    loc = (20, -20, 12)
    rot = (math.radians(60), 0, math.radians(70))
    setup_camera(loc, rot)

    context = {
        "frame_count": frame_count,
    }

    return context


################################################################
# helper functions END
################################################################


def animate_rotation(context, ring_obj, z_rotation, y_rotation):
    # rotate mesh about the y-axis
    degrees = y_rotation
    radians = math.radians(degrees)
    ring_obj.rotation_euler.y = radians

    # rotate mesh about the z-axis
    degrees = z_rotation
    radians = math.radians(degrees)
    ring_obj.rotation_euler.z = radians

    # insert keyframe at frame one
    start_frame = 1
    ring_obj.keyframe_insert("rotation_euler", frame=start_frame)

    # rotate mesh about the y-axis
    degrees = y_rotation + 360
    radians = math.radians(degrees)
    ring_obj.rotation_euler.y = radians

    # rotate mesh about the z-axis
    degrees = z_rotation + 360 * 2
    radians = math.radians(degrees)
    ring_obj.rotation_euler.z = radians

    # insert keyframe after the last frame (to make a seamless loop)
    end_frame = context["frame_count"] + 1
    ring_obj.keyframe_insert("rotation_euler", frame=end_frame)

    # make keyframe interpolation linear
    make_fcurves_linear()


def create_ring(index, current_radius, ring_material):
    # add a circle mesh into the scene
    bpy.ops.mesh.primitive_circle_add(vertices=128, radius=current_radius)

    # get a reference to the currently active object
    ring_obj = bpy.context.active_object
    ring_obj.name = f"ring.{index}"

    # convert mesh into a curve
    bpy.ops.object.convert(target="CURVE")

    # add bevel to curve
    ring_obj.data.bevel_depth = 0.05
    ring_obj.data.bevel_resolution = 16

    # shade smooth
    bpy.ops.object.shade_smooth()

    # apply the material
    apply_material(ring_material)

    return ring_obj


def create_centerpiece(context):
    # create variables used in the loop
    radius_step = 0.1
    number_rings = 50

    z_rotation_step = 10
    z_rotation = 0

    y_rotation = 30

    ring_material = create_metal_ring_material()

    # repeat 50 times
    for i in range(number_rings):

        # calculate new radius
        current_radius = radius_step * i

        ring_obj = create_ring(i, current_radius, ring_material)

        # rotate ring and inset keyframes
        animate_rotation(context, ring_obj, z_rotation, y_rotation)

        # update the z-axis rotation
        z_rotation = z_rotation + z_rotation_step


def main():
    """
    Python code that creates an abstract ring animation loop
    """
    context = setup_scene()
    create_centerpiece(context)
    create_background()
    add_light()


if __name__ == "__main__":
    main()
