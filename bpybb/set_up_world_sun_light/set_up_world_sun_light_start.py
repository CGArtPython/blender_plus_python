"""
Note: set_up_world_sun_light() is avalible via the bpybb Python package.
https://github.com/CGArtPython/bpy_building_blocks
"""

import bpy


def set_up_world_sun_light():
    pass


def main():
    bpy.ops.mesh.primitive_cube_add(location=(0, 0, 1))

    bpy.ops.mesh.primitive_plane_add(size=100)
    plane_obj = bpy.context.active_object
    material = bpy.data.materials.new(name="my_material")
    plane_obj.data.materials.append(material)
    material.diffuse_color = (0.1, 0.1, 0.1, 1.0)

    set_up_world_sun_light()


if __name__ == "__main__":
    main()
