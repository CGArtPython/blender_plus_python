"""
See YouTube tutorial here: https://www.youtube.com/watch?v=BSsjSj0iOaE
"""
import datetime
import functools
import math
import pathlib

import mathutils
import bpy

################################################################
# region helper functions BEGIN
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
    returns the currently active object
    """
    return bpy.context.active_object


def add_ctrl_empty(name=None):

    bpy.ops.object.empty_add(type="PLAIN_AXES")
    empty_ctrl = active_object()

    if name:
        empty_ctrl.name = f"empty.{name}"
    else:
        empty_ctrl.name = "empty.cntrl"

    return empty_ctrl


def make_active(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def set_fcurve_extrapolation_to_linear(obj=None):
    """
    Loops over all the fcurves of an action
    and sets the extrapolation to "LINEAR".
    """
    if obj is None:
        obj = active_object()

    for fcurve in obj.animation_data.action.fcurves:
        fcurve.extrapolation = "LINEAR"


class Axis:
    X = 0
    Y = 1
    Z = 2


def animate_360_rotation(axis_index, last_frame, obj=None, clockwise=False, linear=True, start_frame=1):
    animate_rotation(360, axis_index, last_frame, obj, clockwise, linear, start_frame)


def animate_rotation(angle, axis_index, last_frame, obj=None, clockwise=False, linear=True, start_frame=1):
    if not obj:
        obj = active_object()
    frame = start_frame
    obj.keyframe_insert("rotation_euler", index=axis_index, frame=frame)

    if clockwise:
        angle_offset = -angle
    else:
        angle_offset = angle
    frame = last_frame
    obj.rotation_euler[axis_index] = math.radians(angle_offset) + obj.rotation_euler[axis_index]
    obj.keyframe_insert("rotation_euler", index=axis_index, frame=frame)

    if linear:
        set_fcurve_extrapolation_to_linear()


def set_1080p_render_res():
    """
    Set the resolution of the rendered image to 1080p
    """
    bpy.context.scene.render.resolution_x = 1920
    bpy.context.scene.render.resolution_y = 1080


# bpybb end


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

    set_1080p_render_res()


def remove_libraries():
    bpy.data.batch_remove(bpy.data.libraries)


@functools.cache
def get_script_path():
    # check if we are running from the Text Editor
    if bpy.context.space_data != None and bpy.context.space_data.type == "TEXT_EDITOR":
        print("bpy.context.space_data script_path")
        script_path = bpy.context.space_data.text.filepath
        if not script_path:
            print("ERROR: Can't get the script file folder path, because you haven't saved the script file.")
    else:
        print("__file__ script_path")
        script_path = __file__

    return script_path


@functools.cache
def get_script_folder_path():
    script_path = get_script_path()
    return pathlib.Path(script_path).resolve().parent


def scene_setup():
    fps = 30
    loop_seconds = 12
    frame_count = fps * loop_seconds

    clean_scene()
    remove_libraries()

    for lib in bpy.data.libraries:
        bpy.data.batch_remove(ids=(lib,))

    set_scene_props(fps, loop_seconds)

    context = {
        "frame_count": frame_count,
        "loop_frame_count": frame_count + 1,
    }

    return context


def create_light_rig(light_count, light_type="AREA", rig_radius=2.0, light_radius=1.0, energy=100):
    bpy.ops.mesh.primitive_circle_add(vertices=light_count, radius=rig_radius)
    rig_obj = active_object()

    empty = add_ctrl_empty(name="empty.tracker-target.lights")

    for i in range(light_count):
        loc = rig_obj.data.vertices[i].co

        bpy.ops.object.light_add(type=light_type, radius=light_radius, location=loc)
        light = active_object()
        light.data.energy = energy
        light.parent = rig_obj

        bpy.ops.object.constraint_add(type="TRACK_TO")
        light.constraints["Track To"].target = empty

    return rig_obj, empty


def get_working_directory_path():
    """This function provides the folder path that the script will be operating from.
    There are examples of paths that you can use, just uncomment the path that you want to use.
    """
    # folder_path = pathlib.Path().home() / "tmp"

    folder_path = get_script_folder_path()

    # Examples of other folder paths
    ## Windows
    ### folder_path = pathlib.Path(r"E:\my_projects\project_123")
    ## Linux/macOS
    ### folder_path = pathlib.Path().home() / "my_projects" / "project_123"

    return folder_path


################################################################
# endregion helper functions END
################################################################


def get_list_of_blend_files(path):

    blend_files = []
    for blend_file_path in pathlib.Path(path).rglob("*.blend"):
        blend_files.append(blend_file_path)

    return blend_files


def link_objects(blend_file_path, with_name=None):

    # link the blender file objects into the current blender file
    with bpy.data.libraries.load(blend_file_path, link=True) as (data_from, data_to):
        data_to.objects = data_from.objects

    scene = bpy.context.scene

    linked_objects = []

    # link the objects into the scene collection
    for obj in data_to.objects:
        if obj is None:
            continue

        if with_name and with_name not in obj.name:
            continue

        scene.collection.objects.link(obj)
        linked_objects.append(obj)

    return linked_objects


def create_floor():
    path = get_working_directory_path() / "grid_floor.blend"

    if path.exists():
        link_objects(str(path))
    else:
        bpy.ops.mesh.primitive_plane_add(size=100)
        floor = active_object()

        material = bpy.data.materials.new(name="floor_material")
        material.diffuse_color = (0.0003, 0.0074, 0.0193, 1.0)
        floor.data.materials.append(material)


def prepare_scene(frame_count):

    create_floor()

    light_rig_obj, _ = create_light_rig(light_count=3)

    bpy.ops.object.empty_add()
    focus_empty = bpy.context.active_object
    animate_360_rotation(Axis.Z, frame_count)

    bpy.ops.object.camera_add()
    camera_obj = bpy.context.active_object
    bpy.context.scene.camera = camera_obj

    bpy.ops.object.constraint_add(type="TRACK_TO")
    bpy.context.object.constraints["Track To"].target = focus_empty
    camera_obj.parent = focus_empty

    return camera_obj, focus_empty, light_rig_obj


def get_object_center(target_obj):
    bound_box_coord_sum = mathutils.Vector()
    for bound_box_coord in target_obj.bound_box:
        bound_box_coord_sum += mathutils.Vector(bound_box_coord)

    local_obj_center = bound_box_coord_sum / len(target_obj.bound_box)
    return target_obj.matrix_world @ local_obj_center


def focus_camera_on_target_obj(camera_obj, target_obj):
    make_active(target_obj)

    bpy.ops.view3d.camera_to_view_selected()

    # zoom out a bit to get some space between the edge of the camera and the object
    camera_obj.location *= 1.5


def update_scene(target_obj, focus_empty, camera_obj, light_rig_obj):

    obj_center = get_object_center(target_obj)

    focus_empty.location = obj_center

    height = target_obj.dimensions.z * 2
    camera_obj.location = (height, height, height)

    focus_camera_on_target_obj(camera_obj, target_obj)

    light_rig_obj.location.z = camera_obj.location.z


def run_turntable_render(model_name, output_folder_path):
    time_stamp = datetime.datetime.now().strftime("%H-%M-%S")

    scene = bpy.context.scene

    scene.render.image_settings.file_format = "FFMPEG"
    scene.render.ffmpeg.format = "MPEG4"
    scene.render.filepath = str(output_folder_path / f"{model_name}_turntable_{time_stamp}.mp4")

    bpy.ops.render.render(animation=True)


def unlink_objects(objects):
    scene = bpy.context.scene

    # unlink objects from the
    for obj in objects:
        if obj is not None:
            scene.collection.objects.unlink(obj)


def render_turntable_models(context, blend_files):

    camera_obj, focus_empty, light_rig_obj = prepare_scene(context["loop_frame_count"])

    # we will be looking for models with this text in their name
    target_substr_name = "target"
    for blend_file in blend_files:
        print(f"processing {blend_file}")
        objects = link_objects(str(blend_file), with_name=target_substr_name)

        if not objects:
            print(f"didn't find any model with '{target_substr_name}' in it's name in {blend_file}")
            continue

        target_obj = objects[0]

        update_scene(target_obj, focus_empty, camera_obj, light_rig_obj)

        print(f"rendering turntable {blend_file}")
        output_folder_path = pathlib.Path(blend_file).parent
        run_turntable_render(target_obj.name, output_folder_path)

        unlink_objects(objects)


def main():
    """
    A script that finds all blend files under a path,
    links the target models into the current scene, and renders a turntable loop .mp4
    """
    context = scene_setup()

    # example of a path in your home folder
    models_folder_path = get_working_directory_path() / "models"

    blend_files = get_list_of_blend_files(models_folder_path)

    render_turntable_models(context, blend_files)


if __name__ == "__main__":
    main()
