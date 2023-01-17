# extend Python's functionality to work with file paths
import pathlib

# extend Python's functionality to work with JSON files
import json

# extend Python's functionality to work with time and dates
import datetime

# extend Python's math functionality
import math

# give Python access to Blender's functionality
import bpy


__rig_obj_tag__ = "brainstorm"

################################################################
# region helper functions BEGIN
################################################################


def get_output_folder_path():
    return pathlib.Path.home() / "tmp"


def get_metadata_folder_path():
    output_path = get_output_folder_path()
    metadata_folder_path = output_path / "metadata"
    if not metadata_folder_path.exists():
        metadata_folder_path.mkdir()
    return metadata_folder_path


def parent(child_obj, parent_obj, keep_transform=False):
    """Parent the child object to the parent object"""
    child_obj.parent = parent_obj
    if keep_transform:
        child_obj.matrix_parent_inverse = parent_obj.matrix_world.inverted()


def create_empty():
    bpy.ops.object.empty_add()
    empty_obj = bpy.context.active_object

    empty_obj.name = f"empty.{__rig_obj_tag__}"

    starting_empty_loc = (0.0, 0.0, 0.1)
    empty_obj.location = starting_empty_loc
    return empty_obj


def create_camera(empty_obj):
    bpy.ops.object.camera_add()
    camera_obj = bpy.context.active_object

    camera_obj.name = f"camera.{__rig_obj_tag__}"

    starting_cam_loc = (1.2, -1.4, 0.9)
    camera_obj.location = starting_cam_loc
    parent(camera_obj, empty_obj, keep_transform=True)

    bpy.ops.object.constraint_add(type="TRACK_TO")
    bpy.context.object.constraints["Track To"].target = empty_obj

    return camera_obj


def create_area_light(empty_obj):
    bpy.ops.object.light_add(type="AREA")
    area_light_obj = bpy.context.active_object

    area_light_obj.name = f"area_light.{__rig_obj_tag__}"

    starting_light_loc = (-10.5, 9.0, 3)
    area_light_obj.location = starting_light_loc
    starting_light_rot = (0.2, -1.15, -1.0)
    area_light_obj.rotation_euler = starting_light_rot

    parent(area_light_obj, empty_obj, keep_transform=True)

    return area_light_obj


def create_rig():
    empty_obj = create_empty()

    camera_obj = create_camera(empty_obj)

    area_light_obj = create_area_light(empty_obj)

    return empty_obj, camera_obj, area_light_obj


def remove_rig():
    """Remove any rig objects that were left from the previous run"""
    objects_to_remove = [obj for obj in bpy.data.objects if __rig_obj_tag__ in obj.name]

    for obj in objects_to_remove:
        bpy.data.objects.remove(obj)


def scene_setup(full_resolution=False):
    remove_rig()

    empty_obj, camera_obj, area_light_obj = create_rig()

    bpy.context.scene.camera = camera_obj

    if full_resolution:
        bpy.context.scene.cycles.samples = 300
        bpy.context.scene.render.resolution_percentage = 100
    else:
        bpy.context.scene.cycles.samples = 50
        bpy.context.scene.render.resolution_percentage = 50

    return empty_obj, camera_obj, area_light_obj


################################################################
# endregion helper functions END
################################################################


def render_scene_configurations():

    empty_obj, camera_obj, area_light_obj = scene_setup()


def main():
    """
    Brainstorming Reverse Key Lighting scene setup.

    Inspired by Gleb Alexandrov's tutorial
    One Simple Technique to Improve Your Lighting in Blender | Reverse Key Lighting
    https://www.youtube.com/watch?v=jrCtpmdAhF0
    """
    render_scene_configurations()


if __name__ == "__main__":
    main()
