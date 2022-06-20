import random
import time
import math

import bpy
import mathutils
import addon_utils

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


def create_detail_rotation(obj, frame_count, x_degrees, y_degrees, z_degrees):
    rotation = obj.rotation_euler

    mid_value = mathutils.Euler(
        (
            rotation.x + math.radians(x_degrees),
            rotation.y + math.radians(y_degrees),
            rotation.z + math.radians(z_degrees),
        ),
        "XYZ",
    )

    obj.keyframe_insert("rotation_euler", frame=1)
    obj.keyframe_insert("rotation_euler", frame=frame_count)

    obj.rotation_euler = mid_value
    obj.keyframe_insert("rotation_euler", frame=frame_count / 2)


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

    set_1080px_square_render_res()

    cycles = True
    if cycles:
        bpy.context.scene.render.engine = "CYCLES"
        bpy.context.scene.cycles.device = "GPU"
        bpy.context.scene.cycles.samples = 1024


def setup_scene(i=0):
    fps = 30
    loop_seconds = 12
    frame_count = fps * loop_seconds

    seed = 0
    if seed:
        random.seed(seed)
    else:
        time_seed()

    project_name = "weave"
    render_folder = f"/tmp/project_{project_name}_{seed}/"
    render_pngs = True
    if render_pngs:
        bpy.context.scene.render.image_settings.file_format = "PNG"
        bpy.context.scene.render.filepath = render_folder
    else:
        bpy.context.scene.render.image_settings.file_format = "FFMPEG"
        bpy.context.scene.render.ffmpeg.format = "MPEG4"
        bpy.context.scene.render.filepath = f"{render_folder}/loop_{i}.mp4"

    # Utility Building Blocks
    clean_scene()
    set_scene_props(fps, loop_seconds)

    loc = (0, 0, 6)
    rot = (0, 0, 0)
    setup_camera(loc, rot)

    context = {
        "frame_count": frame_count,
    }

    return context


def make_spline_fcurve_interpolation_linear():
    for fcurve in bpy.context.active_object.data.animation_data.action.fcurves:
        for points in fcurve.keyframe_points:
            points.interpolation = "LINEAR"


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


def enable_extra_curves():
    """
    Add Curve Extra Objects
    https://docs.blender.org/manual/en/latest/addons/add_curve/extra_objects.html
    """
    loaded_default, loaded_state = addon_utils.check("add_curve_extra_objects")
    if not loaded_state:
        addon_utils.enable("add_curve_extra_objects")


def create_emissive_material():
    color = get_random_color()
    material = bpy.data.materials.new(name="emissive_material")
    material.use_nodes = True
    material.node_tree.nodes["Principled BSDF"].inputs["Emission"].default_value = color
    material.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 5.0
    return material


def create_metal_material():
    color = get_random_color()
    material = bpy.data.materials.new(name="metal_material")
    material.use_nodes = True
    material.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = color
    material.node_tree.nodes["Principled BSDF"].inputs["Metallic"].default_value = 1.0
    return material


