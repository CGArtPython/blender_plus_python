"""
See YouTube tutorial here: https://youtu.be/aeDbYuJyXr8
"""
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


def get_random_pallet_color(context):
    return random.choice(context["colors"])


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


# Blender 2.8
# def setup_camera(loc, rot):
#     """
#     create and setup the camera for Blender 2.8
#     """
#     bpy.ops.object.camera_add(rotation=(math.radians(90), 0 , 0))
#     camera = active_object()

#     empty_cam = add_ctrl_empty(name=f"empty.cam")
#     empty_cam.location = loc
#     empty_cam.rotation_euler = rot
#     camera.parent = empty_cam

#     # set the camera as the "active camera" in the scene
#     bpy.context.scene.camera = camera

#     # set the Focal Length of the camera
#     camera.data.lens = 70

#     camera.data.passepartout_alpha = 0.9

#     empty = track_empty(empty_cam)

#     return empty


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


def set_1k_square_render_res():
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
        world.node_tree.nodes["Background"].inputs[0].default_value = (0.0, 0.0, 0.0, 1)

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

    set_1k_square_render_res()


def make_ramp_from_colors(colors, color_ramp_node):
    """
    Creates new sliders on a Color Ramp Node and
    applies the list of colors on each slider
    """
    color_count = len(colors)

    step = 1 / color_count
    cur_pos = step
    # -2 is for the two sliders that are present on the ramp
    for _ in range(color_count - 2):
        color_ramp_node.elements.new(cur_pos)
        cur_pos += step

    for i, color in enumerate(colors):
        color_ramp_node.elements[i].color = color


def get_color_palette():
    # https://www.colourlovers.com/palette/2943292
    # palette = ['#D7CEA3FF', '#907826FF', '#A46719FF', '#CE3F0EFF', '#1A0C47FF']

    palette = [
        [0.83984375, 0.8046875, 0.63671875, 1.0],
        [0.5625, 0.46875, 0.1484375, 1.0],
        [0.640625, 0.40234375, 0.09765625, 1.0],
        [0.8046875, 0.24609375, 0.0546875, 1.0],
        [0.1015625, 0.046875, 0.27734375, 1.0],
    ]

    return palette


def apply_location():
    bpy.ops.object.transform_apply(location=True)


def setup_scene():
    fps = 30
    loop_seconds = 6
    frame_count = fps * loop_seconds

    project_name = "color_slices"
    bpy.context.scene.render.image_settings.file_format = "PNG"
    bpy.context.scene.render.filepath = f"/tmp/project_{project_name}/"

    seed = 0
    if seed:
        random.seed(seed)
    else:
        time_seed()

    # Utility Building Blocks
    clean_scene()
    set_scene_props(fps, loop_seconds)

    loc = (-8, -6, 7.5)
    rot = (0, 0, 0)
    cam_empty = setup_camera(loc, rot)
    cam_empty.location.z = 4.5

    context = {
        "frame_count": frame_count,
    }

    context["colors"] = get_color_palette()

    return context


################################################################
# helper functions END
################################################################


def gen_base_material():

    # create new material and enable nodes
    material = bpy.data.materials.new(name="base_material")
    material.use_nodes = True

    # remove all nodes from the material
    nodes_to_remove = []
    for node in material.node_tree.nodes:
        nodes_to_remove.append(node)

    for node in nodes_to_remove:
        material.node_tree.nodes.remove(node)

    location_x = 0

    # create the Texture Coordinate node
    texture_coordinate_node = material.node_tree.nodes.new(type="ShaderNodeTexCoord")
    texture_coordinate_node.location.x = location_x
    location_x += 250

    # create the Mapping node
    mapping_node = material.node_tree.nodes.new(type="ShaderNodeMapping")
    mapping_node.inputs["Rotation"].default_value.y = math.radians(90)
    mapping_node.inputs["Scale"].default_value.z = 0.1
    mapping_node.location.x = location_x
    location_x += 250

    # create the Gradient Texture node
    gradient_texture_node = material.node_tree.nodes.new(type="ShaderNodeTexGradient")
    gradient_texture_node.location.x = location_x
    location_x += 250

    # create the Color Ramp node
    color_ramp_node = material.node_tree.nodes.new(type="ShaderNodeValToRGB")
    color_ramp_node.location.x = location_x
    location_x += 350

    # create the Principled BSDF node
    principled_bsdf_node = material.node_tree.nodes.new(type="ShaderNodeBsdfPrincipled")
    principled_bsdf_node.location.x = location_x
    location_x += 350

    # create the Material Output node
    material_output_node = material.node_tree.nodes.new(type="ShaderNodeOutputMaterial")
    material_output_node.location.x = location_x

    # setup node links
    material.node_tree.links.new(principled_bsdf_node.outputs["BSDF"], material_output_node.inputs["Surface"])

    material.node_tree.links.new(color_ramp_node.outputs["Color"], principled_bsdf_node.inputs["Base Color"])

    material.node_tree.links.new(mapping_node.outputs["Vector"], gradient_texture_node.inputs["Vector"])

    material.node_tree.links.new(texture_coordinate_node.outputs["Object"], mapping_node.inputs["Vector"])

    material.node_tree.links.new(gradient_texture_node.outputs["Color"], color_ramp_node.inputs["Fac"])

    return material


