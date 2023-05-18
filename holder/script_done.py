"""
Python code to generate this animation
https://www.artstation.com/artwork/g2A5rZ
"""
import random
import time
import pprint
import math


import addon_utils
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


def clean_scene_experimental():
    """
    This might crash Blender!
    Proceed at your own risk!
    But it will clean the scene.
    """
    old_scene_name = "to_delete"
    bpy.context.window.scene.name = old_scene_name
    bpy.ops.scene.new()
    bpy.data.scenes.remove(bpy.data.scenes[old_scene_name])

    # create a new world data block
    bpy.ops.world.new()
    bpy.context.scene.world = bpy.data.worlds["World"]

    purge_orphans()


def active_object():
    """
    returns the currently active object
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


def set_1080px_square_render_res():
    """
    Set the resolution of the rendered image to 1080 by 1080
    """
    bpy.context.scene.render.resolution_x = 1080
    bpy.context.scene.render.resolution_y = 1080


def set_fcurve_extrapolation_to_linear():
    for fc in bpy.context.active_object.animation_data.action.fcurves:
        fc.extrapolation = "LINEAR"


def hex_color_to_rgb(hex_color):
    """
    Converting from a color in the form of a hex triplet string (en.wikipedia.org/wiki/Web_colors#Hex_triplet)
    to a Linear RGB

    Supports: "#RRGGBB" or "RRGGBB"

    Note: We are converting into Linear RGB since Blender uses a Linear Color Space internally
    https://docs.blender.org/manual/en/latest/render/color_management.html

    Video Tutorial: https://www.youtube.com/watch?v=knc1CGBhJeU
    """
    # remove the leading '#' symbol if present
    if hex_color.startswith("#"):
        hex_color = hex_color[1:]

    assert len(hex_color) == 6, f"RRGGBB is the supported hex color format: {hex_color}"

    # extracting the Red color component - RRxxxx
    red = int(hex_color[:2], 16)
    # dividing by 255 to get a number between 0.0 and 1.0
    srgb_red = red / 255
    linear_red = convert_srgb_to_linear_rgb(srgb_red)

    # extracting the Green color component - xxGGxx
    green = int(hex_color[2:4], 16)
    # dividing by 255 to get a number between 0.0 and 1.0
    srgb_green = green / 255
    linear_green = convert_srgb_to_linear_rgb(srgb_green)

    # extracting the Blue color component - xxxxBB
    blue = int(hex_color[4:6], 16)
    # dividing by 255 to get a number between 0.0 and 1.0
    srgb_blue = blue / 255
    linear_blue = convert_srgb_to_linear_rgb(srgb_blue)

    return tuple([linear_red, linear_green, linear_blue])


def hex_color_to_rgba(hex_color, alpha=1.0):
    """
    Converting from a color in the form of a hex triplet string (en.wikipedia.org/wiki/Web_colors#Hex_triplet)
    to a Linear RGB with an Alpha passed as a parameter

    Supports: "#RRGGBB" or "RRGGBB"

    Video Tutorial: https://www.youtube.com/watch?v=knc1CGBhJeU
    """
    linear_red, linear_green, linear_blue = hex_color_to_rgb(hex_color)
    return tuple([linear_red, linear_green, linear_blue, alpha])


def convert_srgb_to_linear_rgb(srgb_color_component):
    """
    Converting from sRGB to Linear RGB
    based on https://en.wikipedia.org/wiki/SRGB#From_sRGB_to_CIE_XYZ

    Video Tutorial: https://www.youtube.com/watch?v=knc1CGBhJeU
    """
    if srgb_color_component <= 0.04045:
        linear_color_component = srgb_color_component / 12.92
    else:
        linear_color_component = math.pow((srgb_color_component + 0.055) / 1.055, 2.4)

    return linear_color_component


def apply_material(material):
    obj = active_object()
    obj.data.materials.append(material)


def apply_emission_material(color, name=None, energy=1):
    material = create_emission_material(color, name=name, energy=energy)

    obj = active_object()
    obj.data.materials.append(material)


def create_emission_material(color, name=None, energy=30, return_nodes=False):
    if name is None:
        name = ""

    material = bpy.data.materials.new(name=f"material.emission.{name}")
    material.use_nodes = True

    out_node = material.node_tree.nodes.get("Material Output")
    bsdf_node = material.node_tree.nodes.get("Principled BSDF")
    material.node_tree.nodes.remove(bsdf_node)

    node_emission = material.node_tree.nodes.new(type="ShaderNodeEmission")
    node_emission.inputs["Color"].default_value = color
    node_emission.inputs["Strength"].default_value = energy

    node_emission.location = 0, 0

    material.node_tree.links.new(node_emission.outputs["Emission"], out_node.inputs["Surface"])

    if return_nodes:
        return material, material.node_tree.nodes
    else:
        return material


def parent(child_obj, parent_obj, keep_transform=False):
    """
    Parent the child object to the parent object
    """
    make_active(child_obj)
    child_obj.parent = parent_obj
    if keep_transform:
        child_obj.matrix_parent_inverse = parent_obj.matrix_world.inverted()


def add_bezier_circle(radius=1.0, bevel_depth=0.0, resolution_u=12, extrude=0):
    bpy.ops.curve.primitive_bezier_circle_add(radius=radius)

    bezier_circle_obj = active_object()

    bezier_circle_obj.data.bevel_depth = bevel_depth
    bezier_circle_obj.data.resolution_u = resolution_u
    bezier_circle_obj.data.extrude = extrude

    return bezier_circle_obj


def add_round_cube(radius=1.0):
    enable_extra_meshes()
    bpy.ops.mesh.primitive_round_cube_add(radius=radius)
    return active_object()


def add_subdivided_round_cube(radius=1.0):

    round_cube_obj = add_round_cube(radius)

    bpy.ops.object.modifier_add(type="SUBSURF")

    return round_cube_obj, round_cube_obj.modifiers["Subdivision"]


def create_data_animation_loop(obj, data_path, start_value, mid_value, start_frame, loop_length, linear_extrapolation=True):
    """
    To make a data property loop we need to:
    1. set the property to an initial value and add a keyframe in the beginning of the loop
    2. set the property to a middle value and add a keyframe in the middle of the loop
    3. set the property the initial value and add a keyframe at the end of the loop
    """
    # set the start value
    setattr(obj, data_path, start_value)
    # add a keyframe at the start
    obj.keyframe_insert(data_path, frame=start_frame)

    # set the middle value
    setattr(obj, data_path, mid_value)
    # add a keyframe in the middle
    mid_frame = start_frame + (loop_length) / 2
    obj.keyframe_insert(data_path, frame=mid_frame)

    # set the end value
    setattr(obj, data_path, start_value)
    # add a keyframe in the end
    end_frame = start_frame + loop_length
    obj.keyframe_insert(data_path, frame=end_frame)

    if linear_extrapolation:
        set_fcurve_extrapolation_to_linear()


def enable_addon(addon_module_name):
    """
    Checkout this video explanation with example

    "How to enable add-ons with Python in Blender (with examples)"
    https://youtu.be/HnrInoBWT6Q
    """
    loaded_default, loaded_state = addon_utils.check(addon_module_name)
    if not loaded_state:
        addon_utils.enable(addon_module_name)


def enable_extra_meshes():
    """
    enable Add Mesh Extra Objects addon
    https://docs.blender.org/manual/en/3.0/addons/add_mesh/mesh_extra_objects.html
    """
    enable_addon(addon_module_name="add_mesh_extra_objects")


def add_fcruve_cycles_modifier(obj=None):
    """
    Apply a cycles modifier to all the fcurve animation data of an object.
    """
    if obj is None:
        obj = active_object()

    for fcurve in obj.animation_data.action.fcurves.values():
        modifier = fcurve.modifiers.new(type="CYCLES")
        modifier.mode_before = "REPEAT"
        modifier.mode_after = "REPEAT"


def animate_up_n_down_bob(start_value, mid_value, obj=None, loop_length=90, start_frame=random.randint(0, 60)):
    """Animate the up and down bobbing motion of an object. Apply a fcurve cycles modifier to make it seamless."""
    if obj is None:
        obj = active_object()

    create_data_animation_loop(
        obj,
        "location",
        start_value=start_value,
        mid_value=mid_value,
        start_frame=start_frame,
        loop_length=loop_length,
        linear_extrapolation=False,
    )

    add_fcruve_cycles_modifier(obj)


def get_random_rotation():
    x = math.radians(random.uniform(0, 360))
    y = math.radians(random.uniform(0, 360))
    z = math.radians(random.uniform(0, 360))
    return mathutils.Euler((x, y, z))


def add_displace_modifier(name, texture_type, empty_obj=None):
    """
    Add a displace modifier and a texture to the currently active object.
    Return the modifier, texture, and empty object to
    control the modifier.
    """
    obj = active_object()

    texture = bpy.data.textures.new(f"texture.{name}", texture_type)

    bpy.ops.object.modifier_add(type="DISPLACE")
    displace_modifier = obj.modifiers["Displace"]
    displace_modifier.texture = texture
    displace_modifier.name = f"displace.{name}"
    displace_modifier.texture_coords = "OBJECT"

    if empty_obj == None:
        empty_obj = add_ctrl_empty()

    empty_obj.name = f"empty.{name}"

    displace_modifier.texture_coords_object = empty_obj

    return displace_modifier, texture, empty_obj


# bpybb end


def load_color_palettes():
    return [
        ["#69D2E7", "#A7DBD8", "#E0E4CC", "#F38630", "#FA6900"],
        ["#FE4365", "#FC9D9A", "#F9CDAD", "#C8C8A9", "#83AF9B"],
        ["#ECD078", "#D95B43", "#C02942", "#542437", "#53777A"],
        ["#556270", "#4ECDC4", "#C7F464", "#FF6B6B", "#C44D58"],
        ["#774F38", "#E08E79", "#F1D4AF", "#ECE5CE", "#C5E0DC"],
        ["#E8DDCB", "#CDB380", "#036564", "#033649", "#031634"],
        ["#490A3D", "#BD1550", "#E97F02", "#F8CA00", "#8A9B0F"],
        ["#594F4F", "#547980", "#45ADA8", "#9DE0AD", "#E5FCC2"],
        ["#00A0B0", "#6A4A3C", "#CC333F", "#EB6841", "#EDC951"],
        ["#E94E77", "#D68189", "#C6A49A", "#C6E5D9", "#F4EAD5"],
        ["#3FB8AF", "#7FC7AF", "#DAD8A7", "#FF9E9D", "#FF3D7F"],
        ["#D9CEB2", "#948C75", "#D5DED9", "#7A6A53", "#99B2B7"],
        ["#FFFFFF", "#CBE86B", "#F2E9E1", "#1C140D", "#CBE86B"],
        ["#343838", "#005F6B", "#008C9E", "#00B4CC", "#00DFFC"],
        ["#EFFFCD", "#DCE9BE", "#555152", "#2E2633", "#99173C"],
        ["#413E4A", "#73626E", "#B38184", "#F0B49E", "#F7E4BE"],
    ]


def select_random_color_palette():
    random_palette = random.choice(load_color_palettes())
    print("Random palette:")
    pprint.pprint(random_palette)
    return random_palette


def get_random_color(color_palette):
    hex_color = random.choice(color_palette)
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

    focus_empty = add_ctrl_empty(name=f"empty.focus")
    focus_empty.location.z = 0.33
    camera.data.dof.use_dof = True
    camera.data.dof.aperture_fstop = 1.1
    camera.data.dof.focus_object = focus_empty

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
    scene.cycles.device = "GPU"

    # Use the CPU to render
    # scene.cycles.device = "CPU"

    scene.cycles.samples = 300

    scene.view_settings.look = "Very High Contrast"

    set_1080px_square_render_res()


def scene_setup(i=0):
    fps = 30
    loop_seconds = 12
    frame_count = fps * loop_seconds

    project_name = "holder"
    bpy.context.scene.render.image_settings.file_format = "PNG"

    seed = 0
    if seed:
        random.seed(seed)
    else:
        seed = time_seed()

    bpy.context.scene.render.filepath = f"/tmp/project_{project_name}_{seed}/"

    # Utility Building Blocks
    use_clean_scene_experimental = False
    if use_clean_scene_experimental:
        clean_scene_experimental()
    else:
        clean_scene()

    set_scene_props(fps, loop_seconds)

    loc = (0, 0, 3.5)
    rot = (0, 0, 0)
    setup_camera(loc, rot)

    context = {
        "frame_count": frame_count,
    }

    return context


def add_lights(color_palette):
    """Add lights into the scene"""
    bpy.ops.object.light_add(type="AREA", radius=5, location=(0, 0, -5))
    light = active_object()
    light.data.shape = "DISK"
    light.data.energy = random.choice([200, 300, 500])
    light.rotation_euler.y = math.radians(180)

    bpy.ops.object.light_add(type="AREA", radius=5, location=(0, 0, 5))
    light = active_object()
    light.data.shape = "DISK"
    light.data.energy = 100

    add_bezier_circle(radius=1.5, bevel_depth=0.0, resolution_u=12, extrude=0.1)
    apply_emission_material(get_random_color(color_palette), energy=100)


################################################################
# endregion helper functions END
################################################################


def create_spherical_gradient_tex_mask(material, node_location_step_x, node_y_location):
    """Adds a group of nodes that creates the spherical mask to separate the glass and metallic parts of the material"""
    node_x_location = 0
    texture_coordinate_node = material.node_tree.nodes.new(type="ShaderNodeTexCoord")
    texture_coordinate_node.location = mathutils.Vector((node_x_location, node_y_location))
    node_x_location += node_location_step_x

    mapping_node = material.node_tree.nodes.new(type="ShaderNodeMapping")
    mapping_node.location = mathutils.Vector((node_x_location, node_y_location))
    node_x_location += node_location_step_x

    gradient_texture_node = material.node_tree.nodes.new(type="ShaderNodeTexGradient")
    gradient_texture_node.gradient_type = "SPHERICAL"
    gradient_texture_node.location = mathutils.Vector((node_x_location, node_y_location))
    node_x_location += node_location_step_x

    mix_shader_color_ramp_node = material.node_tree.nodes.new(type="ShaderNodeValToRGB")
    mix_shader_color_ramp_node.color_ramp.elements[1].position = 0.535
    mix_shader_color_ramp_node.color_ramp.interpolation = "CONSTANT"
    mix_shader_color_ramp_node.location = mathutils.Vector((node_x_location, node_y_location))
    node_x_location += node_location_step_x

    material.node_tree.links.new(texture_coordinate_node.outputs["Object"], mapping_node.inputs["Vector"])
    material.node_tree.links.new(mapping_node.outputs["Vector"], gradient_texture_node.inputs["Vector"])
    material.node_tree.links.new(gradient_texture_node.outputs["Color"], mix_shader_color_ramp_node.inputs["Fac"])

    return mix_shader_color_ramp_node, node_x_location


def create_pointiness_edge_highlight_node_tree(color_palette, material, node_location_step_x, node_y_location):
    """Adds a group of nodes that highlights the edges of the Voronoi displacement
    part of the main material"""
    node_x_location = 0
    geometry_node = material.node_tree.nodes.new(type="ShaderNodeNewGeometry")
    geometry_node.location = mathutils.Vector((node_x_location, node_y_location))
    node_x_location += node_location_step_x

    color_ramp_node = material.node_tree.nodes.new(type="ShaderNodeValToRGB")
    color_ramp_node.color_ramp.elements[0].color = (1, 1, 1, 1)
    color_ramp_node.color_ramp.elements[1].color = (0, 0, 0, 1)
    color_ramp_node.color_ramp.elements[1].position = 0.5
    color_ramp_node.color_ramp.interpolation = "CONSTANT"
    color_ramp_node.location = mathutils.Vector((node_x_location, node_y_location))
    node_x_location += node_location_step_x

    material.node_tree.links.new(geometry_node.outputs["Pointiness"], color_ramp_node.inputs["Fac"])

    mix_rgb_node = material.node_tree.nodes.new(type="ShaderNodeMix")
    mix_rgb_node_input_lookup = {socket.identifier: socket for socket in mix_rgb_node.inputs.values()}
    mix_rgb_node_output_lookup = {socket.identifier: socket for socket in mix_rgb_node.outputs.values()}
    mix_rgb_node.data_type = "RGBA"
    mix_rgb_node.blend_type = "MIX"
    mix_rgb_node.location = mathutils.Vector((node_x_location, node_y_location))

    try_count = 5
    color_a = get_random_color(color_palette)
    color_b = get_random_color(color_palette)
    while color_b == color_a and try_count > 0:
        color_b = get_random_color(color_palette)
        try_count -= 1

    mix_rgb_node_input_lookup["A_Color"].default_value = color_a
    mix_rgb_node_input_lookup["B_Color"].default_value = color_b
    node_x_location += node_location_step_x

    material.node_tree.links.new(color_ramp_node.outputs["Color"], mix_rgb_node_input_lookup["Factor_Float"])

    return mix_rgb_node_output_lookup["Result_Color"], node_x_location


def create_glass_node_tree(color_palette, material, node_location_step_x, node_x_location, node_y_location):
    """Adds a group of nodes that creates the glass part of the main material"""

    layer_weight_node = material.node_tree.nodes.new(type="ShaderNodeLayerWeight")
    layer_weight_node.location = mathutils.Vector((node_x_location, node_y_location))
    node_x_location += node_location_step_x

    base_color = get_random_color(color_palette)

    color_ramp_node = material.node_tree.nodes.new(type="ShaderNodeValToRGB")
    color_ramp_node.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    color_ramp_node.color_ramp.elements[0].position = 0.78
    color_ramp_node.color_ramp.elements[1].color = base_color
    color_ramp_node.color_ramp.elements[1].position = 1.00
    color_ramp_node.location = mathutils.Vector((node_x_location, node_y_location))
    node_x_location += node_location_step_x

    material.node_tree.links.new(layer_weight_node.outputs["Facing"], color_ramp_node.inputs["Fac"])

    principled_bsdf_node = material.node_tree.nodes.new(type="ShaderNodeBsdfPrincipled")
    principled_bsdf_node.inputs["Base Color"].default_value = base_color
    principled_bsdf_node.inputs["Metallic"].default_value = 0.0
    principled_bsdf_node.inputs["Specular"].default_value = 0.0
    principled_bsdf_node.inputs["Roughness"].default_value = 0.25
    principled_bsdf_node.inputs["Transmission"].default_value = 1.0
    principled_bsdf_node.inputs["Emission Strength"].default_value = 15.0
    principled_bsdf_node.hide = True
    principled_bsdf_node.location = mathutils.Vector((node_x_location, node_y_location))

    material.node_tree.links.new(color_ramp_node.outputs["Color"], principled_bsdf_node.inputs["Emission"])

    return principled_bsdf_node


def create_metallic_node_tree(color_palette, material, node_location_step_x):
    """Adds a group of nodes that creates the metallic part of the main material"""

    result = create_spherical_gradient_tex_mask(material, node_location_step_x, node_y_location=300)
    mix_shader_color_ramp_node, spherical_gradient_x_location = result

    result = create_pointiness_edge_highlight_node_tree(color_palette, material, node_location_step_x, node_y_location=-100)
    mix_rgb_node_output_color, edge_highlight_x_location = result

    node_x_location = max(spherical_gradient_x_location, edge_highlight_x_location)

    principled_bsdf_node = material.node_tree.nodes.new(type="ShaderNodeBsdfPrincipled")
    principled_bsdf_node.inputs["Metallic"].default_value = 0.54
    principled_bsdf_node.inputs["Roughness"].default_value = 0.26
    principled_bsdf_node.hide = True
    principled_bsdf_node.location = mathutils.Vector((node_x_location, 0))

    material.node_tree.links.new(mix_rgb_node_output_color, principled_bsdf_node.inputs["Base Color"])

    return principled_bsdf_node, mix_shader_color_ramp_node, node_x_location


def create_material(color_palette):
    """Creates and configures all the shader nodes for the centerpiece material"""
    material = bpy.data.materials.new(name="glass_plus_metallic_voronoi")
    material.use_nodes = True

    # remove all nodes
    material.node_tree.nodes.clear()

    node_location_step_x = 300
    node_x_location = 0

    principled_bsdf_node, mix_shader_color_ramp_node, node_x_location = create_metallic_node_tree(color_palette, material, node_location_step_x)

    principled_bsdf_glass_node = create_glass_node_tree(color_palette, material, node_location_step_x, node_x_location=600, node_y_location=-600)

    node_x_location += node_location_step_x

    mix_shader_node = material.node_tree.nodes.new(type="ShaderNodeMixShader")
    mix_shader_node_input_lookup = {socket.identifier: socket for socket in mix_shader_node.inputs.values()}
    mix_shader_node.location = mathutils.Vector((node_x_location, 100))
    node_x_location += node_location_step_x

    material_output = material.node_tree.nodes.new(type="ShaderNodeOutputMaterial")
    material_output.location = mathutils.Vector((node_x_location, 0))

    material.node_tree.links.new(mix_shader_color_ramp_node.outputs["Color"], mix_shader_node_input_lookup["Fac"])
    material.node_tree.links.new(principled_bsdf_node.outputs["BSDF"], mix_shader_node_input_lookup["Shader"])
    material.node_tree.links.new(principled_bsdf_glass_node.outputs["BSDF"], mix_shader_node_input_lookup["Shader_001"])
    material.node_tree.links.new(mix_shader_node.outputs["Shader"], material_output.inputs["Surface"])

    return material


def create_mesh(ctrl_empty, radius=1.0):
    round_cube, subdivision_modifier = add_subdivided_round_cube(radius)

    parent(round_cube, ctrl_empty)

    subdivision_modifier.levels = 5
    subdivision_modifier.render_levels = 7
    bpy.ops.object.shade_smooth()


def animate_displace_modifier(context):
    displace_modifier, texture, empty = add_displace_modifier(name="base_noise", texture_type="VORONOI")
    texture.noise_scale = 0.75
    texture.noise_intensity = 1
    texture.intensity = 0.4
    texture.use_clamp = True

    loop_circle_path = add_bezier_circle(0.2)
    loop_circle_path.name = "loop_circle_path"
    loop_circle_path.data.path_duration = context["frame_count"]

    make_active(empty)

    empty.rotation_euler = get_random_rotation()

    bpy.ops.object.constraint_add(type="FOLLOW_PATH")
    empty.constraints["Follow Path"].target = loop_circle_path
    bpy.ops.constraint.followpath_path_animate(constraint="Follow Path", owner="OBJECT")


def create_centerpiece(context):
    ctrl_empty = add_ctrl_empty()

    create_mesh(ctrl_empty)

    material = create_material(context["color_palette"])
    apply_material(material)

    start_value = mathutils.Vector((0, 0, 0.05))
    mid_value = mathutils.Vector((0, 0, -0.05))
    animate_up_n_down_bob(obj=ctrl_empty, start_value=start_value, mid_value=mid_value)

    animate_displace_modifier(context)


def main():
    """
    Python code to generate this animation
    https://www.artstation.com/artwork/g2A5rZ
    """
    context = scene_setup()
    context["color_palette"] = select_random_color_palette()
    create_centerpiece(context)
    add_lights(context["color_palette"])


if __name__ == "__main__":
    main()