def apply_hdri(path_to_image, bg_color, hdri_light_strength, bg_strength):
    """
    Based on a technique from a FlippedNormals tutorial
    https://www.youtube.com/watch?v=dbAWTNCJVEs
    """
    world_node_tree = bpy.context.scene.world.node_tree

    nodes_to_remove = []
    for node in world_node_tree.nodes:
        nodes_to_remove.append(node)

    for node in nodes_to_remove:
        world_node_tree.nodes.remove(node)

    location_x = 0
    texture_coordinate_node = world_node_tree.nodes.new(type="ShaderNodeTexCoord")
    texture_coordinate_node.name = "Texture Coordinate"
    texture_coordinate_node.location.x = location_x
    location_x += 200

    mapping_node = world_node_tree.nodes.new(type="ShaderNodeMapping")
    mapping_node.location.x = location_x
    location_x += 200
    mapping_node.name = "Mapping"

    environment_texture_node = world_node_tree.nodes.new(type="ShaderNodeTexEnvironment")
    environment_texture_node.location.x = location_x
    location_x += 300
    environment_texture_node.name = "Environment Texture"
    environment_texture_node.image = bpy.data.images.load(path_to_image)

    background_node = world_node_tree.nodes.new(type="ShaderNodeBackground")
    background_node.location.x = location_x
    background_node.name = "Background"
    background_node.inputs["Strength"].default_value = hdri_light_strength

    background_node_2 = world_node_tree.nodes.new(type="ShaderNodeBackground")
    background_node_2.location.x = location_x
    background_node_2.location.y = -100
    background_node_2.name = "Background.001"
    background_node_2.inputs["Color"].default_value = bg_color
    background_node_2.inputs["Strength"].default_value = bg_strength

    light_path_node = world_node_tree.nodes.new(type="ShaderNodeLightPath")
    light_path_node.location.x = location_x
    light_path_node.location.y = 400
    location_x += 200
    light_path_node.name = "Light Path"

    mix_shader_node = world_node_tree.nodes.new(type="ShaderNodeMixShader")
    mix_shader_node.location.x = location_x
    location_x += 200
    mix_shader_node.name = "Mix Shader"

    world_output_node = world_node_tree.nodes.new(type="ShaderNodeOutputWorld")
    world_output_node.location.x = location_x
    location_x += 200

    # links begin
    from_node = background_node
    to_node = mix_shader_node
    world_node_tree.links.new(from_node.outputs["Background"], to_node.inputs["Shader"])

    from_node = mapping_node
    to_node = environment_texture_node
    world_node_tree.links.new(from_node.outputs["Vector"], to_node.inputs["Vector"])

    from_node = texture_coordinate_node
    to_node = mapping_node
    world_node_tree.links.new(from_node.outputs["Generated"], to_node.inputs["Vector"])

    from_node = environment_texture_node
    to_node = background_node
    world_node_tree.links.new(from_node.outputs["Color"], to_node.inputs["Color"])

    from_node = background_node_2
    to_node = mix_shader_node
    world_node_tree.links.new(from_node.outputs["Background"], to_node.inputs[2])

    from_node = light_path_node
    to_node = mix_shader_node
    world_node_tree.links.new(from_node.outputs["Is Camera Ray"], to_node.inputs["Fac"])

    from_node = mix_shader_node
    to_node = world_output_node
    world_node_tree.links.new(from_node.outputs["Shader"], to_node.inputs["Surface"])
    # links end

    return world_node_tree


def add_lights():
    """
    I used this HDRI: https://polyhaven.com/a/dresden_station_night

    Please consider supporting polyhaven.com @ https://www.patreon.com/polyhaven/overview
    """
    # update the path to where you downloaded the HDRI
    path_to_image = r"C:\tmp\dresden_station_night_1k.exr"

    # Uncomment the next 2 lines for a Linux/macOS path to the HDRI in '~/tmp' folder
    # import os
    # path_to_image = f"{os.path.expanduser('~')}/tmp/dresden_station_night_1k.exr"
    color = (0, 0, 0, 0)
    apply_hdri(path_to_image, bg_color=color, hdri_light_strength=0.1, bg_strength=1)


################################################################
# helper functions END
################################################################


def create_profile_curve():
    bpy.ops.curve.simple(
        Simple_Type='Arc', 
        Simple_endangle=180, 
        use_cyclic_u=False, 
        edit_mode=False)
    profile_curve = active_object()
    profile_curve.scale *= 0.1
    return profile_curve


def create_base_curve():
    bpy.ops.curve.spirals(
        spiral_type='TORUS', 
        turns=15, 
        steps=64, 
        cycles=1, 
        curves_number=4, 
        use_cyclic_u=True, 
        edit_mode=False)
    return active_object()


def animate_point_tilt(obj, frame_count):
    points = obj.data.splines.active.points
    
    for pnt in points:
        pnt.keyframe_insert("tilt", frame=1)
        pnt.tilt = math.radians(360)
        pnt.keyframe_insert("tilt", frame=frame_count + 1)
        
    make_spline_fcurve_interpolation_linear()


def create_primary_curve(profile_curve):
    primary_curve = create_base_curve()
    
    metal_material = create_metal_material()
    apply_material(metal_material)
    
    primary_curve.data.bevel_mode = 'OBJECT'
    primary_curve.data.bevel_object = profile_curve

    bpy.ops.object.modifier_add(type='SOLIDIFY')

    return primary_curve


def create_emissive_curve():
    emissive_curve = create_base_curve()
    
    emissive_material = create_emissive_material()
    apply_material(emissive_material)
    
    emissive_curve.data.bevel_depth = 0.01


def create_centerpiece(context):
    profile_curve = create_profile_curve()
    
    primary_curve = create_primary_curve(profile_curve)
    animate_point_tilt(primary_curve, context["frame_count"])
    
    create_emissive_curve()


def main():
    """
    Python code to generate this animation
    https://www.artstation.com/artwork/QrOv4E
    """
    context = setup_scene()
    add_lights()
    enable_extra_curves()
    create_centerpiece(context)


if __name__ == "__main__":
    main()