def setup_material(context):

    material = gen_base_material()
    nodes = material.node_tree.nodes
    make_ramp_from_colors(context["colors"], nodes["ColorRamp"].color_ramp)

    return material


def gen_perlin_curve(context, random_location, current_z):

    bpy.ops.mesh.primitive_circle_add(vertices=512, radius=context["radius"], location=(0, 0, current_z))
    circle = active_object()
    apply_location()

    deform_coords = []

    for vert in circle.data.vertices:
        new_location = vert.co + random_location
        noise_value = mathutils.noise.noise(new_location)
        noise_value = noise_value / 2

        projected_co = mathutils.Vector((vert.co.x, vert.co.y, 0))
        deform_vector = projected_co * noise_value

        deform_coord = vert.co + deform_vector
        deform_coords.append(deform_coord)

    bpy.ops.object.convert(target="CURVE")
    curve_obj = active_object()

    curve_obj.data.materials.append(context["material"])
    bpy.ops.object.shade_flat()

    curve_obj.data.bevel_mode = "OBJECT"  # remove this for Blender 2.8
    curve_obj.data.bevel_object = context["bevel object"]

    shape_key = add_shape_key(curve_obj, deform_coords)

    return shape_key


def add_shape_key(curve_obj, deform_coords):

    curve_obj.shape_key_add(name="Basis")

    shape_key = curve_obj.shape_key_add(name="Deform")

    deform_coords.reverse()
    for i, coord in enumerate(deform_coords):
        shape_key.data[i].co = coord
    shape_key.value = 1

    return shape_key


def create_bevel_object():
    bpy.ops.mesh.primitive_plane_add()
    bpy.ops.object.convert(target="CURVE")

    bevel_obj = active_object()
    bevel_obj.scale.x = 0.26
    bevel_obj.scale.y = 0.05
    bevel_obj.name = "bevel_object"

    return bevel_obj


def animate_curve(shape_key, start_frame):
    start_value = 1
    mid_value = 0

    loop_length = 60

    shape_key.value = start_value
    shape_key.keyframe_insert("value", frame=start_frame)

    current_frame = start_frame + loop_length / 2
    shape_key.value = mid_value
    shape_key.keyframe_insert("value", frame=current_frame)

    current_frame = start_frame + loop_length
    shape_key.value = start_value
    shape_key.keyframe_insert("value", frame=current_frame)

    start_frame += 1

    return start_frame


def gen_scene(context):
    random_location = mathutils.Vector((random.uniform(0, 100), random.uniform(0, 100), random.uniform(0, 100)))

    curve_count = 100
    context["material"] = setup_material(context)
    context["bevel object"] = create_bevel_object()
    context["radius"] = 1.1
    start_frame = 1
    for i in range(curve_count):
        current_z = 0.1 * i
        shape_key = gen_perlin_curve(context, random_location, current_z)

        start_frame = animate_curve(shape_key, start_frame)


def main():
    """
    Python code for this art project
    https://www.artstation.com/artwork/48wX6L

    Tutorial Video about this script:
    https://www.youtube.com/watch?v=K2iwBjQjgRQ&list=PLB8-FQgROBmlzQ7Xkq4YU7u08Zh3iuyPD&index=7
    """
    context = setup_scene()

    gen_scene(context)


if __name__ == "__main__":
    main()
