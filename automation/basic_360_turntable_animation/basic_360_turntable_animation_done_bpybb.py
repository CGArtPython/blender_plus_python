"""
See YouTube tutorial here: https://www.youtube.com/watch?v=BSsjSj0iOaE
"""
import datetime
import functools
import pathlib

import mathutils
import bpy

# you need to install the bpybb Python package (https://www.youtube.com/watch?v=_irmuKXjhS0)
from bpybb.animate import animate_360_rotation
from bpybb.empty import add_ctrl_empty
from bpybb.output import set_1080p_render_res
from bpybb.utils import clean_scene, active_object, make_active, Axis

################################################################
# region helper functions BEGIN
################################################################


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
    path = pathlib.Path.home() / "tmp" / "grid_floor.blend"

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
