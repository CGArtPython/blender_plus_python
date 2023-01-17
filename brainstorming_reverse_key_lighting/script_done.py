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


def get_scene_configurations():
    return [
        {
            "light_power": 1000,
            "light_location": (-10.5, 9.0, 3),
            "light_rotation": (math.radians(10), math.radians(-65), math.radians(-60)),
            "light_scale": (1.0, 1.0, 1.0),
            "camera_focal_length": 40,
        },
        {
            "light_power": 2500,
            "light_location": (-10.5, 9.0, 3),
            "light_rotation": (math.radians(10), math.radians(-65), math.radians(-20)),
            "light_scale": (1.0, 2.0, 1.0),
            "camera_focal_length": 50,
        },
        {
            "light_power": 1500,
            "light_location": (-10.5, 9.0, 3),
            "light_rotation": (math.radians(10), math.radians(-65), math.radians(-20)),
            "light_scale": (1.4, 1.0, 1.0),
            "camera_focal_length": 60,
        },
    ]


def apply_scene_configuration(scene_config, empty_obj, camera_obj, area_light_obj):
    empty_obj.rotation_euler.z = math.radians(scene_config["empty_z_rotation"])

    area_light_obj.location = scene_config["light_location"]
    area_light_obj.rotation_euler = scene_config["light_rotation"]
    area_light_obj.scale = scene_config["light_scale"]
    area_light_obj.data.energy = scene_config["light_power"]

    camera_obj.location.z = scene_config["camera_z_loc"]
    camera_obj.data.lens = scene_config["camera_focal_length"]


def render_scene():

    output_folder_path = get_output_folder_path()
    time_stamp = datetime.datetime.now().strftime("%H-%M-%S")
    image_name = f"{__rig_obj_tag__}_{time_stamp}"
    bpy.context.scene.render.filepath = str(output_folder_path / f"{image_name}.png")

    bpy.ops.render.render(write_still=True)

    return image_name


def save_scene_configuration(image_name, scene_config):
    """Save the scene configuration into a json file and place it into the metadata folder"""
    metadata_folder_path = get_metadata_folder_path()
    metadata_file_name = str(metadata_folder_path / f"{image_name}.json")
    with open(metadata_file_name, "w") as metadata_file_obj:
        text = json.dumps(scene_config, indent=4)
        metadata_file_obj.write(text)


def extract_scene_configuration(image_name):
    """Based on the image name find the metadata for that image"""
    metadata_folder_path = get_metadata_folder_path()
    metadata_file_name = metadata_folder_path / f"{image_name}.json"

    if metadata_file_name.exists():
        with open(str(metadata_file_name), "r") as metadata_file_obj:
            text = metadata_file_obj.read()
            data = json.loads(text)
        return data
    else:
        print(f"ERROR: {metadata_file_name} scene configuration does not exist")

    return None


def load_scene_configuration(image_name):
    """Based on the image name find the metadata and apply it"""
    empty_obj, camera_obj, area_light_obj = scene_setup(full_resolution=True)

    scene_configuration = extract_scene_configuration(image_name)

    if scene_configuration:
        apply_scene_configuration(scene_configuration, empty_obj, camera_obj, area_light_obj)


def render_scene_configurations():

    empty_obj, camera_obj, area_light_obj = scene_setup()

    scene_configurations = get_scene_configurations()

    empty_z_rotation_step = 30
    current_empty_z_rotation = 0

    camera_z_loc_start = 0.9
    camera_z_loc_step = 0.1
    camera_z_loc_step_count = 3

    while current_empty_z_rotation < 360:

        current_camera_z_loc = camera_z_loc_start

        for _ in range(camera_z_loc_step_count):
            for scene_config in scene_configurations:
                scene_config["empty_z_rotation"] = current_empty_z_rotation
                scene_config["camera_z_loc"] = current_camera_z_loc

                apply_scene_configuration(scene_config, empty_obj, camera_obj, area_light_obj)

                image_name = render_scene()

                save_scene_configuration(image_name, scene_config)

            current_camera_z_loc -= camera_z_loc_step

        current_empty_z_rotation += empty_z_rotation_step


def main():
    """
    Brainstorming Reverse Key Lighting scene setup.

    Inspired by Gleb Alexandrov's tutorial
    One Simple Technique to Improve Your Lighting in Blender | Reverse Key Lighting
    https://www.youtube.com/watch?v=jrCtpmdAhF0
    """
    # If you like one of the created images you can set load_scene_config to True and
    # set image_name to the image name
    load_scene_config = False

    if load_scene_config:
        image_name = "brainstorm_15-34-16"
        load_scene_configuration(image_name)
    else:
        render_scene_configurations()


if __name__ == "__main__":
    main()
